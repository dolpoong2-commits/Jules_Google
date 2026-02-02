import mss
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator

class SubtitleProcessor:
    def __init__(self, tesseract_cmd=None):
        """
        Initialize the SubtitleProcessor.
        :param tesseract_cmd: Optional path to tesseract binary.
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Initialize translator
        # source='auto' allows it to detect English (or other languages) automatically
        self.translator = GoogleTranslator(source='auto', target='ko')

        # Initialize screen capture
        self.sct = mss.mss()

    def capture_region(self, region):
        """
        Captures a region of the screen.
        :param region: dict {'top': int, 'left': int, 'width': int, 'height': int}
        :return: PIL Image
        """
        try:
            sct_img = self.sct.grab(region)
            # mss returns BGRA, convert to RGB for Pillow/Tesseract
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img
        except Exception as e:
            print(f"Capture Error: {e}")
            return None

    def extract_text(self, image):
        """
        Extracts text from a PIL Image using OCR.
        :param image: PIL Image
        :return: Extracted string
        """
        if image is None:
            return ""
        try:
            # Assuming English subtitles for now as per requirements
            # psm 6: Assume a single uniform block of text. Often good for subtitles.
            config = '--psm 6'
            text = pytesseract.image_to_string(image, lang='eng', config=config)
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def translate_text(self, text):
        """
        Translates text to Korean.
        :param text: Text to translate
        :return: Translated text
        """
        if not text:
            return ""
        try:
            translated = self.translator.translate(text)
            return translated
        except Exception as e:
            print(f"Translation Error: {e}")
            return text
