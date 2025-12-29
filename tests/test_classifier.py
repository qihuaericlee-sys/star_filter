import unittest
from unittest.mock import Mock, patch
from core import TitleClassifier


class TestTitleClassifier(unittest.TestCase):
    
    def setUp(self):
        self.mock_client = Mock()
        self.classifier = TitleClassifier(self.mock_client)
    
    @patch('core.classifier.logger')
    def test_classify_title_yes(self, mock_logger):
        # 模拟API响应
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="YES"))]
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result, text = self.classifier.classify_title("Taylor Swift")
        
        self.assertTrue(result)
        self.assertEqual(text, "YES")
    
    @patch('core.classifier.logger')
    def test_classify_title_no(self, mock_logger):
        # 模拟API响应
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="NO"))]
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result, text = self.classifier.classify_title("Thanksgiving")
        
        self.assertFalse(result)
        self.assertEqual(text, "NO")
    
    @patch('core.classifier.logger')
    def test_classify_title_fallback(self, mock_logger):
        # 模拟API响应（非标准响应）
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Yes, this is about a celebrity"))]
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result, text = self.classifier.classify_title("Klopp")
        
        self.assertTrue(result)  # 因为包含"YES"
        self.assertEqual(text, "YES, THIS IS ABOUT A CELEBRITY")


if __name__ == '__main__':
    unittest.main()