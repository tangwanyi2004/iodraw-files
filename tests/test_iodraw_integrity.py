import html
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = [
    ROOT / "all" / "未命名绘图.iodraw",
    ROOT / "all" / "未命名绘图.iodraw.iodraw",
]


def _cells(path):
    return ET.parse(path).getroot().find("root").findall("mxCell")


def _plain_value(cell):
    return html.unescape(cell.get("value", ""))


class IodrawIntegrityTest(unittest.TestCase):
    def test_cell_ids_are_unique(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                ids = [cell.get("id") for cell in _cells(path)]
                self.assertEqual(len(ids), len(set(ids)))

    def test_references_point_to_existing_cells(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells = _cells(path)
                ids = {cell.get("id") for cell in cells}
                missing = []
                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref and ref not in ids:
                            missing.append((cell.get("id"), attr, ref))
                self.assertEqual([], missing)

    def test_left_and_right_parking_success_branches_target_correct_slots(self):
        cells_by_id = {cell.get("id"): cell for cell in _cells(IODRAW_FILES[0])}

        self.assertIn("倒车入库至左边车位", _plain_value(cells_by_id["2C-E8wXzLExmKxaGtvue-101"]))
        self.assertIn("倒车入库至右边车位", _plain_value(cells_by_id["2C-E8wXzLExmKxaGtvue-110"]))

        parking_edges = {
            cell.get("source"): cell.get("target")
            for cell in cells_by_id.values()
            if cell.get("edge") == "1"
        }
        self.assertEqual("2C-E8wXzLExmKxaGtvue-115", parking_edges["2C-E8wXzLExmKxaGtvue-101"])
        self.assertEqual("2C-E8wXzLExmKxaGtvue-115", parking_edges["2C-E8wXzLExmKxaGtvue-110"])
        self.assertIn("进入监听状态", _plain_value(cells_by_id["2C-E8wXzLExmKxaGtvue-115"]))


if __name__ == "__main__":
    unittest.main()
