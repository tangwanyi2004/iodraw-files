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


def parse_graph(path):
    root = ET.parse(path).getroot()
    cells = root.findall(".//mxCell")
    by_id = {cell.get("id"): cell for cell in cells if cell.get("id")}
    return root, cells, by_id


def visible_text(cell):
    text = html.unescape(cell.get("value") or "")
    text = re.sub(r"<[^>]*>", "", text)
    return html.unescape(text).strip()


def has_point(cell, point_name):
    return cell.find(f".//mxPoint[@as='{point_name}']") is not None


class IodrawIntegrityTest(unittest.TestCase):
    def test_files_are_valid_xml_with_consistent_references(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                _, cells, by_id = parse_graph(path)
                ids = [cell.get("id") for cell in cells if cell.get("id")]

                self.assertEqual(len(ids), len(set(ids)), "mxCell ids must be unique")

                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref:
                            self.assertIn(ref, by_id, f"{cell.get('id')} has missing {attr}={ref}")

                    if cell.get("edge") == "1":
                        self.assertTrue(
                            cell.get("source") or has_point(cell, "sourcePoint"),
                            f"{cell.get('id')} has no source endpoint",
                        )
                        self.assertTrue(
                            cell.get("target") or has_point(cell, "targetPoint"),
                            f"{cell.get('id')} has no target endpoint",
                        )

    def test_no_decoded_script_or_javascript_payloads(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                raw = path.read_text(encoding="utf-8")
                decoded = html.unescape(raw).lower()

                self.assertNotIn("<script", decoded)
                self.assertNotIn("javascript:", decoded)
                self.assertNotIn("data:text/html", decoded)

    def test_left_and_right_parking_success_branches_are_distinct(self):
        _, _, by_id = parse_graph(MAIN_FLOW)

        self.assertIn("左转摄像头", visible_text(by_id["2C-E8wXzLExmKxaGtvue-94"]))
        self.assertEqual("倒车入库至左边车位", visible_text(by_id["2C-E8wXzLExmKxaGtvue-101"]))

        self.assertIn("右转摄像头", visible_text(by_id["2C-E8wXzLExmKxaGtvue-102"]))
        self.assertEqual("倒车入库至右边车位", visible_text(by_id["2C-E8wXzLExmKxaGtvue-110"]))

    def test_parking_success_branches_rejoin_listener_state(self):
        _, cells, by_id = parse_graph(MAIN_FLOW)
        rejoin_id = "2C-E8wXzLExmKxaGtvue-115"

        self.assertEqual("进入监听状态", visible_text(by_id[rejoin_id]))

        edges = {(cell.get("source"), cell.get("target")) for cell in cells if cell.get("edge") == "1"}
        self.assertIn(("2C-E8wXzLExmKxaGtvue-101", rejoin_id), edges)
        self.assertIn(("2C-E8wXzLExmKxaGtvue-110", rejoin_id), edges)


if __name__ == "__main__":
    unittest.main()
