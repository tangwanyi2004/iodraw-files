from html import unescape
from pathlib import Path
import re
import unittest
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = [
    ROOT / "all" / "未命名绘图.iodraw",
    ROOT / "all" / "未命名绘图.iodraw.iodraw",
]


def text_value(cell):
    value = unescape(cell.get("value") or "")
    return re.sub(r"<[^>]*>", "", value).strip()


class IodrawIntegrityTest(unittest.TestCase):
    def test_all_iodraw_files_have_valid_references(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                root = ET.parse(path).getroot()
                cells = root.findall(".//mxCell")
                ids = [cell.get("id") for cell in cells if cell.get("id")]

                self.assertEqual(len(ids), len(set(ids)), "duplicate mxCell ids")

                id_set = set(ids)
                missing = []
                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref and ref not in id_set:
                            missing.append((cell.get("id"), attr, ref))

                self.assertEqual([], missing)

    def test_parking_qr_success_branches_target_correct_side(self):
        root = ET.parse(ROOT / "all" / "未命名绘图.iodraw").getroot()
        cells = {cell.get("id"): cell for cell in root.findall(".//mxCell")}

        self.assertEqual(
            "倒车入库至左边车位",
            text_value(cells["2C-E8wXzLExmKxaGtvue-101"]),
        )
        self.assertEqual(
            "倒车入库至右边车位",
            text_value(cells["2C-E8wXzLExmKxaGtvue-110"]),
        )

        for edge_id, source_id in (
            ("2C-E8wXzLExmKxaGtvue-120", "2C-E8wXzLExmKxaGtvue-101"),
            ("2C-E8wXzLExmKxaGtvue-116", "2C-E8wXzLExmKxaGtvue-110"),
        ):
            with self.subTest(edge=edge_id):
                edge = cells[edge_id]
                self.assertEqual(source_id, edge.get("source"))
                self.assertEqual("2C-E8wXzLExmKxaGtvue-115", edge.get("target"))


if __name__ == "__main__":
    unittest.main()
