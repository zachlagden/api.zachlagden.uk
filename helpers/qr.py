"""
sudo apt install libwebp-dev
pip install qrcode[pil]
"""

from qrcode.image.pil import PilImage
from qrcode.image.svg import SvgImage
from io import BytesIO
from PIL import Image
import qrcode

def convert_image_filetype_from_bytesio(bytesiostream: BytesIO, desired_filetype: str) -> BytesIO:
    SUPPORTED_FILETYPES = ["PNG", "JPG", "JPEG", "GIF", "BMP", "WEBP"]
    
    if desired_filetype not in SUPPORTED_FILETYPES:
        raise ValueError("The desired file type is not supported, please choose from PNG, JPG, JPEG, GIF, BMP, or WEBP.")
    
    try:
        bytesiostream.seek(0)
        image = Image.open(bytesiostream)
        image_format = image.format
    except Exception as e:
        raise Exception(f"Failed to open the image from the BytesIO stream: {str(e)}")
    
    if desired_filetype == image_format:
        return bytesiostream
    
    # Create a new BytesIO stream
    new_bytesiostream = BytesIO()
    
    if desired_filetype in ["JPG", "JPEG"]:
        image.save(new_bytesiostream, "JPEG")
    else:
        # For PNG, GIF, BMP, WEBP
        image.save(new_bytesiostream, desired_filetype)
    
    new_bytesiostream.seek(0)
    return new_bytesiostream


def generate_qr_code(args: dict) -> BytesIO:
    # Map the error correction input to the qrcode constants
    error_correction_map = {
        "L": qrcode.constants.ERROR_CORRECT_L, # type: ignore
        "M": qrcode.constants.ERROR_CORRECT_M, # type: ignore
        "Q": qrcode.constants.ERROR_CORRECT_Q, # type: ignore
        "H": qrcode.constants.ERROR_CORRECT_H, # type: ignore
    }

    # Set the error correction level
    error_correction = error_correction_map.get(
        args.get("error_correction", "L"), qrcode.constants.ERROR_CORRECT_L # type: ignore
    )

    # Initialize the QRCode object with the provided or default values
    qr = qrcode.QRCode( # type: ignore
        version=args.get("version"),
        error_correction=error_correction,
        box_size=args.get("size", 10),
        border=args.get("border", 4),
    )

    # Add the data to the QR code
    qr.add_data(args.get("data", ""))
    qr.make(fit=True)

    # Determine the file type and set up appropriate image factory for SVG
    filetype = args.get("filetype", "PNG").upper()
    if filetype == "SVG":
        img_factory = SvgImage
    else:
        img_factory = PilImage

    # Generate the QR code image
    img = qr.make_image(
        fill_color=args.get("fill_color", "black"),
        back_color=args.get("back_color", "white"),
        image_factory=img_factory
    )

    # Create a BytesIO stream to save the image to
    img_io = BytesIO()

    # Special handling for SVG since it doesn't use the 'save' method in the same way
    if filetype == "SVG":
        img.save(img_io)
    else:
        # Correct filetype for JPEG
        if filetype == "JPG":
            filetype = "JPEG"
        img.save(img_io, format=filetype)

    img_io.seek(0)
    
    return img_io

if __name__ == "__main__":
    filetype = "WEBP"
    
    # Example usage
    args = {
        "data": "https://example.com",
        "error_correction": "L",
        "size": 7,
        "border": 3,
        "fill_color": "black",
        "back_color": "white",
        "filetype": filetype # PNG, JPG (JPEG), GIF, BMP, WEBP or SVG.
    }
    bytesiostream = generate_qr_code(args)
    
    # Save the file
    with open("qr_code."+filetype.lower(), "wb") as f:
        f.write(bytesiostream.read())
    
    try:
        img = Image.open(bytesiostream)
        print(img.format)
    except:
        print("Failed to open the image.")
    
    