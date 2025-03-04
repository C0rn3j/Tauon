#!/usr/bin/env python
import sdl3
import io
from PIL import Image
import ctypes

width = 100
height = 100

f = "../assets/artist.png"
g = io.BytesIO()
g.seek(0)
im = Image.open(f)
im.thumbnail((width, height), Image.Resampling.LANCZOS)
im.save(g, "PNG")
g.seek(0)

size = g.getbuffer().nbytes

pointer = ctypes.c_void_p(ctypes.addressof(ctypes.c_char.from_buffer(g.getbuffer())))

stream = sdl3.SDL_IOFromMem(pointer, size)

print("Testing nameless params...")
print(sdl3.IMG_Load_IO(stream, True))
print("Testing named params...")
print(sdl3.IMG_Load_IO(src=stream, closeio=True))
