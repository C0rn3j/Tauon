"""Tauon Music Box - Album chart image generator"""

# Copyright © 2015-2019, Taiko2k captain(dot)gxj(at)gmail.com

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
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from .t_main import Tauon, TrackClass


class TopChart:
	def __init__(self, tauon: Tauon) -> None:
		self.pctl = tauon.pctl
		self.cache_dir = tauon.cache_directory
		self.user_dir = tauon.user_directory
		self.album_art_gen = tauon.album_art_gen

	def _load_font(self, font_name: str, font_size: int) -> ImageFont.ImageFont:
		"""Best-effort font loader.

		On Android you likely won't have 'Monospace' by name, so fall back safely.
		"""
		candidates = []

		family = font_name.strip().lower()
		if family in {"monospace", "mono"}:
			candidates += [
				"DejaVuSansMono.ttf",
				"LiberationMono-Regular.ttf",
				"DroidSansMono.ttf",
			]
		else:
			candidates += [
				f"{font_name}.ttf",
				f"{font_name}.otf",
				"DejaVuSans.ttf",
				"LiberationSans-Regular.ttf",
			]

		for candidate in candidates:
			try:
				return ImageFont.truetype(candidate, font_size)
			except Exception:
				pass

		return ImageFont.load_default()

	def _fit_text_line(
		self,
		draw: ImageDraw.ImageDraw,
		text: str,
		font: ImageFont.ImageFont,
		max_width: int,
	) -> str:
			"""
			Truncate a single line with ellipsis to fit max_width.
			"""
			if draw.textlength(text, font=font) <= max_width:
					return text

			ellipsis = "..."
			low = 0
			high = len(text)

			while low < high:
					mid = (low + high) // 2
					candidate = text[:mid].rstrip() + ellipsis
					if draw.textlength(candidate, font=font) <= max_width:
							low = mid + 1
					else:
							high = mid

			fitted = text[: max(0, low - 1)].rstrip() + ellipsis
			return fitted

	def _draw_text_block(
			self,
			draw: ImageDraw.ImageDraw,
			x: int,
			y: int,
			lines: list[str],
			font_name: str,
			font_size: int,
			max_width: int,
			max_height: int,
			fill: tuple[int, int, int] = (230, 230, 230),
	) -> None:
			"""
			Draw a vertical list of lines, shrinking font size until it fits height.
			"""
			while font_size > 6:
					font = self._load_font(font_name, font_size)

					bbox = draw.textbbox((0, 0), "Ag", font=font)
					line_height = max(1, bbox[3] - bbox[1] + 4)

					total_height = line_height * len(lines)
					if total_height <= max_height:
							break
					font_size -= 1

			font = self._load_font(font_name, font_size)
			bbox = draw.textbbox((0, 0), "Ag", font=font)
			line_height = max(1, bbox[3] - bbox[1] + 4)

			cy = y
			for line in lines:
					fitted = self._fit_text_line(draw, line, font, max_width)
					draw.text((x, cy), fitted, font=font, fill=fill)
					cy += line_height
					if cy > y + max_height:
							break

	def generate(
		self,
		tracks: list[TrackClass],
		bg: tuple[int, int, int] = (10, 10, 10),
		rows: int = 3,
		columns: int = 3,
		show_lables: bool = True,
		font: str = "Monospace 10",
		tile: bool = False,
		cascade: tuple[tuple[int, int, int], tuple[int, int, int]] | None = None,
	) -> bool | str:
		# Main control variables
		border = 29
		text_offset = -7
		size = 170
		spacing = 9

		mode = 1
		if cascade:
			mode = 2

		if tile:
			border = 0
			spacing = 0
			size = 160
			text_offset = 15

		# Determine the final width and height of album grid
		h = round((border * 2) + (size * rows) + (spacing * (rows - 1)))
		w = round((border * 2) + (size * columns) + (spacing * (columns - 1)))

		if mode == 2:
			r1, r2, r3 = cascade[0]
			logging.info(r1 * 2 + r2 * 2 + r3 * 2)
			sets = []
			for q in range(100, 10000):
				a = q / r1
				b = q / r2
				c = q / r3

				if a - int(a) == b - int(b) == c - int(c) == 0:
					sets.append((int(a), int(b), int(c)))

			if not sets:
				return False

			abc = None
			for s in sets:
				if s[(r1, r2, r3).index(min((r1, r2, r3)))] > 165:
					abc = s
					break
			else:
				return False

			d1, d2, d3 = cascade[1]

			w = round(border * 2) + (abc[0] * r1)
			h = round(border * 2) + (abc[0] * d1) + (abc[1] * d2) + (abc[2] * d3)

		ww = w
		i = -1

		positions = []

		# Grid mode
		if mode == 1:
			for r in range(rows):
				for c in range(columns):
					i += 1

					# Break if we run out of albums
					if i > len(tracks) - 1:
						break

					# Determine coordinates for current album
					x = round(border + ((spacing + size) * c))
					y = round(border + ((spacing + size) * r))

					positions.append((tracks[i], x, y, size))

				positions.append(False)

		# Cascade mode
		elif mode == 2:
			a, b, c = abc

			size = a
			spacing = 0
			inv_space = 0
			if not tile:
				inv_space = 8

			x = border
			y = border

			for d in range(d1):
				for cl in range(r1):
					i += 1
					x = border + (spacing + size) * cl
					if i > len(tracks) - 1:
						break
					positions.append((tracks[i], x + inv_space // 2, y + inv_space // 2, size - inv_space))
				y += spacing + size

			size = b
			if not tile:
				inv_space = 6
			positions.append(False)

			for d in range(d2):
				for cl in range(r2):
					i += 1
					x = border + (spacing + size) * cl
					logging.info(x)
					if i > len(tracks) - 1:
						break
					positions.append((tracks[i], x + inv_space // 2, y + inv_space // 2, size - inv_space))
				y += spacing + size

			size = c
			if not tile:
				inv_space = 4
			positions.append(False)

			for d in range(d3):
				for cl in range(r3):
					i += 1
					x = border + (spacing + size) * cl
					if i > len(tracks) - 1:
						break
					positions.append((tracks[i], x + inv_space // 2, y + inv_space // 2, size - inv_space))
				y += spacing + size

		# Parse font
		font_comp = font.split(" ")
		font_size = int(font_comp.pop())
		font_name = " ".join(font_comp) if font_comp else "Monospace"

		col_w = 500
		two_col = False
		if len(positions) * (font_size + 4) > h - border * 2:
			two_col = True
			font_size += 1
			col_w = 380

		if show_lables:
			ww += col_w  # Add extra area to final size for text
			if two_col:
				ww += col_w + 20

		text_lines: list[str] = []
		b_text_lines: list[str] = []
		second_col = False

		for item in positions:
			if item is False:
				if not second_col:
					text_lines.append("")
				else:
					b_text_lines.append("")

				if two_col:
					second_col = not second_col
				continue

			track, x, y, size = item
			artist = track.album_artist or track.artist
			line = f"{artist} - {track.album}"

			if not second_col:
				text_lines.append(line)
			else:
				b_text_lines.append(line)

		canvas = Image.new("RGB", (ww, h), bg)
		draw = ImageDraw.Draw(canvas)

		for item in positions:
			if item is False:
				continue

			track, x, y, size = item

			try:
				art_file = self.album_art_gen.save_thumb(track, (size, size), None, png=True, zoom=True)
			except Exception:
				logging.exception("Failed to save album art as file object")
				continue

			if not art_file:
				continue

			try:
				art = Image.open(art_file).convert("RGB")
				if art.size != (size, size):
					art = art.resize((size, size), Image.Resampling.LANCZOS)
				canvas.paste(art, (x, y))
			except Exception:
				logging.exception("Failed to load or paste album art")
				continue

		if show_lables:
			y_text_padding = 3
			if tile:
				y_text_padding += 6

			self._draw_text_block(
				draw=draw,
				x=w + text_offset,
				y=border + y_text_padding,
				lines=text_lines,
				font_name=font_name,
				font_size=font_size,
				max_width=col_w - text_offset - spacing,
				max_height=h - border,
				fill=(230, 230, 230),
			)

		if b_text_lines:
			y_text_padding = 3
			if tile:
				y_text_padding += 6

			self._draw_text_block(
				draw=draw,
				x=w + col_w + 10 + text_offset,
				y=border + y_text_padding,
				lines=b_text_lines,
				font_name=font_name,
				font_size=font_size,
				max_width=col_w - text_offset - spacing,
				max_height=h - border,
				fill=(230, 230, 230),
			)

		output_path = os.path.join(self.user_dir, "chart.png")
		canvas.save(output_path, "PNG")

		# Convert to JPEG for convenience
		output_path2 = os.path.join(self.user_dir, "chart.jpg")
		im = Image.open(output_path)
		im.save(output_path2, "JPEG", quality=92)

		return output_path2
