"""Tauon Music Box - SVG Module"""

# Copyright © 2019-2020, Taiko2k captain(dot)gxj(at)gmail.com

#     This file is part of Tauon Music Box.
#
#     Tauon Music Box is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Tauon Music Box is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Tauon Music Box.  If not, see <http://www.gnu.org/licenses/>.
import logging
import os
from pathlib import Path

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM


def render_icons(source_directory: str, output_directory: str, scale: int) -> None:
	"""Render SVG files to PNG without cairo"""

	source = Path(source_directory)
	output = Path(output_directory)

	output.mkdir(parents=True, exist_ok=True)

	targets = [f for f in source.iterdir() if f.suffix == ".svg" and f.is_file()]

	for svg_file in targets:
		out_path = output / (svg_file.stem + ".png")

		try:
			drawing = svg2rlg(str(svg_file))

			if drawing is None:
				logging.error("Couldn't load %s", svg_file)
				continue

			# apply scaling
			drawing.width *= scale
			drawing.height *= scale
			drawing.scale(scale, scale)

			renderPM.drawToFile(drawing, str(out_path), fmt="PNG")

		except Exception:
			logging.exception("Couldn't render %s", svg_file)
