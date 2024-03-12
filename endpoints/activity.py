# Standard Library Imports
import json

# Third Party Imports
import requests

# Flask imports
from flask import Blueprint

# Flask Extensions
from flask_restx import Api, Resource, Namespace, reqparse

# Helper Functions
from helpers.keys import check_api_key
from helpers.tools import build_url

# Load the config
with open("config.json", "r") as f:
    CONFIG = json.load(f)

# Load the API keys
with open("api_keys.json", "r") as f:
    API_KEYS = json.load(f)
    
# Create a Blueprint for main routes
blueprint = Blueprint("tools", __name__)

# Define the API
api = Api(
    blueprint,
    version="1.0",
    title="api.zachlagden.uk API",
    description="Useful endpoints for use over many of my projects.",
    default="main",
    default_label="Main API endpoints",
    doc="/docs",
)

# Define namespace for Flask-RESTx
NSactivity = Namespace("activity", description="Activity API endpoints")

"""
LastFM Now Playing Endpoint

This endpoint fetches the currently playing track from LastFM.

The endpoint requires the following query parameters:
- api_key: An API key for authentication

The endpoint returns a JSON object with the following keys:
- ok: A boolean indicating if the request was successful
- status: The HTTP status code of the response
- message: A message about the status of the request
- data: The data returned from the LastFM API
"""

activity_now_playing_parser = reqparse.RequestParser()
activity_now_playing_parser.add_argument(
    "api_key", type=str, required=True, help="An API key for authentication"
)


@NSactivity.route("/now_playing")
class LastFMNowPlaying(Resource):
    @NSactivity.expect(activity_now_playing_parser)
    @api.doc(
        description="Fetches the track I'm currently playing on Spotify, if any.",
        responses={
            200: "Success",
            401: "Invalid API key",
            500: "Failed to get now playing data from LastFM",
        },
    )
    def get(self):
        args = activity_now_playing_parser.parse_args()

        if not check_api_key(args["api_key"]):
            return {
                "ok": False,
                "status": 401,
                "message": "Invalid API key",
            }, 401

        request_url = build_url(
            CONFIG["lastfm"]["api"]["base_url"],
            CONFIG["lastfm"]["api"]["params"],
        )

        request_response = requests.get(request_url)

        if request_response.status_code != 200:
            return {
                "ok": False,
                "status": request_response.status_code,
                "message": "Failed to get now playing data from LastFM while sending request. Response from the API is in the data key.",
                "data": request_response.text,
            }

        request_data = request_response.json()

        if (
            "recenttracks" not in request_data
            or "track" not in request_data["recenttracks"]
        ):
            return {
                "ok": False,
                "status": 500,
                "message": "Failed to get now playing data from LastFM. Response from the API is in the data key.",
                "data": request_data,
            }, 500

        track = request_data["recenttracks"]["track"][0]
        if "@attr" in track and "nowplaying" in track["@attr"]:
            track_data = {
                "artist": track["artist"]["#text"],
                "name": track["name"],
                "album": track["album"]["#text"],
                "url": track["url"],
                "image": track["image"][-1]["#text"],
            }

            return {
                "ok": True,
                "status": 200,
                "message": "Successfully fetched now playing data.",
                "data": track_data,
            }
        else:
            return {
                "ok": True,
                "status": 200,
                "message": "No track is currently playing",
                "data": None,
            }, 404


"""
LastFM Recent Tracks Endpoint

This endpoint fetches the most recent tracks from LastFM.

The endpoint requires the following query parameters:
- api_key: An API key for authentication

The endpoint also accepts the following optional query parameters:
- limit: The number of tracks to return

The endpoint returns a JSON object with the following keys:
- ok: A boolean indicating if the request was successful
- status: The HTTP status code of the response
- message: A message about the status of the request
- data: The data returned from the LastFM API
"""

activity_recent_tracks_parser = reqparse.RequestParser()
activity_recent_tracks_parser.add_argument(
    "api_key", type=str, required=True, help="An API key for authentication"
)
activity_recent_tracks_parser.add_argument(
    "limit", type=int, help="The number of tracks to return"
)


@NSactivity.route("/recent_tracks")
class LastFMRecentTracks(Resource):
    @NSactivity.expect(activity_recent_tracks_parser)
    @api.doc(
        description="Fetches the tracks I've recently listened to on Spotify.",
        responses={
            200: "Success",
            401: "Invalid API key",
            500: "Failed to get recent tracks data from LastFM",
        },
    )
    def get(self):
        args = activity_recent_tracks_parser.parse_args()

        if not check_api_key(args["api_key"]):
            return {
                "ok": False,
                "status": 401,
                "message": "Invalid API key",
            }, 401

        request_url = build_url(
            CONFIG["lastfm"]["api"]["base_url"],
            CONFIG["lastfm"]["api"]["params"],
        )

        request_response = requests.get(request_url)

        if request_response.status_code != 200:
            return {
                "ok": False,
                "status": request_response.status_code,
                "message": "Failed to get recent tracks data from LastFM while sending request. Response from the API is in the data key.",
                "data": request_response.text,
            }

        request_data = request_response.json()

        if (
            "recenttracks" not in request_data
            or "track" not in request_data["recenttracks"]
        ):
            return {
                "ok": False,
                "status": 500,
                "message": "Failed to get recent tracks data from LastFM. Response from the API is in the data key.",
                "data": request_data,
            }, 500

        tracks = request_data["recenttracks"]["track"]
        if args["limit"] is not None:
            tracks = tracks[: args["limit"]]

        track_data = []
        for track in tracks:
            track_data.append(
                {
                    "artist": track["artist"]["#text"],
                    "name": track["name"],
                    "album": track["album"]["#text"],
                    "url": track["url"],
                    "image": track["image"][-1]["#text"],
                }
            )

        return {
            "ok": True,
            "status": 200,
            "message": "Successfully fetched recent tracks data.",
            "data": track_data,
        }