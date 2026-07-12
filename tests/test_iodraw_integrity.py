import html
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = sorted((REPO_ROOT / "all").glob("*.iodraw*"))
PRIMARY_FLOW = REPO_ROOT / "all" / "未命名绘图.iodraw"


def parse_cells(path):
    root = ET.parse(path).getroot().find("root")
    if root is None:
        raise AssertionError(f"{path} has no mxGraphModel/root")
    cells = root.findall("mxCell")
    return cells, {cell.get("id"): cell for cell in cells}


def plain_value(cell):
    value = html.unescape(cell.get("value") or "")
    value = value.replace("<br>", "\n").replace("&nbsp;", " ")
    return re.sub(r"<[^>]*>", "", value)


class IodrawIntegrityTest(unittest.TestCase):
    def test_all_iodraw_files_parse_and_reference_existing_cells(self):
        self.assertGreater(len(IODRAW_FILES), 0)

        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                cells, by_id = parse_cells(path)
                ids = [cell.get("id") for cell in cells]
                self.assertNotIn(None, ids)
                self.assertEqual(len(ids), len(set(ids)))

                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref:
                            self.assertIn(ref, by_id, f"{cell.get('id')} has missing {attr}={ref}")

    def test_iodraw_payloads_do_not_contain_executable_html(self):
        dangerous_patterns = ("<script", "javascript:", "onerror=", "onclick=")

        for path in IODRAW_FILES:
            cells, _ = parse_cells(path)
            with self.subTest(path=path.name):
                for cell in cells:
                    payload = html.unescape(
                        " ".join(cell.get(attr) or "" for attr in ("value", "style"))
                    ).lower()
                    for pattern in dangerous_patterns:
                        self.assertNotIn(pattern, payload, cell.get("id"))

    def test_left_and_right_parking_success_actions_target_distinct_bays(self):
        _, by_id = parse_cells(PRIMARY_FLOW)

        self.assertEqual(
            plain_value(by_id["2C-E8wXzLExmKxaGtvue-101"]),
            "倒车入库至左边车位",
        )
        self.assertEqual(
            plain_value(by_id["2C-E8wXzLExmKxaGtvue-110"]),
            "倒车入库至右边车位",
        )

    def test_parking_success_actions_return_to_listening_state(self):
        cells, by_id = parse_cells(PRIMARY_FLOW)
        expected_target = "2C-E8wXzLExmKxaGtvue-115"
        self.assertEqual(plain_value(by_id[expected_target]), "进入监听状态")

        edges = {(cell.get("source"), cell.get("target")) for cell in cells if cell.get("edge") == "1"}
        self.assertIn(("2C-E8wXzLExmKxaGtvue-101", expected_target), edges)
        self.assertIn(("2C-E8wXzLExmKxaGtvue-110", expected_target), edges)


if __name__ == "__main__":
    unittest.main()
