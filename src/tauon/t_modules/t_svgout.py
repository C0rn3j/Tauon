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

import fitz  # PyMuPDF


def render_icons(source_directory: str, output_directory: str, scale: int) -> None:
	"""Render SVG files to PNG."""
	targets = []

	for file in os.listdir(source_directory):
		in_path = os.path.join(source_directory, file)
		if file.endswith(".svg") and os.path.isfile(in_path):
			targets.append(file)

	os.makedirs(output_directory, exist_ok=True)

	for file in targets:
		name = os.path.splitext(file)[0]
		in_path = os.path.join(source_directory, file)
		out_path = os.path.join(output_directory, name + ".png")

		try:
			doc = fitz.open(in_path)
			if doc.page_count == 0:
				logging.error(f"Couldn't load {in_path}")
				continue

			page = doc[0]

			# Scale SVG to output size
			matrix = fitz.Matrix(scale, scale)

			# alpha=True preserves transparency
			pixmap = page.get_pixmap(matrix=matrix, alpha=True)
			pixmap.save(out_path)

			doc.close()

		except Exception as exc:
			logging.exception(f"Failed to render {in_path}: {exc}")
