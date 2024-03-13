# Standard Library Imports
from io import BytesIO
import json

# Third Party Imports
import qrcode

# Flask imports
from flask import request, send_file, Blueprint

# Flask Extensions
from flask_restx import Api, Resource, Namespace, reqparse

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
NStools = Namespace("tools", description="Tools API endpoints")

"""
QR Code Generator Endpoint

This endpoint generates a QR code from the given data.

The endpoint requires the following query parameters:
- api_key: An API key for authentication
- data: The data to encode in the QR code

The endpoint also accepts the following optional query parameters:
- size: The size of the QR code (as a factor of the base size)
- error_correction: The error correction level: L (low), M (medium), Q (quartile), H (high)

The endpoint returns a PNG image of the QR code.
"""

tools_qr_parser = reqparse.RequestParser()
tools_qr_parser.add_argument(
    "data", type=str, required=True, help="Data to encode in the QR code"
)
tools_qr_parser.add_argument(
    "size",
    type=int,
    default=8,
    choices=list(range(1, 51)),
    help="Size of the QR code (as a factor of the base size)",
)
tools_qr_parser.add_argument(
    "error_correction",
    type=str,
    default="L",
    choices=["L", "M", "Q", "H"],
    help="Error correction level: L (low), M (medium), Q (quartile), H (high)",
)

@NStools.route("/qr")
class QRCodeGenerator(Resource):
    @NStools.expect(tools_qr_parser)
    @api.doc(
        description="Generates a QR code from the given data.",
        responses={
            200: "Success",
            401: "Invalid API key",
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

        try:
            # Map the error correction input to the qrcode constants
            error_correction_map = {
                "L": qrcode.constants.ERROR_CORRECT_L,  # type: ignore
                "M": qrcode.constants.ERROR_CORRECT_M,  # type: ignore
                "Q": qrcode.constants.ERROR_CORRECT_Q,  # type: ignore
                "H": qrcode.constants.ERROR_CORRECT_H,  # type: ignore
            }
            error_correction = error_correction_map.get(
                args["error_correction"], qrcode.constants.ERROR_CORRECT_L  # type: ignore
            )

            # Generate the QR code
            qr = qrcode.QRCode(  # type: ignore
                version=1,
                error_correction=error_correction,
                box_size=args["size"],
                border=4,
            )
            qr.add_data(args["data"])
            qr.make(fit=True)

            # Save the QR code to a BytesIO stream rather than a file
            img = qr.make_image(fill_color="black", back_color="white")
            img_io = BytesIO()
            img.save(img_io, "PNG")
            img_io.seek(0)
        except Exception as e:
            return {
                "ok": False,
                "status": 500,
                "message": f"Failed to generate QR code",
                "error": str(e),
            }, 500

        return send_file(img_io, mimetype="image/png")