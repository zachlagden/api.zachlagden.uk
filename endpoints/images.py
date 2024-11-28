# Standard Library Imports
from io import BytesIO
import base64
import json

# Third Party Imports
from barcode.writer import SVGWriter
from PIL import Image
from sklearn.cluster import KMeans
import barcode
import cv2
import numpy as np
import requests
import requests
import urllib.request

# Flask imports
from flask import send_file, Blueprint

# Flask Extensions
from flask_restx import Api, Resource, Namespace, reqparse

# Helpers
from helpers.qr import generate_qr_code

# Load the config
with open("config.json", "r") as f:
    CONFIG = json.load(f)

# Load the API keys
with open("api_keys.json", "r") as f:
    API_KEYS = json.load(f)

# Create a Blueprint for main routes
blueprint = Blueprint("images", __name__)

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
NSimages = Namespace("images", description="Images API endpoints")

"""
Extract Dominant Colors Endpoint

This endpoint extracts the dominant colors from an image.

The endpoint requires the following query parameters:
- url: The URL of the image to process

The endpoints returns a JSON object containing the dominant colors.
"""

dominant_colors_parser = reqparse.RequestParser()
dominant_colors_parser.add_argument(
    "url",
    type=str,
    required=True,
    help="URL of the image to process, must be either PNG, JPG, JPEG, GIF, BMP, or WEBP",
)
dominant_colors_parser.add_argument(
    "n_colors",
    type=int,
    default=3,
    help="Number of dominant colors to extract",
    choices=list(range(1, 11)),
)


@NSimages.route("/dominant_colors")
class DominantColorsExtractor(Resource):
    @NSimages.expect(dominant_colors_parser)
    @api.doc(
        description="Extracts the dominant colors from an image.",
        responses={
            200: "Success",
            400: "The supplied URL is not a valid image, not accessible, or too large",
            500: "Failed to extract dominant colors",
        },
    )
    def get(self):
        args = dominant_colors_parser.parse_args()

        # Ensure the URL is a valid URL using the urllib library
        try:
            urllib.request.urlopen(args["url"])
        except Exception as e:
            return {
                "ok": False,
                "status": 400,
                "message": "The supplied URL is not valid.",
                "error": str(e),
            }, 400

        # Download the image using requests and save to a bytesio stream
        try:
            image_response = requests.get(args["url"])
            image_io_stream = BytesIO(image_response.content)
            image_io_stream.seek(0)
        except Exception as e:
            return {
                "ok": False,
                "status": 400,
                "message": "Failed to download the image.",
                "error": str(e),
            }, 400

        # Read the image using PIL
        try:
            image = Image.open(image_io_stream)
        except Exception as e:
            return {
                "ok": False,
                "status": 400,
                "message": "The supplied URL is not a valid image.",
                "error": str(e),
            }, 400

        # Reset the stream
        image_io_stream = BytesIO()

        # Convert the image to PNG
        image.save(image_io_stream, "PNG")

        # Seek to the start of the stream
        image_io_stream.seek(0)

        image_byte_string = image_io_stream.read()

        # Convert byte string to NumPy array
        image_np_array = np.frombuffer(image_byte_string, dtype=np.uint8)

        # Decode the image from the NumPy array
        image = cv2.imdecode(image_np_array, cv2.IMREAD_COLOR)

        # Reshape the image to a 2D array of pixels
        pixels = image.reshape((-1, 3))

        # Convert to floating point
        image = np.float32(pixels)

        # Apply KMeans clustering
        kmeans = KMeans(n_clusters=args["n_colors"])
        kmeans.fit(pixels)

        # Retrieve the dominant colors
        colors = kmeans.cluster_centers_

        # Convert the pixel values to integer
        colors = colors.astype(int).tolist()

        # Convert the colors to hex
        hex_colors = [
            f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}" for color in colors
        ]

        return {
            "ok": True,
            "status": 200,
            "message": "Successfully extracted dominant colors",
            "data": {
                "hex_colors": hex_colors,
                "rgb_colors": colors,
            },
        }


"""
QR Code Generator Endpoint

This endpoint generates a QR code from the given data.

The endpoint requires the following query parameters:
- data: The data to encode in the QR code

The endpoint also accepts the following optional query parameters:
- size: The size of the QR code (as a factor of the base size)
- error_correction: The error correction level: L (low), M (medium), Q (quartile), H (high)
- fill_color: The color of the QR code itself. Accepts any valid HTML color name or hex code.
- back_color: The background color of the QR code. Accepts any valid HTML color name or hex code.
- version: The version of the QR code. This is an integer from 1 to 40. If not specified, we will determine the smallest version that will fit the data.
- border: The size of the border around the QR code. This is the number of modules on each side.

The endpoint returns a PNG image of the QR code.
"""

