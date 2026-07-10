import html
import re
import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = [
    ROOT / "all" / "未命名绘图.iodraw",
    ROOT / "all" / "未命名绘图.iodraw.iodraw",
]
MAIN_FLOW = ROOT / "all" / "未命名绘图.iodraw"


def parse_cells(path):
    root = ET.parse(path).getroot()
    cells = root.findall(".//mxCell")
    by_id = {}
    duplicates = []
    for cell in cells:
        cell_id = cell.attrib.get("id")
        if cell_id in by_id:
            duplicates.append(cell_id)
        by_id[cell_id] = cell
    return cells, by_id, duplicates


def text_value(cell):
    return html.unescape(cell.attrib.get("value", ""))


class IodrawIntegrityTest(unittest.TestCase):
    def test_files_are_well_formed_with_valid_references(self):
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells, by_id, duplicates = parse_cells(path)
                self.assertEqual([], duplicates)

                missing_refs = []
                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.attrib.get(attr)
                        if ref and ref not in by_id:
                            missing_refs.append((cell.attrib.get("id"), attr, ref))

                self.assertEqual([], missing_refs)

    def test_cells_do_not_contain_active_script_payloads(self):
        dangerous = re.compile(
            r"<\s*script|javascript\s*:|on(?:click|error|load|mouseover)\s*=",
            re.IGNORECASE,
        )

        for path in IODRAW_FILES:
            cells, _, _ = parse_cells(path)
            with self.subTest(path=path.name):
                offenders = []
                for cell in cells:
                    payload = " ".join(
                        [
                            html.unescape(cell.attrib.get("value", "")),
                            urllib.parse.unquote(html.unescape(cell.attrib.get("value", ""))),
                            html.unescape(cell.attrib.get("style", "")),
                        ]
                    )
                    if dangerous.search(payload):
                        offenders.append(cell.attrib.get("id"))

                self.assertEqual([], offenders)

    def test_left_and_right_parking_branches_go_to_distinct_bays(self):
        _, cells, _ = parse_cells(MAIN_FLOW)

        self.assertIn("倒车入库至左边车位", text_value(cells["2C-E8wXzLExmKxaGtvue-101"]))
        self.assertIn("右转摄像头", text_value(cells["2C-E8wXzLExmKxaGtvue-102"]))
        self.assertIn("倒车入库至右边车位", text_value(cells["2C-E8wXzLExmKxaGtvue-110"]))
        self.assertIn("进入监听状态", text_value(cells["2C-E8wXzLExmKxaGtvue-115"]))

        left_success_edge = cells["2C-E8wXzLExmKxaGtvue-120"]
        right_success_edge = cells["2C-E8wXzLExmKxaGtvue-116"]
        self.assertEqual("2C-E8wXzLExmKxaGtvue-101", left_success_edge.attrib["source"])
        self.assertEqual("2C-E8wXzLExmKxaGtvue-115", left_success_edge.attrib["target"])
        self.assertEqual("2C-E8wXzLExmKxaGtvue-110", right_success_edge.attrib["source"])
        self.assertEqual("2C-E8wXzLExmKxaGtvue-115", right_success_edge.attrib["target"])


if __name__ == "__main__":
    unittest.main()
