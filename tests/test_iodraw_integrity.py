import html
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = [
    ROOT / "all" / "未命名绘图.iodraw",
    ROOT / "all" / "未命名绘图.iodraw.iodraw",
]
PARKING_FLOW = ROOT / "all" / "未命名绘图.iodraw"


def parse_cells(path):
    root = ET.parse(path).getroot()
    return {cell.get("id"): cell for cell in root.iter("mxCell") if cell.get("id")}


def cell_text(cell):
    return html.unescape(cell.get("value") or "")


class IodrawIntegrityTest(unittest.TestCase):
    def test_xml_references_are_valid(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells = parse_cells(path)
                seen = set()
                duplicate_ids = set()

                for cell in ET.parse(path).getroot().iter("mxCell"):
                    cell_id = cell.get("id")
                    if cell_id in seen:
                        duplicate_ids.add(cell_id)
                    seen.add(cell_id)

                self.assertFalse(duplicate_ids)

                for cell in cells.values():
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref is not None:
                            self.assertIn(ref, cells, f"{path.name}: {cell.get('id')} {attr}={ref}")

    def test_parking_qr_success_branches_target_correct_side(self):
        cells = parse_cells(PARKING_FLOW)

        left_action = cell_text(cells["2C-E8wXzLExmKxaGtvue-101"])
        right_action = cell_text(cells["2C-E8wXzLExmKxaGtvue-110"])

        self.assertIn("倒车入库至左边车位", left_action)
        self.assertIn("倒车入库至右边车位", right_action)
        self.assertNotIn("倒车入库至左边车位", right_action)

    def test_parking_branches_rejoin_listening_state(self):
        cells = parse_cells(PARKING_FLOW)

        expected_edges = {
            "2C-E8wXzLExmKxaGtvue-101": "2C-E8wXzLExmKxaGtvue-120",
            "2C-E8wXzLExmKxaGtvue-110": "2C-E8wXzLExmKxaGtvue-116",
            "2C-E8wXzLExmKxaGtvue-111": "2C-E8wXzLExmKxaGtvue-118",
        }

        for source, edge_id in expected_edges.items():
            with self.subTest(source=source):
                edge = cells[edge_id]
                self.assertEqual(edge.get("source"), source)
                self.assertEqual(edge.get("target"), "2C-E8wXzLExmKxaGtvue-115")
                self.assertIn("进入监听状态", cell_text(cells[edge.get("target")]))


if __name__ == "__main__":
    unittest.main()
