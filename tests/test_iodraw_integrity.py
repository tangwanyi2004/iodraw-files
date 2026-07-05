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
MAIN_FLOW = IODRAW_FILES[0]


def parse_cells(path):
    root = ET.parse(path).getroot().find("root")
    if root is None:
        raise AssertionError(f"{path} has no mxGraphModel/root element")
    return list(root)


def cell_text(cell):
    value = html.unescape(cell.get("value") or "")
    return re.sub(r"<[^>]+>", "", value)


class IodrawIntegrityTest(unittest.TestCase):
    def test_files_parse_with_unique_ids_and_valid_references(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells = parse_cells(path)
                ids = [cell.get("id") for cell in cells]
                self.assertEqual(len(ids), len(set(ids)))

                id_set = set(ids)
                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref:
                            self.assertIn(ref, id_set, f"{cell.get('id')} has missing {attr}={ref}")

    def test_values_do_not_contain_active_script_payloads(self):
        dangerous = ("<script", "javascript:", "onerror=", "onclick=", "<iframe", "<object")
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                for cell in parse_cells(path):
                    decoded = html.unescape(cell.get("value") or "").lower()
                    self.assertFalse(
                        any(pattern in decoded for pattern in dangerous),
                        f"{cell.get('id')} contains an active payload",
                    )

    def test_left_and_right_parking_success_branches_target_distinct_slots(self):
        cells = {cell.get("id"): cell for cell in parse_cells(MAIN_FLOW)}

        self.assertEqual(cell_text(cells["2C-E8wXzLExmKxaGtvue-101"]), "倒车入库至左边车位")
        self.assertEqual(cell_text(cells["2C-E8wXzLExmKxaGtvue-110"]), "倒车入库至右边车位")

        listen_state = "2C-E8wXzLExmKxaGtvue-115"
        self.assertEqual(cell_text(cells[listen_state]), "进入监听状态")
        self.assertEqual(cells["2C-E8wXzLExmKxaGtvue-120"].get("source"), "2C-E8wXzLExmKxaGtvue-101")
        self.assertEqual(cells["2C-E8wXzLExmKxaGtvue-120"].get("target"), listen_state)
        self.assertEqual(cells["2C-E8wXzLExmKxaGtvue-116"].get("source"), "2C-E8wXzLExmKxaGtvue-110")
        self.assertEqual(cells["2C-E8wXzLExmKxaGtvue-116"].get("target"), listen_state)


if __name__ == "__main__":
    unittest.main()
