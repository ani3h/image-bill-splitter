import cv2
import pytesseract
import numpy as np
from PIL import Image
import os
import sys


def convert_to_jpg(input_path, output_path=None):
    try:
        # Open the image file
        with Image.open(input_path) as img:
            # Convert image to RGB if it's in a different mode (e.g., RGBA, P)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # If no output path provided, construct one with a .jpg extension
            if output_path is None:
                base, _ = os.path.splitext(input_path)
                output_path = base + ".jpg"

            # Save the image in JPEG format
            img.save(output_path, "JPEG")
            return output_path
    except Exception as e:
        print(f"Error converting image: {e}")
        sys.exit(1)


def extract_text(image_path):
    img = cv2.imread(image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, tresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    blurred = cv2.GaussianBlur(tresh, (5, 5), 0)

    extract_text = pytesseract.image_to_string(blurred, lang='eng')

    return extract_text
