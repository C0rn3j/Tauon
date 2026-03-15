"""Tauon Music Box - Basic Drawing and Text Drawing Functions Module"""

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

import ctypes
import io
import logging
import math
import os
from ctypes import byref, c_bool, c_float, c_size_t
from typing import TYPE_CHECKING

import sdl3
from PIL import Image, ImageDraw, ImageFont

from .t_extra import ColourRGBA, Timer, alpha_blend, coll_rect

if TYPE_CHECKING:
	from io import BytesIO

	from .t_main import Tauon

try:
	from jxlpy import JXLImagePlugin

	logging.info("Found jxlpy for JPEG XL support")
except ModuleNotFoundError:
	logging.warning("Unable to import jxlpy, JPEG XL support will be disabled.")
except Exception:
	logging.exception("Unknown error trying to import jxlpy, JPEG XL support will be disabled.")


class QuickThumbnail:
	def __init__(self, tauon: Tauon) -> None:
		self.ddt = tauon.ddt
		self.renderer = tauon.renderer
		self.items: list[QuickThumbnail] = []
		self.queue: list[QuickThumbnail] = []
		self.rect = sdl3.SDL_FRect(0.0, 0.0)
		self.texture = None
		self.surface = None
		self.size = 50
		self.alive = False
		self.url = None

	def destruct(self) -> None:
		if self.surface:
			sdl3.SDL_DestroySurface(self.surface)
			self.surface = None
		if self.texture:
			sdl3.SDL_DestroyTexture(self.texture)
			self.texture = None
		self.alive = False

	def read_and_thumbnail(self, f: str, width: int, height: int) -> None:
		g = io.BytesIO()
		g.seek(0)
		im = Image.open(f)
		im.thumbnail((width, height), Image.Resampling.LANCZOS)
		im.save(g, "PNG")
		g.seek(0)
		self.surface = self.ddt.load_image(g)
		self.alive = True

	def prime(self) -> None:
		texture = sdl3.SDL_CreateTextureFromSurface(self.renderer, self.surface)
		sdl3.SDL_DestroySurface(self.surface)
		self.surface = None
		tex_w = c_float(0.0)
		tex_h = c_float(0.0)
		sdl3.SDL_GetTextureSize(texture, byref(tex_w), byref(tex_h))
		self.rect.w = int(tex_w.value)
		self.rect.h = int(tex_h.value)
		self.texture = texture

	def draw(self, x: int, y: int) -> bool | None:
		if len(self.items) > 30:
			img = self.items[0]
			img.destruct()
			self.items.remove(img)
		if not self.alive:
			if self not in self.queue:
				self.queue.append(self)
			return False
		if not self.texture:
			self.prime()
		self.rect.x = round(x)
		self.rect.y = round(y)
		sdl3.SDL_RenderTexture(self.renderer, self.texture, None, self.rect)

		return True


perf = Timer()


