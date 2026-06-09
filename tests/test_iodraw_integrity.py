import html
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAWING_FILES = (
    ROOT / "all" / "未命名绘图.iodraw",
    ROOT / "all" / "未命名绘图.iodraw.iodraw",
)
MAIN_DRAWING = ROOT / "all" / "未命名绘图.iodraw"
RIGHT_PARKING_ACTION_ID = "2C-E8wXzLExmKxaGtvue-110"
LEFT_PARKING_ACTION_ID = "2C-E8wXzLExmKxaGtvue-101"
MONITOR_STATE_ID = "2C-E8wXzLExmKxaGtvue-115"


def parse_cells(path):
    root = ET.parse(path).getroot().find("root")
    if root is None:
        raise AssertionError(f"{path} does not contain an mxGraphModel root")
    cells = root.findall("mxCell")
    return cells, {cell.attrib["id"]: cell for cell in cells}


def cell_text(cell):
    value = html.unescape(cell.attrib.get("value", ""))
    value = value.replace("&nbsp;", " ")
    value = re.sub(r"<[^>]+>", "", value)
    return value.strip()


class IodrawIntegrityTest(unittest.TestCase):
    def test_drawing_files_have_valid_references(self):
        for path in DRAWING_FILES:
            with self.subTest(path=path.name):
                cells, cell_by_id = parse_cells(path)

                self.assertEqual(
                    len(cell_by_id),
                    len(cells),
                    f"{path} contains duplicate mxCell ids",
                )

                for cell in cells:
                    cell_id = cell.attrib["id"]
                    for attr in ("parent", "source", "target"):
                        ref = cell.attrib.get(attr)
                        if ref is not None:
                            self.assertIn(
                                ref,
                                cell_by_id,
                                f"{path}: {cell_id} has missing {attr} reference {ref}",
                            )

    def test_left_and_right_parking_success_actions_are_distinct(self):
        cells, cell_by_id = parse_cells(MAIN_DRAWING)
        labels = [cell_text(cell) for cell in cells]

        self.assertEqual(labels.count("倒车入库至左边车位"), 1)
        self.assertEqual(labels.count("倒车入库至右边车位"), 1)
        self.assertEqual(cell_text(cell_by_id[LEFT_PARKING_ACTION_ID]), "倒车入库至左边车位")
        self.assertEqual(cell_text(cell_by_id[RIGHT_PARKING_ACTION_ID]), "倒车入库至右边车位")

        edges = [cell for cell in cells if cell.attrib.get("edge") == "1"]
        self.assertTrue(
            any(
                edge.attrib.get("source") == LEFT_PARKING_ACTION_ID
                and edge.attrib.get("target") == MONITOR_STATE_ID
                for edge in edges
            ),
            "left parking success action should re-enter monitoring state",
        )
        self.assertTrue(
            any(
                edge.attrib.get("source") == RIGHT_PARKING_ACTION_ID
                and edge.attrib.get("target") == MONITOR_STATE_ID
                for edge in edges
            ),
            "right parking success action should re-enter monitoring state",
        )


if __name__ == "__main__":
    unittest.main()
