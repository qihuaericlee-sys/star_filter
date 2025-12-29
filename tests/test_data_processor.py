import unittest
import json
import tempfile
from pathlib import Path
from core.data_processor import DataProcessor


class TestDataProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = DataProcessor()
    
    def test_extract_title_from_item(self):
        # 测试正常情况
        item = {"title": "Test Title", "other": "data"}
        self.assertEqual(self.processor.extract_title_from_item(item), "Test Title")
        
        # 测试不同字段名
        item = {"Title": "Another Title"}
        self.assertEqual(self.processor.extract_title_from_item(item), "Another Title")
        
        # 测试无标题字段
        item = {"name": "Test Name"}
        self.assertEqual(self.processor.extract_title_from_item(item), "Test Name")
        
        # 测试无标题
        item = {"data": "some data"}
        self.assertIsNone(self.processor.extract_title_from_item(item))
    
    def test_load_json_file_list(self):
        # 创建临时JSON文件（列表结构）
        test_data = [{"title": "Item 1"}, {"title": "Item 2"}]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)
        
        try:
            records, container_key, original_data = self.processor.load_json_file(temp_path)
            self.assertEqual(len(records), 2)
            self.assertIsNone(container_key)
            self.assertEqual(original_data, test_data)
        finally:
            temp_path.unlink()
    
    def test_load_json_file_dict(self):
        # 创建临时JSON文件（字典结构）
        test_data = {"items": [{"title": "Item 1"}, {"title": "Item 2"}]}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)
        
        try:
            records, container_key, original_data = self.processor.load_json_file(temp_path)
            self.assertEqual(len(records), 2)
            self.assertEqual(container_key, "items")
            self.assertEqual(original_data, test_data)
        finally:
            temp_path.unlink()


if __name__ == '__main__':
    unittest.main()