class TDraw:
	def __init__(self, renderer: sdl3.LP_SDL_Renderer) -> None:
		# All
		self.renderer = renderer
		self.scale = 1
		self.force_subpixel_text = False

		# Drawing
		self.sdlrect = sdl3.SDL_FRect(10.0, 10.0, 10.0, 10.0)

		# Text and Fonts
		self.source_rect = sdl3.SDL_FRect(0.0, 0.0, 0.0, 0.0)
		self.dest_rect = sdl3.SDL_FRect(0.0, 0.0, 0.0, 0.0)

		self.surf = None
		self.context = None
		self.layout = None

		self.text_background_colour = ColourRGBA(0, 0, 0, 255)
		self.pretty_rect: tuple[int, int, int, int] | None = None
		self.real_bg: bool = False
		self.alpha_bg: bool = False
		self.force_gray: bool = False
		self.f_dict: dict[float, tuple[str, int, float]] = {}
		self.ttc: dict[
			tuple[int, str, int, int, int, int, int, int, int, int],
			list[object],
		] = {}
		self.ttl: list[tuple[int, str, int, int, int, int, int, int, int, int]] = []

		self.was_truncated = False

	def _parse_font_string(self, font_str: str) -> tuple[str, int]:
		parts = font_str.rsplit(" ", 1)
		if len(parts) == 2:
			name, size = parts
			try:
				return name, max(1, int(float(size)))
			except Exception:
				return name, 12
		return font_str, 12

	def _load_font_obj(self, font: int) -> ImageFont.ImageFont:
		if font not in self.f_dict:
			logging.info(f"Font not loaded: {font!s}")
			return ImageFont.load_default()

		font_str = self.f_dict[font][0]
		font_name, font_size = self._parse_font_string(font_str)

		candidates = []

		if os.path.exists(font_name):
			candidates.append(font_name)

		family_lower = font_name.lower()
		if family_lower in {"monospace", "mono"}:
			candidates.extend([
				"DejaVuSansMono.ttf",
				"LiberationMono-Regular.ttf",
				"DroidSansMono.ttf",
			])
		else:
			candidates.extend([
				font_name,
				font_name + ".ttf",
				font_name + ".otf",
				"DejaVuSans.ttf",
				"LiberationSans-Regular.ttf",
				"DroidSans.ttf",
			])

		for candidate in candidates:
			try:
				return ImageFont.truetype(candidate, font_size)
			except Exception:
				continue

		return ImageFont.load_default()

	def _measure_text(self, text: str, font_obj: ImageFont.ImageFont) -> tuple[int, int]:
		img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
		draw = ImageDraw.Draw(img)
		if not text:
			bbox = draw.textbbox((0, 0), " ", font=font_obj)
		else:
			bbox = draw.multiline_textbbox((0, 0), text, font=font_obj, spacing=0)
		w = max(1, bbox[2] - bbox[0])
		h = max(1, bbox[3] - bbox[1])
		return w, h

	def _line_height(self, font_obj: ImageFont.ImageFont) -> int:
		img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
		draw = ImageDraw.Draw(img)
		bbox = draw.textbbox((0, 0), "Ag", font=font_obj)
		return max(1, bbox[3] - bbox[1] + 2)

	def _fit_text_ellipsis(self, text: str, font_obj: ImageFont.ImageFont, max_width: int) -> str:
		if not text:
			return text

		img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
		draw = ImageDraw.Draw(img)

		if draw.textlength(text, font=font_obj) <= max_width:
			return text

		ellipsis = "..."
		low = 0
		high = len(text)

		while low < high:
			mid = (low + high) // 2
			candidate = text[:mid].rstrip() + ellipsis
			if draw.textlength(candidate, font=font_obj) <= max_width:
				low = mid + 1
			else:
				high = mid

		return text[:max(0, low - 1)].rstrip() + ellipsis

	def _wrap_text_lines(
		self,
		text: str,
		font_obj: ImageFont.ImageFont,
		max_width: int,
		max_height: int | None = None,
		ellipsize: bool = True,
	) -> tuple[list[str], bool]:
		img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
		draw = ImageDraw.Draw(img)

		line_height = self._line_height(font_obj)
		max_lines = None
		if max_height is not None and line_height > 0:
			max_lines = max(1, max_height // line_height)

		paragraphs = text.splitlines() or [""]
		lines: list[str] = []
		truncated = False

		for paragraph in paragraphs:
			if paragraph == "":
				lines.append("")
				if max_lines is not None and len(lines) >= max_lines:
					if paragraph != paragraphs[-1]:
						truncated = True
					break
				continue

			words = paragraph.split(" ")
			current = ""

			for word in words:
				test = word if not current else current + " " + word
				if draw.textlength(test, font=font_obj) <= max_width:
					current = test
				else:
					if current:
						lines.append(current)
					else:
						lines.append(self._fit_text_ellipsis(word, font_obj, max_width))

					current = word if draw.textlength(word, font=font_obj) <= max_width else ""

					if max_lines is not None and len(lines) >= max_lines:
						truncated = True
						break

			if max_lines is not None and len(lines) >= max_lines:
				truncated = True
				break

			if current:
				lines.append(current)

			if max_lines is not None and len(lines) >= max_lines:
				if paragraph != paragraphs[-1]:
					truncated = True
				break

		if not lines:
			lines = [""]

		if max_lines is not None and len(lines) > max_lines:
			lines = lines[:max_lines]
			truncated = True

		if ellipsize and truncated and lines:
			lines[-1] = self._fit_text_ellipsis(lines[-1], font_obj, max_width)

		return lines, truncated

	def _render_text_image(
		self,
		text: str,
		font_obj: ImageFont.ImageFont,
		colour: ColourRGBA,
		bg: ColourRGBA,
		max_x: int,
		max_y: int | None = None,
		wrap: bool = False,
		alpha_bg: bool = False,
	) -> tuple[Image.Image, int, int, bool, int]:
		if wrap:
			lines, truncated = self._wrap_text_lines(text, font_obj, max_x, max_y, ellipsize=True)
		else:
			line = self._fit_text_ellipsis(text, font_obj, max_x)
			lines = [line]
			truncated = line != text

		line_height = self._line_height(font_obj)
		text_h = max(1, line_height * len(lines))
		text_w = 1
		for line in lines:
			w, _ = self._measure_text(line, font_obj)
			text_w = max(text_w, min(w, max_x))

		img = Image.new(
			"RGBA",
			(text_w, text_h + 4),
			(0, 0, 0, 0) if alpha_bg else (bg.r, bg.g, bg.b, 255),
		)
		draw = ImageDraw.Draw(img)

		y = 0
		for line in lines:
			draw.text((0, y), line, font=font_obj, fill=(colour.r, colour.g, colour.b, colour.a))
			y += line_height

		try:
			ascent, descent = font_obj.getmetrics()
			y_off = max(0, round(round(ascent) - 13 * self.scale))
		except Exception:
			y_off = 0

		return img, img.size[0], img.size[1], truncated, y_off

	def load_image(self, g: BytesIO) -> sdl3.LP_SDL_Surface:
		size = g.getbuffer().nbytes
		ptr = ctypes.c_void_p(ctypes.addressof(ctypes.c_char.from_buffer(g.getbuffer())))
		stream = sdl3.SDL_IOFromMem(ptr, c_size_t(size))
		return sdl3.IMG_Load_IO(stream, c_bool(True))

	def rect_s(self, rectangle: tuple[int, int, int, int], colour: ColourRGBA, thickness: int) -> None:
		sdl3.SDL_SetRenderDrawColor(self.renderer, colour.r, colour.g, colour.b, colour.a)
		x, y, w, h = (round(x) for x in rectangle)
		th = math.floor(thickness)
		self.sdlrect.x = x - th
		self.sdlrect.y = y - th
		self.sdlrect.w = th
		self.sdlrect.h = h + th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)  # left
		self.sdlrect.x = x - th
		self.sdlrect.y = y + h
		self.sdlrect.w = w + th
		self.sdlrect.h = th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)  # bottom
		self.sdlrect.x = x
		self.sdlrect.y = y - th
		self.sdlrect.w = w + th
		self.sdlrect.h = th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)  # top
		self.sdlrect.x = x + w
		self.sdlrect.y = y
		self.sdlrect.w = th
		self.sdlrect.h = h + th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)  # right

	def rect_si(self, rectangle: tuple[int, int, int, int], colour: ColourRGBA, thickness: int) -> None:
		sdl3.SDL_SetRenderDrawColor(self.renderer, colour.r, colour.g, colour.b, colour.a)
		x, y, w, h = (round(x) for x in rectangle)
		th = math.floor(thickness)
		self.sdlrect.x = x
		self.sdlrect.y = y
		self.sdlrect.w = th
		self.sdlrect.h = h
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)  # left
		self.sdlrect.x = x
		self.sdlrect.y = y + (h - th)
		self.sdlrect.w = w
		self.sdlrect.h = th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)  # bottom
		self.sdlrect.x = x
		self.sdlrect.y = y
		self.sdlrect.w = w
		self.sdlrect.h = th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)  # top
		self.sdlrect.x = x + (w - th)
		self.sdlrect.y = y
		self.sdlrect.w = th
		self.sdlrect.h = h
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)  # right

	def rect_a(self, location_xy: list[int], size_wh: list[int], colour: ColourRGBA) -> None:
		self.rect((location_xy[0], location_xy[1], size_wh[0], size_wh[1]), colour)

	def clear_rect(self, rectangle: tuple[int, int, int, int]) -> None:
		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_NONE)
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)

		self.sdlrect.x = float(rectangle[0])
		self.sdlrect.y = float(rectangle[1])
		self.sdlrect.w = float(rectangle[2])
		self.sdlrect.h = float(rectangle[3])

		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)
		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)

	def rect(self, rectangle: tuple[int, int, int, int], colour: ColourRGBA) -> None:
		sdl3.SDL_SetRenderDrawColor(self.renderer, colour.r, colour.g, colour.b, colour.a)

		self.sdlrect.x = float(rectangle[0])
		self.sdlrect.y = float(rectangle[1])
		self.sdlrect.w = float(rectangle[2])
		self.sdlrect.h = float(rectangle[3])

		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)

	def bordered_rect(
		self, rectangle: tuple[int, int, int, int], fill_colour: ColourRGBA, outer_colour: ColourRGBA, border_size: int
	) -> None:
		self.sdlrect.x = round(rectangle[0]) - border_size
		self.sdlrect.y = round(rectangle[1]) - border_size
		self.sdlrect.w = round(rectangle[2]) + border_size + border_size
		self.sdlrect.h = round(rectangle[3]) + border_size + border_size
		sdl3.SDL_SetRenderDrawColor(self.renderer, outer_colour.r, outer_colour.g, outer_colour.b, outer_colour.a)
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)
		self.sdlrect.x = round(rectangle[0])
		self.sdlrect.y = round(rectangle[1])
		self.sdlrect.w = round(rectangle[2])
		self.sdlrect.h = round(rectangle[3])
		sdl3.SDL_SetRenderDrawColor(self.renderer, fill_colour.r, fill_colour.g, fill_colour.b, fill_colour.a)
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)

	def line(self, x1: int, y1: int, x2: int, y2: int, colour: ColourRGBA) -> None:
		sdl3.SDL_SetRenderDrawColor(self.renderer, colour.r, colour.g, colour.b, colour.a)
		sdl3.SDL_RenderLine(self.renderer, round(x1), round(y1), round(x2), round(y2))

	def get_text_w(self, text: str, font: int, height: bool = False) -> int:
		x, y = self.get_text_wh(text, font, 3000)
		if height:
			return y
		return x

	def clear_text_cache(self) -> None:
		for key in self.ttl:
			so = self.ttc[key]
			sdl3.SDL_DestroyTexture(so[1])

		self.ttc.clear()
		self.ttl.clear()

	def prime_font(self, name: str, size: float, user_handle: float, offset: int = 0) -> None:
		self.f_dict[user_handle] = (name + " " + str(size * self.scale), offset, size * self.scale)

	def get_text_wh(self, text: str, font: int, max_x: int, wrap: bool = False) -> tuple[int, int] | None:
		font_obj = self._load_font_obj(font)

		if wrap:
			lines, _ = self._wrap_text_lines(text, font_obj, max_x)
			line_height = self._line_height(font_obj)
			width = 1
			for line in lines:
				w, _ = self._measure_text(line, font_obj)
				width = max(width, min(w, max_x))
			return width, max(1, line_height * len(lines))

		line = self._fit_text_ellipsis(text, font_obj, max_x)
		w, h = self._measure_text(line, font_obj)
		return min(w, max_x), h

	def get_y_offset(self, text: str, font: int, max_x: int, wrap: bool = False) -> int:
		"""HACKY"""
		font_obj = self._load_font_obj(font)
		try:
			ascent, descent = font_obj.getmetrics()
			y_off = round(round(ascent) - 13 * self.scale)
		except Exception:
			y_off = 0

		return y_off

	def __render_text(self, key: dict, x: int, y: int, range_top: int, range_height: int, align: int) -> None:
		sd = key

		if sd[3]:
			self.was_truncated = True

		if align == 1:
			sd[0].x = round(x) - sd[0].w

		elif align == 2:
			sd[0].x -= int(sd[0].w / 2)

		if range_height is not None and range_height < sd[0].h:
			if range_top < 0:
				range_top = 0

			if range_top > sd[0].h - range_height:
				range_top = sd[0].h - range_height

			self.source_rect.y = round(range_top)
			self.source_rect.w = sd[0].w
			self.source_rect.h = round(range_height)

			self.dest_rect.x = sd[0].x
			self.dest_rect.y = sd[0].y
			self.dest_rect.w = sd[0].w
			self.dest_rect.h = round(range_height)

			sdl3.SDL_RenderTexture(self.renderer, sd[1], self.source_rect, self.dest_rect)
			return

		sdl3.SDL_RenderTexture(self.renderer, sd[1], None, sd[0])

	def __draw_text_cairo(
		self,
		location: list[int],
		text: str,
		colour: ColourRGBA,
		font: int,
		max_x: int,
		bg: ColourRGBA,
		align: int = 0,
		max_y: int | None = None,
		wrap: bool = False,
		range_top: int = 0,
		range_height: int | None = None,
		real_bg: bool = False,
		key: tuple[int, str, int, int, int, int, int, int, int, int] | None = None,
	) -> int:
		force_cache = False
		if key:
			force_cache = True

		self.was_truncated = False

		max_x += 12  # Hack
		max_x = round(max_x)

		alpha_bg = self.alpha_bg

		if bg.a < 200:
			alpha_bg = True

		x = round(location[0])
		y = round(location[1])

		if self.pretty_rect:
			w, h = self.get_text_wh(text, font, max_x, wrap)
			quick_box = [x, y, w, h]

			if align == 1:
				quick_box[0] = x - quick_box[2]

			elif align == 2:
				quick_box[0] -= int(quick_box[2] / 2)

			if coll_rect(self.pretty_rect, quick_box):
				alpha_bg = True
			else:
				alpha_bg = False

		if alpha_bg:
			bg = ColourRGBA(0, 0, 0, 0)

		if max_y is not None:
			max_y = round(max_y)

		if len(text) == 0:
			return 0

		if key is None:
			key = (max_x, text, font, colour.r, colour.g, colour.b, colour.a, bg.r, bg.g, bg.b)

		if not real_bg or force_cache:
			sd = self.ttc.get(key)
			if sd:
				sd = self.ttc[key]
				sd[0].x = round(x)
				sd[0].y = round(y) - sd[2]

				self.__render_text(sd, x, y, range_top, range_height, align)
				self.ttl.remove(key)
				self.ttl.append(key)

				if wrap:
					return sd[0].h
				return sd[0].w

		font_obj = self._load_font_obj(font)

		img, w, h, truncated, y_off = self._render_text_image(
			text=text,
			font_obj=font_obj,
			colour=colour,
			bg=bg,
			max_x=max_x,
			max_y=max_y,
			wrap=wrap,
			alpha_bg=True,
		)

		self.was_truncated = truncated

		raw = img.tobytes()
		buffer = ctypes.create_string_buffer(raw, len(raw))
		ptr = ctypes.cast(buffer, ctypes.c_void_p)

		surface = sdl3.SDL_CreateSurfaceFrom(
			w,
			h,
			sdl3.SDL_PIXELFORMAT_RGBA8888,
			ptr,
			w * 4,
		)

		if not surface:
			logging.error("Failed to create SDL surface for text")
			return 0

		c = sdl3.SDL_CreateTextureFromSurface(self.renderer, surface)
		sdl3.SDL_DestroySurface(surface)

		if not c:
			logging.error("Failed to create SDL texture for text")
			return 0

		blend_mode = sdl3.SDL_ComposeCustomBlendMode(
			sdl3.SDL_BLENDFACTOR_ONE,
			sdl3.SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA,
			sdl3.SDL_BLENDOPERATION_ADD,
			sdl3.SDL_BLENDFACTOR_ONE,
			sdl3.SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA,
			sdl3.SDL_BLENDOPERATION_ADD,
		)
		sdl3.SDL_SetTextureBlendMode(c, blend_mode)

		dst = sdl3.SDL_FRect(round(x), round(y))
		dst.w = round(w)
		dst.h = round(h)
		dst.y = round(y) - y_off

		pack = [dst, c, y_off, self.was_truncated, buffer]

		self.__render_text(pack, x, y, range_top, range_height, align)

		if not real_bg or force_cache:
			self.ttc[key] = pack
			self.ttl.append(key)
			if len(self.ttl) > 350:
				old_key = self.ttl[0]
				so = self.ttc[old_key]
				sdl3.SDL_DestroyTexture(so[1])
				del self.ttc[old_key]
				del self.ttl[0]

		if wrap:
			return dst.h
		return dst.w

	def text(
		self,
		location: list[int],
		text: str,
		colour: ColourRGBA,
		font: int,
		max_w: int = 4000,
		bg: ColourRGBA | None = None,
		range_top: int = 0,
		range_height: int | None = None,
		real_bg: bool = False,
		key: tuple[int, str, int, int, int, int, int, int, int, int] | None = None,
	) -> int | None:
		if not text:
			return 0

		max_w = max(1, max_w)

		if bg is None:
			bg = self.text_background_colour

		if colour.a != 255:
			colour = alpha_blend(colour, bg)
		align = 0
		if len(location) > 2:
			if location[2] == 1:
				align = 1
			if location[2] == 2:
				align = 2
			if location[2] == 4:
				max_h = None
				if len(location) > 4:
					max_h = location[4]

				return self.__draw_text_cairo(
					location,
					text,
					colour,
					font,
					location[3],
					bg,
					max_y=max_h,
					wrap=True,
					range_top=range_top,
					range_height=range_height,
				)

		return self.__draw_text_cairo(location, text, colour, font, max_w, bg, align, real_bg=real_bg, key=key)
