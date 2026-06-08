import html
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = [
    REPO_ROOT / "all" / "未命名绘图.iodraw",
    REPO_ROOT / "all" / "未命名绘图.iodraw.iodraw",
]
MAIN_FLOW = REPO_ROOT / "all" / "未命名绘图.iodraw"


def load_cells(path):
    root = ET.parse(path).getroot().find("root")
    if root is None:
        raise AssertionError(f"{path} is missing mxGraphModel/root")
    cells = root.findall("mxCell")
    by_id = {}
    for cell in cells:
        cell_id = cell.attrib.get("id")
        if not cell_id:
            continue
        if cell_id in by_id:
            raise AssertionError(f"{path} has duplicate mxCell id {cell_id}")
        by_id[cell_id] = cell
    return cells, by_id


def visible_text(cell):
    value = html.unescape(cell.attrib.get("value", ""))
    value = re.sub(r"<br\s*/?>", "\n", value)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def point_y(edge, point_kind):
    geometry = edge.find("mxGeometry")
    for point in geometry.findall("mxPoint"):
        if point.attrib.get("as") == point_kind:
            return point.attrib["y"]
    raise AssertionError(f"{edge.attrib.get('id')} has no {point_kind}")


class IodrawIntegrityTest(unittest.TestCase):
    def test_all_files_parse_and_references_resolve(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells, by_id = load_cells(path)
                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.attrib.get(attr)
                        self.assertTrue(
                            not ref or ref in by_id,
                            f"{path} cell {cell.attrib.get('id')} has missing {attr} {ref}",
                        )

    def test_parking_qr_success_branches_target_correct_side(self):
        _, by_id = load_cells(MAIN_FLOW)

        self.assertIn("左转摄像头", visible_text(by_id["2C-E8wXzLExmKxaGtvue-94"]))
        self.assertIn("倒车入库至左边车位", visible_text(by_id["2C-E8wXzLExmKxaGtvue-101"]))
        self.assertIn("右转摄像头", visible_text(by_id["2C-E8wXzLExmKxaGtvue-102"]))
        self.assertIn("倒车入库至右边车位", visible_text(by_id["2C-E8wXzLExmKxaGtvue-110"]))

        left_success = by_id["2C-E8wXzLExmKxaGtvue-99"]
        right_success = by_id["2C-E8wXzLExmKxaGtvue-108"]
        self.assertEqual(point_y(left_success, "targetPoint"), "-9.939999999999145")
        self.assertEqual(point_y(right_success, "targetPoint"), "389.06000000000085")

        self.assertEqual(by_id["2C-E8wXzLExmKxaGtvue-120"].attrib["source"], "2C-E8wXzLExmKxaGtvue-101")
        self.assertEqual(by_id["2C-E8wXzLExmKxaGtvue-120"].attrib["target"], "2C-E8wXzLExmKxaGtvue-115")
        self.assertEqual(by_id["2C-E8wXzLExmKxaGtvue-116"].attrib["source"], "2C-E8wXzLExmKxaGtvue-110")
        self.assertEqual(by_id["2C-E8wXzLExmKxaGtvue-116"].attrib["target"], "2C-E8wXzLExmKxaGtvue-115")


if __name__ == "__main__":
    unittest.main()
