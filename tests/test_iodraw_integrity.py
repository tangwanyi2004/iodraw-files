import html
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = sorted((REPO_ROOT / "all").glob("*.iodraw*"))


class IodrawIntegrityTest(unittest.TestCase):
    def _parse_cells(self, path):
        model = ET.parse(path).getroot()
        graph_root = model.find("root")
        self.assertIsNotNone(graph_root, f"{path} is missing mxGraphModel/root")
        cells = graph_root.findall("mxCell")
        by_id = {cell.attrib["id"]: cell for cell in cells if "id" in cell.attrib}
        return cells, by_id

    def test_all_iodraw_files_have_valid_references(self):
        self.assertTrue(IODRAW_FILES, "expected at least one iodraw file")

        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells, by_id = self._parse_cells(path)
                ids = [cell.attrib["id"] for cell in cells if "id" in cell.attrib]
                self.assertEqual(len(ids), len(set(ids)), f"{path} contains duplicate mxCell ids")

                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.attrib.get(attr)
                        if ref:
                            self.assertIn(ref, by_id, f"{path}: {cell.attrib.get('id')} has missing {attr} {ref}")

    def test_all_iodraw_files_avoid_active_script_payloads(self):
        dangerous_patterns = ("<script", "javascript:", "onerror=", "onclick=")

        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells, _ = self._parse_cells(path)
                for cell in cells:
                    payload = " ".join(
                        html.unescape(cell.attrib.get(attr, "")).lower()
                        for attr in ("value", "style")
                    )
                    for pattern in dangerous_patterns:
                        self.assertNotIn(pattern, payload, f"{path}: {cell.attrib.get('id')} contains {pattern}")

    def test_parking_qr_branches_target_distinct_parking_bays(self):
        cells, by_id = self._parse_cells(REPO_ROOT / "all" / "未命名绘图.iodraw")

        left_success = by_id["2C-E8wXzLExmKxaGtvue-101"].attrib["value"]
        right_success = by_id["2C-E8wXzLExmKxaGtvue-110"].attrib["value"]
        listen_state = by_id["2C-E8wXzLExmKxaGtvue-115"].attrib["value"]

        self.assertRegex(left_success, re.compile("倒车入库至左边车位"))
        self.assertRegex(right_success, re.compile("倒车入库至右边车位"))
        self.assertRegex(listen_state, re.compile("进入监听状态"))

        outgoing = {}
        for cell in cells:
            source = cell.attrib.get("source")
            target = cell.attrib.get("target")
            if source and target:
                outgoing.setdefault(source, set()).add(target)

        self.assertIn("2C-E8wXzLExmKxaGtvue-115", outgoing["2C-E8wXzLExmKxaGtvue-101"])
        self.assertIn("2C-E8wXzLExmKxaGtvue-115", outgoing["2C-E8wXzLExmKxaGtvue-110"])


if __name__ == "__main__":
    unittest.main()
