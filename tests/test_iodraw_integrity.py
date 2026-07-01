import re
import unittest
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = [
    ROOT / "all" / "未命名绘图.iodraw",
    ROOT / "all" / "未命名绘图.iodraw.iodraw",
]


def parse_cells(path):
    root = ET.parse(path).getroot().find("root")
    if root is None:
        raise AssertionError(f"{path} has no root cell container")
    return list(root.findall("mxCell"))


def cell_text(cell):
    value = unescape(cell.attrib.get("value", ""))
    value = re.sub(r"<br\s*/?>", "\n", value)
    value = re.sub(r"<[^>]+>", "", value)
    return unescape(value).strip()


class IodrawIntegrityTest(unittest.TestCase):
    def test_xml_references_are_valid(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells = parse_cells(path)
                ids = [cell.attrib["id"] for cell in cells]
                self.assertEqual(len(ids), len(set(ids)))

                id_set = set(ids)
                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.attrib.get(attr)
                        if ref:
                            self.assertIn(ref, id_set, f"{cell.attrib['id']} has missing {attr} {ref}")

                    if cell.attrib.get("edge") != "1":
                        continue

                    geometry = cell.find("mxGeometry")
                    has_source = bool(cell.attrib.get("source"))
                    has_target = bool(cell.attrib.get("target"))
                    has_source_point = geometry is not None and geometry.find("mxPoint[@as='sourcePoint']") is not None
                    has_target_point = geometry is not None and geometry.find("mxPoint[@as='targetPoint']") is not None
                    self.assertTrue(
                        has_source or has_source_point,
                        f"{cell.attrib['id']} edge has no source endpoint",
                    )
                    self.assertTrue(
                        has_target or has_target_point,
                        f"{cell.attrib['id']} edge has no target endpoint",
                    )

    def test_parking_qr_success_branches_use_correct_side(self):
        cells = {cell.attrib["id"]: cell for cell in parse_cells(ROOT / "all" / "未命名绘图.iodraw")}

        left_camera = cell_text(cells["2C-E8wXzLExmKxaGtvue-94"])
        left_success = cell_text(cells["2C-E8wXzLExmKxaGtvue-101"])
        right_camera = cell_text(cells["2C-E8wXzLExmKxaGtvue-102"])
        right_success = cell_text(cells["2C-E8wXzLExmKxaGtvue-110"])
        monitor = cell_text(cells["2C-E8wXzLExmKxaGtvue-115"])

        self.assertIn("左转摄像头", left_camera)
        self.assertEqual(left_success, "倒车入库至左边车位")
        self.assertIn("右转摄像头", right_camera)
        self.assertEqual(right_success, "倒车入库至右边车位")
        self.assertEqual(monitor, "进入监听状态")

        rejoin_edges = {
            edge.attrib["source"]: edge.attrib["target"]
            for edge in cells.values()
            if edge.attrib.get("edge") == "1" and edge.attrib.get("source") and edge.attrib.get("target")
        }
        self.assertEqual(rejoin_edges["2C-E8wXzLExmKxaGtvue-101"], "2C-E8wXzLExmKxaGtvue-115")
        self.assertEqual(rejoin_edges["2C-E8wXzLExmKxaGtvue-110"], "2C-E8wXzLExmKxaGtvue-115")


if __name__ == "__main__":
    unittest.main()
