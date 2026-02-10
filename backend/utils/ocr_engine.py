from PIL import Image
import pytesseract
from pdf2image import convert_from_path


def ocr_image(image_path: str) -> str:
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)


def ocr_pdf(pdf_path: str) -> str:
    pages = convert_from_path(pdf_path)
    text = ""

    for page in pages:
        text += pytesseract.image_to_string(page)

    return text
