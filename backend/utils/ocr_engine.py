import os
import shutil
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# On Windows, Tesseract usually isn't on PATH after install — allow pointing to it explicitly
_tesseract_cmd = os.getenv("TESSERACT_CMD")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd
elif os.name == "nt":
    default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(default_path):
        pytesseract.pytesseract.tesseract_cmd = default_path


TESSERACT_HELP = (
    "Tesseract-OCR is not installed or not found. On Windows: download and install it from "
    "https://github.com/UB-Mannheim/tesseract/wiki, then either add it to your PATH or "
    "set the TESSERACT_CMD environment variable in your .env file to its full path, e.g. "
    r'TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe'
)

POPPLER_HELP = (
    "Poppler is not installed (required for OCR on scanned PDFs). On Windows: download it from "
    "https://github.com/oschwartz10612/poppler-windows/releases, extract it, and add its 'bin' "
    "folder to your PATH, or set POPPLER_PATH in your .env file to that 'bin' folder."
)


def _check_tesseract():
    if not shutil.which(pytesseract.pytesseract.tesseract_cmd or "tesseract") and not os.path.exists(
        pytesseract.pytesseract.tesseract_cmd or ""
    ):
        raise RuntimeError(TESSERACT_HELP)


def ocr_image(image_path: str) -> str:
    _check_tesseract()
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(TESSERACT_HELP)


def ocr_pdf(pdf_path: str) -> str:
    _check_tesseract()
    poppler_path = os.getenv("POPPLER_PATH")  # optional, only needed if not on PATH
    try:
        pages = convert_from_path(pdf_path, poppler_path=poppler_path)
    except Exception as e:
        if "poppler" in str(e).lower() or "Unable to get page count" in str(e):
            raise RuntimeError(POPPLER_HELP)
        raise

    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page)
    return text