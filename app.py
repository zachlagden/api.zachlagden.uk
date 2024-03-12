"""
The api.zachlagden.uk API.

Useful endpoints for use over many of my projects.
"""

# Standard Library Imports
from typing import Union
import json

# Flask imports
from flask import Flask, render_template, request

# Flask Extensions
from flask_restx import Api
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter

# Load the config
with open("config.json", "r") as f:
    CONFIG = json.load(f)

# Load the API keys
with open("api_keys.json", "r") as f:
    API_KEYS = json.load(f)

# Create the Flask app
app = Flask(__name__)

# Flask Limiter


def custom_key_func() -> Union[str, None]:
    return (
        request.args.get("api_key") or get_remote_address()
        if get_remote_address()
        else (
            request.headers.getlist("Cf-Connecting-Ip")[0]
            if request.headers.getlist("Cf-Connecting-Ip")
            else None
        )
    )


# Initialize Flask-Limiter
limiter = Limiter(
    app=app,
    key_func=custom_key_func,
    default_limits=["200 per day", "50 per hour"],  # Default rate limit
)

# Flask Endpoints

@app.route("/")
def _index():
    return render_template("index.html")

# Define the API
api = Api(
    app,
    version="1.0",
    title="api.zachlagden.uk API",
    description="Useful endpoints for use over many of my projects.",
    default="main",
    default_label="Main API endpoints",
    doc="/docs",
)

# Add the namespaces to the API
from endpoints import activity, tools

api.add_namespace(activity.NSactivity)
api.add_namespace(tools.NStools)

if __name__ == "__main__":
    app.run(debug=True, port=43333)
