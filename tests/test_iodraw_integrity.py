import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = sorted((REPO_ROOT / "all").glob("*.iodraw"))
PARKING_FLOW = REPO_ROOT / "all" / "未命名绘图.iodraw"


def parse(path):
    return ET.parse(path).getroot()


def cell_map(root):
    return {cell.get("id"): cell for cell in root.findall(".//mxCell") if cell.get("id")}


def text_value(cell):
    return cell.get("value") or ""


class IodrawIntegrityTest(unittest.TestCase):
    def test_iodraw_files_are_well_formed_with_valid_references(self):
        self.assertTrue(IODRAW_FILES, "expected iodraw files under all/")
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                root = parse(path)
                cells = root.findall(".//mxCell")
                ids = [cell.get("id") for cell in cells if cell.get("id")]
                self.assertEqual(len(ids), len(set(ids)), "mxCell ids must be unique")

                known_ids = set(ids)
                missing = []
                for cell in cells:
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref and ref not in known_ids:
                            missing.append((cell.get("id"), attr, ref))
                self.assertEqual([], missing)

    def test_iodraw_values_do_not_embed_active_script_payloads(self):
        dangerous = re.compile(r"<\s*script|javascript:|on(?:click|error|load)\s*=", re.I)
        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                root = parse(path)
                offenders = []
                for cell in root.findall(".//mxCell"):
                    combined = " ".join(filter(None, [cell.get("value"), cell.get("style")]))
                    if dangerous.search(combined):
                        offenders.append(cell.get("id"))
                self.assertEqual([], offenders)

    def test_left_and_right_qr_success_branches_park_in_distinct_bays(self):
        cells = cell_map(parse(PARKING_FLOW))

        self.assertIn("倒车入库至左边车位", text_value(cells["2C-E8wXzLExmKxaGtvue-101"]))
        self.assertIn("倒车入库至右边车位", text_value(cells["2C-E8wXzLExmKxaGtvue-110"]))

        for action_id in ("2C-E8wXzLExmKxaGtvue-101", "2C-E8wXzLExmKxaGtvue-110"):
            outgoing_targets = [
                cell.get("target")
                for cell in cells.values()
                if cell.get("source") == action_id
            ]
            self.assertIn("2C-E8wXzLExmKxaGtvue-115", outgoing_targets)
            self.assertIn("进入监听状态", text_value(cells["2C-E8wXzLExmKxaGtvue-115"]))


if __name__ == "__main__":
    unittest.main()
