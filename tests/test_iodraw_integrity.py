import html
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOW_PATH = ROOT / "all" / "未命名绘图.iodraw"


def clean_value(value):
    text = html.unescape(value or "")
    return re.sub(r"<[^>]*>", "", text).strip()


class ParkingFlowTest(unittest.TestCase):
    def test_qr_success_actions_use_the_matching_parking_side(self):
        root = ET.parse(FLOW_PATH).getroot()
        cells = {
            cell.get("id"): cell
            for cell in root.iter("mxCell")
            if cell.get("id")
        }

        self.assertEqual(
            "左转摄像头进行二维码识别",
            clean_value(cells["2C-E8wXzLExmKxaGtvue-94"].get("value")),
        )
        self.assertEqual(
            "倒车入库至左边车位",
            clean_value(cells["2C-E8wXzLExmKxaGtvue-101"].get("value")),
        )
        self.assertEqual(
            "右转摄像头进行二维码识别",
            clean_value(cells["2C-E8wXzLExmKxaGtvue-102"].get("value")),
        )
        self.assertEqual(
            "倒车入库至右边车位",
            clean_value(cells["2C-E8wXzLExmKxaGtvue-110"].get("value")),
        )


if __name__ == "__main__":
    unittest.main()
