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


def visible_text(cell):
    value = html.unescape(cell.attrib.get("value", ""))
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


class IodrawIntegrityTest(unittest.TestCase):
    def parse_cells(self, path):
        root = ET.parse(path).getroot()
        cells = root.findall(".//mxCell")
        by_id = {}
        duplicate_ids = []
        for cell in cells:
            cell_id = cell.attrib.get("id")
            if not cell_id:
                continue
            if cell_id in by_id:
                duplicate_ids.append(cell_id)
            by_id[cell_id] = cell
        self.assertFalse(duplicate_ids, f"{path} has duplicate mxCell ids: {duplicate_ids}")
        return cells, by_id

    def test_graph_references_are_valid(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path):
                cells, by_id = self.parse_cells(path)
                missing = []
                for cell in cells:
                    cell_id = cell.attrib.get("id", "<missing id>")
                    for attr in ("parent", "source", "target"):
                        ref = cell.attrib.get(attr)
                        if ref is not None and ref not in by_id:
                            missing.append((cell_id, attr, ref))
                self.assertFalse(missing, f"{path} has missing references: {missing}")

    def test_parking_qr_success_paths_match_camera_direction(self):
        _, by_id = self.parse_cells(ROOT / "all" / "未命名绘图.iodraw")

        self.assertEqual(visible_text(by_id["2C-E8wXzLExmKxaGtvue-94"]), "左转摄像头进行二维码识别")
        self.assertEqual(visible_text(by_id["2C-E8wXzLExmKxaGtvue-101"]), "倒车入库至左边车位")
        self.assertEqual(by_id["2C-E8wXzLExmKxaGtvue-120"].attrib["source"], "2C-E8wXzLExmKxaGtvue-101")
        self.assertEqual(by_id["2C-E8wXzLExmKxaGtvue-120"].attrib["target"], "2C-E8wXzLExmKxaGtvue-115")

        self.assertEqual(visible_text(by_id["2C-E8wXzLExmKxaGtvue-102"]), "右转摄像头进行二维码识别")
        self.assertEqual(visible_text(by_id["2C-E8wXzLExmKxaGtvue-110"]), "倒车入库至右边车位")
        self.assertEqual(by_id["2C-E8wXzLExmKxaGtvue-116"].attrib["source"], "2C-E8wXzLExmKxaGtvue-110")
        self.assertEqual(by_id["2C-E8wXzLExmKxaGtvue-116"].attrib["target"], "2C-E8wXzLExmKxaGtvue-115")
        self.assertEqual(visible_text(by_id["2C-E8wXzLExmKxaGtvue-115"]), "进入监听状态")


if __name__ == "__main__":
    unittest.main()