tools_qr_parser = reqparse.RequestParser()
tools_qr_parser.add_argument(
    "data", type=str, required=True, help="Data to encode in the QR code"
)
tools_qr_parser.add_argument(
    "filetype",
    type=str,
    default="PNG",
    choices=["PNG", "JPG", "JPEG", "GIF", "BMP", "WEBP", "SVG", "BASE64"],
    help="The file type of the QR code image",
    case_sensitive=False,
)
tools_qr_parser.add_argument(
    "size",
    type=int,
    default=8,
    choices=list(range(1, 101)),
    help="Size of the QR code (as a factor of the base size). This is an integer from 1 to 100.",
)
tools_qr_parser.add_argument(
    "error_correction",
    type=str,
    default="L",
    choices=["L", "M", "Q", "H"],
    help="Error correction level: L (low), M (medium), Q (quartile), H (high)",
)
tools_qr_parser.add_argument(
    "version",
    type=int,
    choices=list(range(1, 41)),
    help="The version of the QR code. This is an integer from 1 to 40. If not specified, we will determine the smallest version that will fit the data.",
)
tools_qr_parser.add_argument(
    "border",
    type=int,
    default=4,
    choices=list(range(1, 11)),
    help="The size of the border around the QR code. This is the number of modules on each side.",
)
tools_qr_parser.add_argument(
    "fill_color",
    type=str,
    default="black",
    help="The color of the QR code itself. Accepts any valid HTML color name or hex code.",
    case_sensitive=False,
)
tools_qr_parser.add_argument(
    "back_color",
    type=str,
    default="white",
    help="The background color of the QR code. Accepts any valid HTML color name or hex code.",
    case_sensitive=False,
)


@NSimages.route("/qr")
class QRCodeGenerator(Resource):
    @NSimages.expect(tools_qr_parser)
    @api.doc(
        description="Generates a QR code from the given data.",
        responses={
            200: "Success",
            400: "The data cannot be longer than 1000 characters",
            500: "Failed to generate QR code",
        },
    )
    def get(self):
        args = tools_qr_parser.parse_args()

        # Ensure the data is not too long
        if len(args["data"]) > 1000:
            return {
                "ok": False,
                "status": 400,
                "message": "The data cannot be longer than 1000 characters",
            }, 400

        # Check if the file type is BASE64
        IS_BASE64 = False
        if args["filetype"].upper() == "BASE64":
            IS_BASE64 = True
            args["filetype"] = "PNG"

        try:
            img_io = generate_qr_code(args)
        except Exception as e:
            return {
                "ok": False,
                "status": 500,
                "message": f"Failed to generate QR code",
                "error": str(e),
            }, 500

        # If the file type is BASE64, return the base64 encoded image
        if IS_BASE64:
            base64_bytes = base64.b64encode(img_io.getvalue())
            base64_string = base64_bytes.decode("utf-8")

            return {
                "ok": True,
                "status": 200,
                "message": "Successfully generated QR code",
                "base64": base64_string,
            }

        else:
            return send_file(
                img_io,
                mimetype=f"image/{args['filetype'].lower()}",
                download_name=f"qr_code.{args['filetype'].lower()}",
            )


"""
Barcode Generator Endpoint

This endpoint generates a barcode from the given data.

The endpoint requires the following query parameters:
- data: The data to encode in the barcode

The endpoint also accepts the following optional query parameters:
- barcode_type: The type of the barcode to generate (code39, ean13, ean8, upca, code128)

The endpoint returns an SVG image of the barcode.
"""

# Add an argument parser for the new barcode endpoint
tools_barcode_parser = reqparse.RequestParser()
tools_barcode_parser.add_argument(
    "data", type=str, required=True, help="Data to encode in the barcode"
)
tools_barcode_parser.add_argument(
    "barcode_type",
    type=str,
    default="code128",
    choices=["code39", "ean13", "ean8", "upca", "code128"],
    help="Type of the barcode to generate",
)


@NSimages.route("/barcode")
class BarcodeGenerator(Resource):
    @NSimages.expect(tools_barcode_parser)
    @api.doc(
        description="Generates a barcode from the given data.",
        responses={
            200: "Success",
            401: "Invalid API key",
            500: "Failed to generate barcode",
        },
    )
    def get(self):
        args = tools_barcode_parser.parse_args()

        try:
            # Generate the barcode
            barcode_class = barcode.get_barcode_class(args["barcode_type"])  # type: ignore
            barcode_instance = barcode_class(args["data"], writer=SVGWriter())

            # Save the barcode to a BytesIO stream
            img_io = BytesIO()
            barcode_instance.write(img_io)
            img_io.seek(0)
        except Exception as e:
            return {
                "ok": False,
                "status": 500,
                "message": "Failed to generate barcode",
                "error": str(e),
            }, 500

        return send_file(img_io, mimetype="image/svg+xml", download_name="barcode.svg")
