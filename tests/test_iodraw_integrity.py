import html
import re
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = sorted((ROOT / "all").glob("*.iodraw*"))


def clean_value(value):
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]*>", "", text)
    return text.replace("\xa0", " ").strip()


def parse_iodraw(path):
    return ET.parse(path).getroot()


class IodrawIntegrityTest(unittest.TestCase):
    def test_iodraw_files_parse_and_reference_existing_cells(self):
        self.assertTrue(IODRAW_FILES, "expected iodraw files under all/")

        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                root = parse_iodraw(path)
                cells = [cell for cell in root.iter("mxCell") if cell.get("id")]
                ids = [cell.get("id") for cell in cells]
                duplicates = [cell_id for cell_id, count in Counter(ids).items() if count > 1]
                self.assertEqual([], duplicates)

                id_set = set(ids)
                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref is not None:
                            self.assertIn(ref, id_set, f"{cell.get('id')} has missing {attr}={ref}")

    def test_iodraw_files_do_not_contain_executable_payloads(self):
        dangerous_patterns = (
            "<script",
            "javascript:",
            "onerror=",
            "onclick=",
            "onload=",
        )

        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                raw = path.read_text(encoding="utf-8").lower()
                for pattern in dangerous_patterns:
                    self.assertNotIn(pattern, raw)

    def test_parking_flow_keeps_left_and_right_qr_actions_distinct(self):
        root = parse_iodraw(ROOT / "all" / "未命名绘图.iodraw")
        cells = {cell.get("id"): cell for cell in root.iter("mxCell") if cell.get("id")}

        self.assertEqual(
            "左转摄像头进行二维码识别",
            clean_value(cells["2C-E8wXzLExmKxaGtvue-94"].get("value")),
        )
        self.assertEqual(
            "右转摄像头进行二维码识别",
            clean_value(cells["2C-E8wXzLExmKxaGtvue-102"].get("value")),
        )

        self.assertEqual(
            "倒车入库至左边车位",
            clean_value(cells["2C-E8wXzLExmKxaGtvue-101"].get("value")),
        )
        self.assertEqual(
            "倒车入库至右边车位",
            clean_value(cells["2C-E8wXzLExmKxaGtvue-110"].get("value")),
        )

        self.assertEqual("2C-E8wXzLExmKxaGtvue-101", cells["2C-E8wXzLExmKxaGtvue-120"].get("source"))
        self.assertEqual("2C-E8wXzLExmKxaGtvue-110", cells["2C-E8wXzLExmKxaGtvue-116"].get("source"))
        self.assertEqual("2C-E8wXzLExmKxaGtvue-115", cells["2C-E8wXzLExmKxaGtvue-120"].get("target"))
        self.assertEqual("2C-E8wXzLExmKxaGtvue-115", cells["2C-E8wXzLExmKxaGtvue-116"].get("target"))
        self.assertEqual("进入监听状态", clean_value(cells["2C-E8wXzLExmKxaGtvue-115"].get("value")))


if __name__ == "__main__":
    unittest.main()
