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


def parse_cells(path):
    root = ET.parse(path).getroot()
    cells = {}
    for cell in root.iter("mxCell"):
        cell_id = cell.get("id")
        if cell_id:
            if cell_id in cells:
                raise AssertionError(f"{path} has duplicate mxCell id {cell_id}")
            cells[cell_id] = cell
    return cells


def plain_value(cell):
    value = html.unescape(cell.get("value") or "")
    return re.sub(r"<[^>]+>", "", value).replace("\xa0", " ").strip()


class IodrawIntegrityTest(unittest.TestCase):
    def test_explicit_cell_references_exist(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path):
                cells = parse_cells(path)
                missing = []
                for cell in cells.values():
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref and ref not in cells:
                            missing.append((cell.get("id"), attr, ref))
                self.assertEqual([], missing)

    def test_parking_qr_success_branches_match_camera_side(self):
        cells = parse_cells(ROOT / "all" / "未命名绘图.iodraw")

        self.assertEqual(
            "倒车入库至左边车位",
            plain_value(cells["2C-E8wXzLExmKxaGtvue-101"]),
        )
        self.assertEqual(
            "倒车入库至右边车位",
            plain_value(cells["2C-E8wXzLExmKxaGtvue-110"]),
        )

        edges = {
            (cell.get("source"), cell.get("target"))
            for cell in cells.values()
            if cell.get("edge") == "1"
        }
        listen_id = "2C-E8wXzLExmKxaGtvue-115"
        self.assertIn(("2C-E8wXzLExmKxaGtvue-101", listen_id), edges)
        self.assertIn(("2C-E8wXzLExmKxaGtvue-110", listen_id), edges)


if __name__ == "__main__":
    unittest.main()
