import unittest
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
IODRAW_FILES = sorted((REPO_ROOT / "all").glob("*.iodraw*"))
MAIN_DRAWING = REPO_ROOT / "all" / "未命名绘图.iodraw"


def cells_by_id(path):
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    return {
        cell.get("id"): cell
        for cell in root.findall(".//mxCell")
        if cell.get("id")
    }


def label(cell):
    return unescape(cell.get("value") or "")


class IodrawIntegrityTest(unittest.TestCase):
    def test_xml_references_point_to_existing_cells(self):
        self.assertTrue(IODRAW_FILES, "expected iodraw files to validate")

        for path in IODRAW_FILES:
            with self.subTest(path=path.name):
                root = ET.fromstring(path.read_text(encoding="utf-8"))
                cell_list = root.findall(".//mxCell")
                ids = [cell.get("id") for cell in cell_list if cell.get("id")]
                cells = {cell.get("id"): cell for cell in cell_list if cell.get("id")}
                self.assertEqual(
                    len(ids),
                    len(set(ids)),
                    "mxCell IDs must be unique",
                )

                for cell_id, cell in cells.items():
                    for attr in ("parent", "source", "target"):
                        ref = cell.get(attr)
                        if ref is not None:
                            self.assertIn(
                                ref,
                                cells,
                                f"{cell_id} has missing {attr} reference {ref}",
                            )

    def test_left_and_right_qr_success_paths_target_matching_parking_slots(self):
        cells = cells_by_id(MAIN_DRAWING)

        self.assertIn("左转摄像头", label(cells["2C-E8wXzLExmKxaGtvue-94"]))
        self.assertIn("右转摄像头", label(cells["2C-E8wXzLExmKxaGtvue-102"]))
        self.assertEqual(
            cells["2C-E8wXzLExmKxaGtvue-104"].get("source"),
            "2C-E8wXzLExmKxaGtvue-98",
        )
        self.assertEqual(
            cells["2C-E8wXzLExmKxaGtvue-104"].get("target"),
            "2C-E8wXzLExmKxaGtvue-102",
        )

        left_success = label(cells["2C-E8wXzLExmKxaGtvue-101"])
        right_success = label(cells["2C-E8wXzLExmKxaGtvue-110"])

        self.assertIn("倒车入库至左边车位", left_success)
        self.assertIn("倒车入库至右边车位", right_success)
        self.assertNotIn("倒车入库至左边车位", right_success)

        self.assertEqual(
            cells["2C-E8wXzLExmKxaGtvue-120"].get("target"),
            "2C-E8wXzLExmKxaGtvue-115",
        )
        self.assertEqual(
            cells["2C-E8wXzLExmKxaGtvue-116"].get("target"),
            "2C-E8wXzLExmKxaGtvue-115",
        )


if __name__ == "__main__":
    unittest.main()
