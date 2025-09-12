import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import resvg
from affine import Affine


class SVGConverter:
    """Конвертер SVG в PNG с использованием resvg-py"""

    @staticmethod
    def convert(
        svg_path: Path,
        png_path: Optional[Path] = None,
        width: int = 1200,
    ) -> Optional[Path]:
        """
        Конвертировать SVG в PNG используя resvg-py.
        """
        try:
            if png_path is None:
                png_path = svg_path.with_suffix(".png")

            svg_string = svg_path.read_text(encoding="utf-8")

            # --- XML Parsing to get size for scaling ---
            svg_string_no_decl = re.sub(
                r"^\s*<\?xml[^>]*\?>", "", svg_string
            ).strip()
            root = ET.fromstring(svg_string_no_decl)
            original_width_str = root.attrib.get("width", "0")
            original_width = float(
                re.sub(r"[a-zA-Z%]+$", "", original_width_str)
            )

            if original_width == 0:
                viewbox_str = root.attrib.get("viewBox")
                if viewbox_str:
                    _, _, vb_width, _ = [float(v) for v in viewbox_str.split()]
                    original_width = original_width or vb_width

            scale = width / original_width if original_width > 0 else 1.0
            # --- End XML Parsing ---

            font_db = resvg.usvg.FontDatabase.default()
            font_db.load_system_fonts()
            options = resvg.usvg.Options.default()
            tree = resvg.usvg.Tree.from_str(svg_string, options, font_db)

            transform = Affine.scale(scale)
            # Передаем срез из 6 элементов, как требует библиотека
            png_data = resvg.render(tree, transform=transform[0:6])

            # Конвертируем список байтов в объект bytes и записываем в файл
            png_path.write_bytes(bytes(png_data))

            if png_path.exists():
                return png_path

            print("resvg conversion failed: could not process SVG.")
            return None

        except Exception as e:
            print(f"Error converting SVG with resvg: {e}")
            return None
