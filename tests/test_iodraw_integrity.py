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


def clean_value(value):
    if value is None:
        return ""
    unescaped = html.unescape(value)
    return re.sub(r"<[^>]+>", "", unescaped).strip()


class IodrawIntegrityTest(unittest.TestCase):
    def parse_cells(self, path):
        root = ET.parse(path).getroot()
        graph_root = root.find("root")
        self.assertIsNotNone(graph_root, f"{path} must contain an mxGraph root")
        return graph_root.findall("mxCell")

    def test_iodraw_files_are_parseable_and_references_resolve(self):
        dangerous_patterns = ("<script", "javascript:", "onerror=", "onclick=")

        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells = self.parse_cells(path)
                ids = [cell.attrib["id"] for cell in cells if "id" in cell.attrib]
                self.assertEqual(len(ids), len(set(ids)), f"{path} contains duplicate mxCell ids")

                id_set = set(ids)
                for cell in cells:
                    cell_text = " ".join(
                        cell.attrib.get(attr, "").lower()
                        for attr in ("value", "style")
                    )
                    for pattern in dangerous_patterns:
                        self.assertNotIn(pattern, cell_text, f"{path} contains {pattern}")

                    for attr in ("parent", "source", "target"):
                        ref = cell.attrib.get(attr)
                        if ref is not None:
                            self.assertIn(ref, id_set, f"{path} has missing {attr} reference {ref}")

    def test_parking_qr_success_branches_target_their_respective_bays(self):
        cells = {cell.attrib.get("id"): cell for cell in self.parse_cells(MAIN_FLOW)}

        self.assertEqual(
            clean_value(cells["2C-E8wXzLExmKxaGtvue-101"].attrib.get("value")),
            "倒车入库至左边车位",
        )
        self.assertEqual(
            clean_value(cells["2C-E8wXzLExmKxaGtvue-110"].attrib.get("value")),
            "倒车入库至右边车位",
        )
        self.assertEqual(
            clean_value(cells["2C-E8wXzLExmKxaGtvue-115"].attrib.get("value")),
            "进入监听状态",
        )


if __name__ == "__main__":
    unittest.main()
