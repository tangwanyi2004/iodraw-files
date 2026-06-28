import re
import unittest
from html import unescape
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
MAIN_DIAGRAM = ROOT / "all" / "未命名绘图.iodraw"
ALL_DIAGRAMS = [
    MAIN_DIAGRAM,
    ROOT / "all" / "未命名绘图.iodraw.iodraw",
]


def load_cells(path):
    root = ElementTree.parse(path).getroot().find("root")
    return {cell.attrib["id"]: cell for cell in root.findall("mxCell")}


def text_value(cell):
    value = unescape(cell.attrib.get("value", ""))
    return re.sub(r"<[^>]+>", "", value).strip()


class IodrawIntegrityTest(unittest.TestCase):
    def test_diagrams_have_valid_xml_references(self):
        for path in ALL_DIAGRAMS:
            with self.subTest(path=path.name):
                cells = load_cells(path)
                ids = set(cells)
                missing = []

                for cell in cells.values():
                    for attr in ("parent", "source", "target"):
                        ref = cell.attrib.get(attr)
                        if ref and ref not in ids:
                            missing.append((cell.attrib["id"], attr, ref))

                self.assertFalse(missing)

    def test_parking_qr_success_paths_target_correct_side(self):
        cells = load_cells(MAIN_DIAGRAM)

        self.assertEqual(
            "倒车入库至左边车位",
            text_value(cells["2C-E8wXzLExmKxaGtvue-101"]),
        )
        self.assertEqual(
            "倒车入库至右边车位",
            text_value(cells["2C-E8wXzLExmKxaGtvue-110"]),
        )

        self.assertEqual(
            "进入监听状态",
            text_value(cells[cells["2C-E8wXzLExmKxaGtvue-120"].attrib["target"]]),
        )
        self.assertEqual(
            "进入监听状态",
            text_value(cells[cells["2C-E8wXzLExmKxaGtvue-116"].attrib["target"]]),
        )


if __name__ == "__main__":
    unittest.main()
