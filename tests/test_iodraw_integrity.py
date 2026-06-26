import html
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = [
    ROOT / "all" / "未命名绘图.iodraw",
    ROOT / "all" / "未命名绘图.iodraw.iodraw",
]
MAIN_FLOW_FILE = ROOT / "all" / "未命名绘图.iodraw"


def load_cells(path):
    root = ET.parse(path).getroot()
    return root.find("root").findall("mxCell")


def visible_text(cell):
    raw = cell.get("value") or ""
    return re.sub(r"<[^>]+>", "", html.unescape(raw)).strip()


class IodrawIntegrityTest(unittest.TestCase):
    def test_files_parse_and_references_resolve(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells = load_cells(path)
                ids = [cell.get("id") for cell in cells]
                id_set = set(ids)

                self.assertEqual(len(ids), len(id_set), "duplicate mxCell ids")
                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref:
                            self.assertIn(ref, id_set, f"{cell.get('id')} has missing {attr}")

                for cell in cells:
                    if cell.get("edge") != "1" or cell.get("source") or cell.get("target"):
                        continue
                    geometry = cell.find("mxGeometry")
                    points = [] if geometry is None else geometry.findall("mxPoint")
                    self.assertGreaterEqual(
                        len(points),
                        2,
                        f"{cell.get('id')} edge has neither refs nor point endpoints",
                    )

    def test_left_and_right_qr_success_branches_target_correct_parking_spaces(self):
        cells = {cell.get("id"): cell for cell in load_cells(MAIN_FLOW_FILE)}

        self.assertEqual(visible_text(cells["2C-E8wXzLExmKxaGtvue-94"]), "左转摄像头进行二维码识别")
        self.assertEqual(visible_text(cells["2C-E8wXzLExmKxaGtvue-98"]), "二维码识别结果是否为“我的停车位”")
        self.assertEqual(visible_text(cells["2C-E8wXzLExmKxaGtvue-101"]), "倒车入库至左边车位")

        self.assertEqual(visible_text(cells["2C-E8wXzLExmKxaGtvue-102"]), "右转摄像头进行二维码识别")
        self.assertEqual(visible_text(cells["2C-E8wXzLExmKxaGtvue-107"]), "二维码识别结果是否为“我的停车位”")
        self.assertEqual(visible_text(cells["2C-E8wXzLExmKxaGtvue-110"]), "倒车入库至右边车位")

        edges = [
            (cell.get("source"), cell.get("target"))
            for cell in cells.values()
            if cell.get("edge") == "1"
        ]
        self.assertIn(("2C-E8wXzLExmKxaGtvue-101", "2C-E8wXzLExmKxaGtvue-115"), edges)
        self.assertIn(("2C-E8wXzLExmKxaGtvue-110", "2C-E8wXzLExmKxaGtvue-115"), edges)


if __name__ == "__main__":
    unittest.main()
