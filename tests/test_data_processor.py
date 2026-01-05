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

        # 测试 Weibo 风格的 keyword
        item = {"keyword": "明星彩名", "raw_data": ["明星彩名", "2025-12-20"]}
        self.assertEqual(self.processor.extract_title_from_item(item), "明星彩名")

        # 测试 raw_data 首元素
        item = {"raw_data": ["首元素标题", 123, 456]}
        self.assertEqual(self.processor.extract_title_from_item(item), "首元素标题")
    
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

    def test_load_json_file_date_indexed(self):
        # 创建按日期索引的 JSON 文件
        test_data = {
            "2025-12-20": {
                "date": "2025-12-20",
                "items": [{"keyword": "A"}, {"keyword": "B"}]
            },
            "2025-12-21": {
                "date": "2025-12-21",
                "items": [{"keyword": "C"}]
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            records, container_key, original_data = self.processor.load_json_file(temp_path)
            self.assertEqual(container_key, 'by_date')
            # 3 条记录
            self.assertEqual(len(records), 3)
            # 检查 _source_date 字段
            dates = sorted([r.get('_source_date') for r in records])
            self.assertEqual(dates, ['2025-12-20', '2025-12-20', '2025-12-21'])
        finally:
            temp_path.unlink()


if __name__ == '__main__':
    unittest.main()