import html
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = [
    ROOT / "all" / "未命名绘图.iodraw",
    ROOT / "all" / "未命名绘图.iodraw.iodraw",
]


def _cells(path):
    return ET.parse(path).getroot().findall(".//mxCell")


def _text(cell):
    return html.unescape(cell.get("value") or "")


class IodrawIntegrityTest(unittest.TestCase):
    def test_cell_references_point_to_existing_cells(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells = _cells(path)
                ids = [cell.get("id") for cell in cells if cell.get("id")]
                self.assertEqual(len(ids), len(set(ids)))

                id_set = set(ids)
                missing = []
                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref and ref not in id_set:
                            missing.append((cell.get("id"), attr, ref))

                self.assertEqual([], missing)

    def test_left_and_right_parking_success_branches_target_different_spaces(self):
        cells = {
            cell.get("id"): cell
            for cell in _cells(ROOT / "all" / "未命名绘图.iodraw")
            if cell.get("id")
        }

        self.assertIn("倒车入库至左边车位", _text(cells["2C-E8wXzLExmKxaGtvue-101"]))
        self.assertIn("倒车入库至右边车位", _text(cells["2C-E8wXzLExmKxaGtvue-110"]))
        self.assertIn("进入监听状态", _text(cells["2C-E8wXzLExmKxaGtvue-115"]))

        listening_edges = {
            cell.get("source")
            for cell in cells.values()
            if cell.get("edge") == "1" and cell.get("target") == "2C-E8wXzLExmKxaGtvue-115"
        }
        self.assertIn("2C-E8wXzLExmKxaGtvue-101", listening_edges)
        self.assertIn("2C-E8wXzLExmKxaGtvue-110", listening_edges)


if __name__ == "__main__":
    unittest.main()
