import unittest
from unittest.mock import MagicMock, patch
from PIL import Image
from subtitle_processor import SubtitleProcessor

class TestSubtitleProcessor(unittest.TestCase):

    @patch('subtitle_processor.pytesseract')
    @patch('subtitle_processor.mss.mss')
    def test_pipeline(self, mock_mss, mock_pytesseract):
        """
        Test the Capture -> OCR -> Translate pipeline with mocks.
        """
        # Setup mocks
        mock_sct = MagicMock()
        mock_mss.return_value = mock_sct

        # Mock grab return (dummy)
        # mss grab returns an object with size and bgra
        mock_grab_obj = MagicMock()
        mock_grab_obj.size = (100, 50)
        mock_grab_obj.bgra = b'\x00' * 100 * 50 * 4
        mock_sct.grab.return_value = mock_grab_obj

        # Mock OCR result
        mock_pytesseract.image_to_string.return_value = "Hello World"

        processor = SubtitleProcessor()

        # 1. Test Capture
        region = {'top': 0, 'left': 0, 'width': 100, 'height': 50}
        img = processor.capture_region(region)
        self.assertIsInstance(img, Image.Image)
        mock_sct.grab.assert_called_with(region)

        # 2. Test Extract
        text = processor.extract_text(img)
        self.assertEqual(text, "Hello World")

        # 3. Test Translate
        # Mocking the translator instance method directly
        with patch.object(processor.translator, 'translate', return_value="안녕하세요 세상") as mock_trans:
            translated = processor.translate_text(text)
            self.assertEqual(translated, "안녕하세요 세상")
            mock_trans.assert_called_with("Hello World")

if __name__ == '__main__':
    unittest.main()
