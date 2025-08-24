"""Tauon Music Box

Preamble

Welcome to the Tauon Music Box source code.
I started this project when I was first learning python, as a result this code can be quite messy.
No doubt I have written some things terribly wrong or inefficiently in places.
I would highly recommend not using this project as an example on how to code cleanly or correctly.
"""

# Copyright © 2015-2025, Taiko2k captain(dot)gxj(at)gmail.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from __future__ import annotations

import base64
import builtins
import colorsys
import copy
import ctypes
import ctypes.util
import datetime
import gc as gbc
import gettext
import glob
import hashlib
import importlib
import io
import json
import locale as py_locale
import logging

#import magic
import math

#import mimetypes
import os
import pickle
import platform
import random
import re
import secrets
import shlex
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time

#import type_enforced
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
import zipfile
from collections import OrderedDict
from ctypes import Structure, byref, c_char_p, c_double, c_float, c_int, c_ubyte, c_uint32, c_void_p, pointer
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import certifi
import musicbrainzngs
import mutagen
import mutagen.flac
import mutagen.id3
import mutagen.mp4
import mutagen.oggvorbis
import requests
import sdl3
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from send2trash import send2trash
from unidecode import unidecode

builtins._ = lambda x: x

from tauon.t_modules.guitar_chords import GuitarChords  # noqa: E402
from tauon.t_modules.t_config import Config  # noqa: E402
from tauon.t_modules.t_db_migrate import database_migrate  # noqa: E402
from tauon.t_modules.t_dbus import Gnome  # noqa: E402
from tauon.t_modules.t_draw import QuickThumbnail, TDraw  # noqa: E402
from tauon.t_modules.t_enums import LoaderCommand, PlayerState, PlayingState, StopMode  # noqa: E402
from tauon.t_modules.t_extra import (  # noqa: E402
	ColourGenCache,
	ColourRGBA,
	FunctionStore,
	RadioPlaylist,
	RadioStation,
	StarRecord,
	TauonPlaylist,
	TauonQueueItem,
	TestTimer,
	Timer,
	alpha_blend,
	alpha_mod,
	archive_file_scan,
	check_equal,
	clean_string,
	colour_slide,
	colour_value,
	commonprefix,
	contrast_ratio,
	d_date_display,
	d_date_display2,
	filename_safe,
	filename_to_metadata,
	fit_box,
	folder_file_scan,
	genre_correct,
	get_artist_safe,
	get_artist_strip_feat,
	get_display_time,
	get_filesize_string,
	get_filesize_string_rounded,
	get_folder_size,
	get_hms_time,
	get_split_artists,
	get_year_from_string,
	grow_rect,
	hls_to_rgb,
	hms_to_seconds,
	hsl_to_rgb,
	is_grey,
	is_light,
	j_chars,
	mac_styles,
	point_distance,
	point_proximity_test,
	process_odat,
	reduce_paths,
	rgb_add_hls,
	rgb_to_hls,
	search_magic,
	search_magic_any,
	seconds_to_day_hms,
	shooter,
	sleep_timeout,
	star_count,
	star_count3,
	subtract_rect,
	test_lumi,
	tmp_cache_dir,
	tryint,
	uri_parse,
	year_search,
)
from tauon.t_modules.t_jellyfin import Jellyfin  # noqa: E402
from tauon.t_modules.t_launch import Launch  # noqa: E402
from tauon.t_modules.t_lyrics import genius, lyric_sources, uses_scraping  # noqa: E402
from tauon.t_modules.t_phazor import Cachement, LibreSpot, get_phazor_path, phazor_exists, player4  # noqa: E402
from tauon.t_modules.t_prefs import Prefs  # noqa: E402
from tauon.t_modules.t_search import bandcamp_search  # noqa: E402
from tauon.t_modules.t_spot import SpotCtl  # noqa: E402
from tauon.t_modules.t_stream import StreamEnc  # noqa: E402
from tauon.t_modules.t_tagscan import Ape, Flac, M4a, Opus, Wav, parse_picture_block  # noqa: E402
from tauon.t_modules.t_themeload import Deco, load_theme  # noqa: E402
from tauon.t_modules.t_tidal import Tidal  # noqa: E402
from tauon.t_modules.t_webserve import (  # noqa: E402
	VorbisMonitor,
	authserve,
	controller,
	stream_proxy,
	webserve,
	webserve2,
)

# Detect platform
macos = False
msys = False
system = "Linux"
arch = platform.machine()
platform_release = platform.release()
platform_system = platform.system()
win_ver = 0
if platform_system == "Windows":
	try:
		win_ver = int(platform_release)
	except Exception:
		logging.exception("Failed getting Windows version from platform.release()")

if sys.platform == "win32":
	# system = 'Windows'
	system = "Linux"
	msys = True
	if msys:
		import gi
		from gi.repository import GLib
	else:
		import atexit

		import comtypes
		import win32api
		import win32con
		import win32gui
		import win32ui
else:
	system = "Linux"
	import fcntl

if sys.platform == "darwin":
	macos = True

if system == "Linux" and not macos and not msys:
	from tauon.t_modules.t_dbus import Gnome

if system == "Windows" or msys:
	from lynxtray import SysTrayIcon

CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
class Tauon:
	"""Root class for everything Tauon"""

	def __init__(self, holder: Holder, bag: Bag, gui: GuiVar) -> None:
		self.use_cc                       = is_module_loaded("opencc")
		self.use_natsort                  = is_module_loaded("natsort")

		self.bag                          = bag
		self.mpt                          = bag.mpt
		self.gme                          = bag.gme
		self.renderer                     = bag.renderer
		self.ddt                          = TDraw(bag.renderer)
		self.fonts                        = bag.fonts
		self.formats                      = bag.formats
		self.macos                        = bag.macos
		self.mac_close                    = bag.mac_close
		self.mac_maximize                 = bag.mac_maximize
		self.mac_minimize                 = bag.mac_minimize
		self.system                       = bag.system
		self.platform_system              = bag.platform_system
		self.primary_stations             = bag.primary_stations
		self.wayland                      = bag.wayland
		self.msys                         = bag.msys
		self.dirs                         = bag.dirs
		self.colours                      = bag.colours
		self.download_directories         = bag.download_directories
		self.launch_prefix                = bag.launch_prefix
		self.overlay_texture_texture      = bag.overlay_texture_texture
		self.de_notify_support            = bag.de_notify_support
		self.old_window_position          = bag.old_window_position
		self.cache_directory              = bag.dirs.cache_directory
		self.config_directory             = bag.dirs.config_directory
		self.user_directory               = bag.dirs.user_directory
		self.install_directory            = bag.dirs.install_directory
		self.music_directory              = bag.dirs.music_directory
		self.locale_directory             = bag.dirs.locale_directory
		self.n_cache_directory            = bag.dirs.n_cache_directory
		self.e_cache_directory            = bag.dirs.e_cache_directory
		self.g_cache_directory            = bag.dirs.g_cache_directory
		self.a_cache_directory            = bag.dirs.a_cache_directory
		self.r_cache_directory            = bag.dirs.r_cache_directory
		self.b_cache_directory            = bag.dirs.b_cache_directory
		self.draw_max_button              = bag.draw_max_button
		self.draw_min_button              = bag.draw_min_button
		self.song_notification            = bag.song_notification
		self.tls_context                  = bag.tls_context
		self.folder_image_offsets         = bag.folder_image_offsets
		self.inp                          = gui.inp
		self.n_version                    = holder.n_version
		self.t_window                     = holder.t_window
		self.t_title                      = holder.t_title
		self.t_version                    = holder.t_version
		self.t_agent                      = holder.t_agent
		self.t_id                         = holder.t_id
		self.fs_mode                      = holder.fs_mode
		self.window_default_size          = holder.window_default_size
		self.window_title                 = holder.window_title
		self.logical_size                 = bag.logical_size
		self.window_size                  = bag.window_size
		self.draw_border                  = holder.draw_border
		self.desktop                      = bag.desktop
		self.pid                          = os.getpid()
		# List of encodings to check for with the fix mojibake function
		self.encodings                    = ["cp932", "utf-8", "big5hkscs", "gbk"]  # These seem to be the most common for Japanese
		self.column_names = (
			"Artist",
			"Album Artist",
			"Album",
			"Title",
			"Composer",
			"Time",
			"Date",
			"Genre",
			"#",
			"P",
			"Starline",
			"Rating",
			"Comment",
			"Codec",
			"Lyrics",
			"Bitrate",
			"S",
			"Filename",
			"Disc",
			"CUE",
			"ID"
		)
		self.device                       = socket.gethostname()
		self.search_string_cache:     dict[int, str] = {}
		self.search_dia_string_cache: dict[int, str] = {}
		self.albums:            list[int] = []
		self.added:             list[int] = []
		self.album_dex:         list[int] = []
		self.to_scan:           list[int] = []
		self.after_scan: list[TrackClass] = []
		self.quick_import_done: list[str] = []
		self.move_jobs: list[tuple[str, str, bool, str, LoadClass]] = []
		self.move_in_progress:       bool = False
		self.worker2_lock                 = threading.Lock()
		self.dummy_event:          sdl3.SDL_Event = sdl3.SDL_Event()
		self.temp_dest                            = sdl3.SDL_FRect(0, 0)
		self.text_box_canvas_rect      = sdl3.SDL_FRect(0, 0, round(2000 * gui.scale), round(40 * gui.scale))
		self.text_box_canvas_hide_rect = sdl3.SDL_FRect(0, 0, round(2000 * gui.scale), round(40 * gui.scale))
		self.text_box_canvas           = sdl3.SDL_CreateTexture(
			self.renderer, sdl3.SDL_PIXELFORMAT_ARGB8888,
			sdl3.SDL_TEXTUREACCESS_TARGET, round(self.text_box_canvas_rect.w), round(self.text_box_canvas_rect.h))
		self.translate                            = _
		self.strings                              = Strings()
		self.gui                                  = gui
		self.prefs                                = bag.prefs
		self.snap_mode                            = bag.snap_mode
		self.flatpak_mode                         = bag.flatpak_mode
		self.core_use: int                        = 0
		self.dl_use: int                          = 0
		self.latest_db_version                    = bag.latest_db_version
		self.g_tc_notify                          = None
		# Setting various timers
		self.spot_search_rate_timer       = Timer()
		self.track_box_path_tool_timer    = Timer()
		self.message_box_min_timer        = Timer()
		self.cursor_blink_timer           = Timer()
		self.animate_monitor_timer        = Timer()
		self.min_render_timer             = Timer()
		self.vis_rate_timer               = Timer()
		self.vis_decay_timer              = Timer()
		self.scroll_timer                 = Timer()
		self.scroll_timer.set()
		self.perf_timer                   = Timer() # Reassigned later
		self.quick_d_timer                = Timer()
		self.core_timer                   = Timer() # Reassigned later
		self.sleep_timer                  = Timer()
		self.gallery_select_animate_timer = Timer()
		self.gallery_select_animate_timer.force_set(10)
		self.search_clear_timer           = Timer()
		self.gall_pl_switch_timer         = Timer()
		self.gall_pl_switch_timer.force_set(999)
		self.d_click_timer                = Timer()
		self.d_click_timer.force_set(10)
		self.lyrics_check_timer           = Timer()
		self.scroll_hide_timer            = Timer(100)
		self.scroll_gallery_hide_timer    = Timer(100)
		self.get_lfm_wait_timer           = Timer(10)
		self.lyrics_fetch_timer           = Timer(10)
		self.gallery_load_delay           = Timer(10)
		self.queue_add_timer              = Timer(100)
		self.toast_love_timer             = Timer(100)
		self.toast_mode_timer             = Timer(100)
		self.scrobble_warning_timer       = Timer(1000)
		self.sync_file_timer              = Timer(1000)
		self.sync_file_update_timer       = Timer(1000)
		self.restore_ignore_timer         = Timer()
		self.restore_ignore_timer.force_set(100)
		self.fields = Fields(self)
		# Create top menu
		self.x_menu                = Menu(self, 190, show_icons=True)
		self.set_menu              = Menu(self, 150)
		self.field_menu            = Menu(self, 140)
		self.dl_menu               = Menu(self, 90)

		self.cancel_menu           = Menu(self, 100)
		self.extra_menu            = Menu(self, 175, show_icons=True)
		self.stop_menu             = Menu(self, 175, show_icons=False)
		self.shuffle_menu          = Menu(self, 120)
		self.repeat_menu           = Menu(self, 120)
		self.tab_menu              = Menu(self, 160, show_icons=True)
		self.playlist_menu         = Menu(self, 130)
		self.showcase_menu         = Menu(self, 135)
		self.spotify_playlist_menu = Menu(self, 175)
		self.queue_menu            = Menu(self, 150)
		self.radio_entry_menu      = Menu(self, 125)
		self.center_info_menu      = Menu(self, 125)
		self.gallery_menu          = Menu(self, 175, show_icons=True)
		self.artist_info_menu      = Menu(self, 135)
		self.artist_list_menu      = Menu(self, 165, show_icons=True)
		self.lightning_menu        = Menu(self, 165)
		self.lsp_menu              = Menu(self, 145)
		self.folder_tree_menu      = Menu(self, 175, show_icons=True)
		self.folder_tree_stem_menu = Menu(self, 190, show_icons=True)
		self.overflow_menu         = Menu(self, 175)
		self.radio_context_menu    = Menu(self, 175)
		self.radio_tab_menu        = Menu(self, 160, show_icons=True)
		self.mode_menu             = Menu(self, 175)
		self.track_menu            = Menu(self, 195, show_icons=True)
		self.picture_menu          = Menu(self, 175)
		self.selection_menu        = Menu(self, 200, show_icons=False)
		self.folder_menu           = Menu(self, 193, show_icons=True)
		self.extra_tab_menu        = Menu(self, 155, show_icons=True)


		self.smooth_scroll                        = SmoothScroll(tauon=self)
		self.lb                                   = ListenBrainz(tauon=self)
		self.thread_manager                       = ThreadManager(tauon=self)
		self.album_mode_art_size                  = bag.album_mode_art_size
		self.artist_picture_render                = PictureRender(tauon=self)
		self.artist_preview_render                = PictureRender(tauon=self)
		self.input_sdl                            = GetSDLInput(tauon=self)
		self.pctl                                 = PlayerCtl(tauon=self)
		self.mini_lyrics_scroll                   = self.pctl.mini_lyrics_scroll
		self.playlist_panel_scroll                = self.pctl.playlist_panel_scroll
		self.artist_info_scroll                   = self.pctl.artist_info_scroll
		self.device_scroll                        = self.pctl.device_scroll
		self.artist_list_scroll                   = self.pctl.artist_list_scroll
		self.gallery_scroll                       = self.pctl.gallery_scroll
		self.tree_view_scroll                     = self.pctl.tree_view_scroll
		self.radio_view_scroll                    = self.pctl.radio_view_scroll
		self.artist_info_box                      = self.pctl.artist_info_box
		self.draw                                 = self.pctl.draw
		self.radiobox                             = self.pctl.radiobox
		self.dummy_track                          = self.radiobox.dummy_track
		self.queue_box                            = self.pctl.queue_box
		self.tree_view_box                        = self.pctl.tree_view_box
		self.star_store                           = self.pctl.star_store
		self.lastfm                               = self.pctl.lastfm
		self.lfm_scrobbler                        = self.pctl.lfm_scrobbler
		self.artist_list_box                      = self.pctl.artist_list_box
		self.guitar_chords                        = GuitarChords(tauon=self, mouse_wheel=self.inp.mouse_wheel, mouse_position=self.inp.mouse_position, window_size=self.window_size)
		self.search_over                          = SearchOverlay(tauon=self)
		self.stats_gen                            = GStats(tauon=self)
		self.deco                                 = Deco(tauon=self)
		self.bottom_bar1                          = BottomBarType1(tauon=self)
		self.bottom_bar_ao1                       = BottomBarType_ao1(tauon=self)
		self.top_panel                            = TopPanel(tauon=self)
		self.playlist_box                         = PlaylistBox(tauon=self)
		self.radio_view                           = RadioView(tauon=self)
		self.view_box                             = ViewBox(tauon=self)
		self.pref_box                             = Over(tauon=self)
		self.fader                                = Fader(tauon=self)
		self.style_overlay                        = StyleOverlay(tauon=self)
		self.album_art_gen                        = self.style_overlay.album_art_gen
		self.tool_tip                             = ToolTip(tauon=self)
		self.tool_tip2                            = ToolTip(tauon=self)
		self.columns_tool_tip                     = ToolTip3(tauon=self)
		self.f_store                              = FunctionStore()
		self.tool_tip2.trigger                    = 1.8
		self.undo                                 = Undo(tauon=self)
		self.timed_lyrics_ren                     = TimedLyricsRen(tauon=self)
		self.rename_files                         = TextBox2(tauon=self)
		self.rename_track_box                     = RenameTrackBox(tauon=self)
		self.edit_artist                          = TextBox2(tauon=self)
		self.edit_album                           = TextBox2(tauon=self)
		self.edit_title                           = TextBox2(tauon=self)
		self.edit_album_artist                    = TextBox2(tauon=self)
		self.trans_edit_box                       = TransEditBox(tauon=self)
		self.sub_lyrics_a                         = TextBox2(tauon=self)
		self.sub_lyrics_b                         = TextBox2(tauon=self)
		self.sub_lyrics_box                       = SubLyricsBox(tauon=self)
		self.export_playlist_box                  = ExportPlaylistBox(tauon=self)
		self.rename_text_area                     = TextBox(tauon=self)
		self.rename_playlist_box                  = RenamePlaylistBox(tauon=self)
		self.message_box                          = MessageBox(tauon=self)
		self.search_text                          = self.search_over.search_text
		self.sync_target                          = TextBox2(tauon=self)
		self.playlist_folder_box                  = TextBox2(tauon=self)
		self.edge_playlist2                       = EdgePulse2(tauon=self)
		self.lyric_side_top_pulse                 = EdgePulse2(tauon=self)
		self.lyric_side_bottom_pulse              = EdgePulse2(tauon=self)
		self.tab_pulse                            = EdgePulse(tauon=self)
		self.radio_thumb_gen                      = RadioThumbGen(tauon=self)
		self.dl_mon                               = DLMon(tauon=self)
		self.drop_shadow                          = DropShadow(tauon=self)
		self.lyrics_ren_mini                      = LyricsRenMini(tauon=self)
		self.lyrics_ren                           = LyricsRen(tauon=self)
		self.synced_to_static_lyrics              = TimedLyricsToStatic()
		self.mini_mode                            = MiniMode(tauon=self)
		self.mini_mode2                           = MiniMode2(tauon=self)
		self.mini_mode3                           = MiniMode3(tauon=self)
		self.vb                                   = VorbisMonitor(tauon=self)

		if self.system == "Linux" and not self.macos and not self.msys:
			self.gnome = Gnome(tauon=self)

		self.text_plex_usr     = TextBox2(tauon=self)
		self.text_plex_pas     = TextBox2(tauon=self)
		self.text_plex_ser     = TextBox2(tauon=self)

		self.text_jelly_usr    = TextBox2(tauon=self)
		self.text_jelly_pas    = TextBox2(tauon=self)
		self.text_jelly_ser    = TextBox2(tauon=self)

		self.text_koel_usr     = TextBox2(tauon=self)
		self.text_koel_pas     = TextBox2(tauon=self)
		self.text_koel_ser     = TextBox2(tauon=self)

		self.text_air_usr      = TextBox2(tauon=self)
		self.text_air_pas      = TextBox2(tauon=self)
		self.text_air_ser      = TextBox2(tauon=self)

		self.text_spot_client       = TextBox2(tauon=self)
		self.text_spot_secret       = TextBox2(tauon=self)
		#self.text_spot_username     = TextBox2(tauon=self)
		#self.text_spot_password     = TextBox2(tauon=self)

		self.text_maloja_url   = TextBox2(tauon=self)
		self.text_maloja_key   = TextBox2(tauon=self)

		self.text_sat_url      = TextBox2(tauon=self)
		self.text_sat_playlist = TextBox2(tauon=self)

		self.rename_folder     = TextBox2(tauon=self)
		self.transcode_list:      list[list[int]] = []
		self.transcode_state:                 str = ""
		self.loaderCommand:                   int = LoaderCommand.NONE
		self.loaderCommandReady:             bool = False
		self.cm_clean_db:                    bool = False
		self.worker_save_state:              bool = False
		self.whicher                              = whicher
		self.load_orders:         list[LoadClass] = []
		self.switch_playlist                      = None
		self.album_info_cache: dict[int, tuple[bool, list[int], bool]] = {}
		self.album_info_cache_key                 = (-1, -1)
		self.console                              = bag.console
		self.TrackClass                           = TrackClass
		self.quickthumbnail                       = QuickThumbnail(tauon=self)
		self.gall_ren                             = GallClass(tauon=self, size=self.album_mode_art_size)
		self.thumb_tracks                         = ThumbTracks(tauon=self)
		self.chunker                              = Chunker()
		self.stream_proxy                         = StreamEnc(self)
		self.level_train:       list[list[float]] = []
		self.radio_server: ThreadedHTTPServer | None = None
		self.listen_alongers:    dict[str, Timer] = {}
		self.encode_folder_name                   = encode_folder_name
		self.encode_track_name                    = encode_track_name
		self.todo:               list[TrackClass] = []
		self.heart_colours                        = ColourGenCache(0.7, 0.7)
		#self.power_tag_colours                    = ColourGenCache(0.5, 0.8)

		self.tray_lock = threading.Lock()
		self.tray_releases = 0

		self.play_lock = None
		self.update_play_lock: Callable[[], None] | None = None
		self.sleep_lock = None
		self.shutdown_lock = None
		self.quick_close: bool = False
		self.pl_to_id = self.pctl.pl_to_id
		self.id_to_pl = self.pctl.id_to_pl

		self.copied_track = None
		self.aud:                        CDLL = ctypes.cdll.LoadLibrary(str(get_phazor_path(self.pctl)))
		logging.debug(f"Loaded Phazor path at: {get_phazor_path(self.pctl)}")
		self.player4_state:       PlayerState = PlayerState.STOPPED
		self.librespot_p: Popen[bytes] | None = None
		self.spot_ctl                         = SpotCtl(self)
		self.cachement                        = Cachement(self)
		self.spotc                            = LibreSpot(self)

		#self.recorded_songs = []

		self.chrome_mode: bool = False
		self.web_running: bool = False
		self.web_thread = None
		self.remote_limited: bool = True
		self.enable_librespot = shutil.which("librespot")

		self.MenuItem = MenuItem

		self.chrome: Chrome | None = None
		self.chrome_menu: Menu | None = None

		self.tidal             = Tidal(self)
		self.plex              = PlexService(self)
		self.jellyfin          = Jellyfin(self)
		self.koel              = KoelService(self)
		self.tau               = TauService(self)
		self.album_star_store  = AlbumStarStore(self)
		self.subsonic          = self.album_star_store.subsonic

		self.playlist_autoscan = False
		self.dropped_playlist = -1


def main(holder: Holder) -> None:
	t_window               = holder.t_window
	renderer               = holder.renderer
	logical_size           = holder.logical_size
	window_size            = holder.window_size
	maximized              = holder.maximized
	scale                  = holder.scale
	window_opacity         = holder.window_opacity
	draw_border            = holder.draw_border
	transfer_args_and_exit = holder.transfer_args_and_exit
	old_window_position    = holder.old_window_position
	install_directory      = holder.install_directory
	user_directory         = holder.user_directory
	pyinstaller_mode       = holder.pyinstaller_mode
	phone                  = holder.phone
	window_default_size    = holder.window_default_size
	window_title           = holder.window_title
	fs_mode                = holder.fs_mode
	t_title                = holder.t_title
	n_version              = holder.n_version
	t_version              = holder.t_version
	t_id                   = holder.t_id
	t_agent                = holder.t_agent
	dev_mode               = holder.dev_mode
	instance_lock          = holder.instance_lock
	log                    = holder.log
	logging.info(f"Window size: {window_size}; Logical size: {logical_size}")

	tls_context = setup_tls(holder)
	last_fm_enable = is_module_loaded("pylast")
	if last_fm_enable:
		# pyLast needs to be reimported AFTER setup_tls(), else pyinstaller breaks
		importlib.reload(pylast)

	discord_allow = is_module_loaded("lynxpresence", "ActivityType")
	#ctypes = sys.modules.get("ctypes")  # Fetch from loaded modules

	if sys.platform == "win32" and msys:
		font_folder = str(install_directory / "fonts")
		if os.path.isdir(font_folder):
			logging.info(f"Fonts directory:           {font_folder}")

			fc = ctypes.cdll.LoadLibrary("libfontconfig-1.dll")
			fc.FcConfigReference.restype = ctypes.c_void_p
			fc.FcConfigReference.argtypes = (ctypes.c_void_p,)
			fc.FcConfigAppFontAddDir.argtypes = (ctypes.c_void_p, ctypes.c_char_p)
			config = ctypes.c_void_p()
			config.contents = fc.FcConfigGetCurrent()
			fc.FcConfigAppFontAddDir(config.value, font_folder.encode())

	# Detect what desktop environment we are in to enable specific features
	desktop = os.environ.get("XDG_CURRENT_DESKTOP")
	# de_notify_support = desktop == 'GNOME' or desktop == 'KDE'
	de_notify_support = False
	draw_min_button = True
	draw_max_button = True
	left_window_control = False

	detect_macstyle = False
	gtk_settings: Gtk.Settings | None = None
	mac_close = ColourRGBA(253, 70, 70, 255)
	mac_maximize = ColourRGBA(254, 176, 36, 255)
	mac_minimize = ColourRGBA(42, 189, 49, 255)
	try:
		# TODO(Martin): Bump to 4.0 - https://github.com/Taiko2k/Tauon/issues/1316
		gi.require_version("Gtk", "3.0")
		from gi.repository import Gtk

		gtk_settings = Gtk.Settings().get_default()
		if "minimize" not in str(gtk_settings.get_property("gtk-decoration-layout")):
			draw_min_button = False
		if "maximize" not in str(gtk_settings.get_property("gtk-decoration-layout")):
			draw_max_button = False
		if "close" in str(gtk_settings.get_property("gtk-decoration-layout")).split(":")[0]:
			left_window_control = True
		gtk_theme = str(gtk_settings.get_property("gtk-theme-name")).lower()
		#logging.info(f"GTK theme is: {gtk_theme}")
		for k, v in mac_styles.items():
			if k in gtk_theme:
				detect_macstyle = True
				if v is not None:
					mac_close = v[0]
					mac_maximize = v[1]
					mac_minimize = v[2]

	except Exception:
		logging.exception("Error accessing GTK settings")

	# Set data folders (portable mode)
	config_directory = user_directory
	cache_directory = user_directory / "cache"
	home_directory = os.path.join(os.path.expanduser("~"))

	asset_directory = install_directory / "assets"
	svg_directory = install_directory / "assets" / "svg"
	scaled_asset_directory = asset_directory

	music_directory = Path("~").expanduser() / "Music"
	if not music_directory.is_dir():
		music_directory = Path("~").expanduser() / "music"

	download_directory = Path("~").expanduser() / "Downloads"

	# Detect if we are installed or running portable
	install_mode = False
	flatpak_mode = False
	snap_mode = False
	if str(install_directory).startswith(("/opt/", "/usr/", "/app/", "/snap/", "/nix/store/")):
		install_mode = True
		if str(install_directory)[:6] == "/snap/":
			snap_mode = True
		if str(install_directory)[:5] == "/app/":
			# Flatpak mode
			logging.info("Detected running as Flatpak")

			# [old / no longer used] Symlink fontconfig from host system as workaround for poor font rendering
			if os.path.exists(os.path.join(home_directory, ".var/app/com.github.taiko2k.tauonmb/config")):

				host_fcfg = os.path.join(home_directory, ".config/fontconfig/")
				flatpak_fcfg = os.path.join(home_directory, ".var/app/com.github.taiko2k.tauonmb/config/fontconfig")

				if os.path.exists(host_fcfg):

					# if os.path.isdir(flatpak_fcfg) and not os.path.islink(flatpak_fcfg):
					#	 shutil.rmtree(flatpak_fcfg)
					if os.path.islink(flatpak_fcfg):
						logging.info("-- Symlink to fonconfig exists, removing")
						os.unlink(flatpak_fcfg)
					# else:
					#	 logging.info("-- Symlinking user fonconfig")
					#	 #os.symlink(host_fcfg, flatpak_fcfg)

			flatpak_mode = True

	logging.info(f"Platform: {sys.platform}")

	if pyinstaller_mode:
		logging.info("Pyinstaller mode")

	# If we're installed, use home data locations
	if (install_mode and system == "Linux") or macos or msys:
		cache_directory  = Path(GLib.get_user_cache_dir()) / "TauonMusicBox"
		#user_directory   = Path(GLib.get_user_data_dir()) / "TauonMusicBox"
		config_directory = user_directory

	#	if not user_directory.is_dir():
	#		os.makedirs(user_directory)

		if not config_directory.is_dir():
			os.makedirs(config_directory)

		if snap_mode:
			logging.info("Installed as Snap")
		elif flatpak_mode:
			logging.info("Installed as Flatpak")
		else:
			logging.info("Running from installed location")

		if not (user_directory / "encoder").is_dir():
			os.makedirs(user_directory / "encoder")


	# elif (system == 'Windows' or msys) and (
	# 	'Program Files' in install_directory or
	# 	os.path.isfile(install_directory + '\\unins000.exe')):
	#
	#	 user_directory = os.path.expanduser('~').replace("\\", '/') + "/Music/TauonMusicBox"
	#	 config_directory = user_directory
	#	 cache_directory = user_directory / "cache"
	#	 logging.info(f"User Directory: {user_directory}")
	#	 install_mode = True
	#	 if not os.path.isdir(user_directory):
	#		 os.makedirs(user_directory)

	else:
		logging.info("Running in portable mode")
		config_directory = user_directory

	if not (user_directory / "state.p").is_file() and cache_directory.is_dir():
		logging.info("Clearing old cache directory")
		logging.info(cache_directory)
		shutil.rmtree(str(cache_directory))

	n_cache_dir = cache_directory / "network"
	e_cache_dir = cache_directory / "export"
	g_cache_dir = cache_directory / "gallery"
	a_cache_dir = cache_directory / "artist"
	r_cache_dir = cache_directory / "radio-thumbs"
	b_cache_dir = user_directory  / "artist-backgrounds"

	if not os.path.isdir(n_cache_dir):
		os.makedirs(n_cache_dir)
	if not os.path.isdir(e_cache_dir):
		os.makedirs(e_cache_dir)
	if not os.path.isdir(g_cache_dir):
		os.makedirs(g_cache_dir)
	if not os.path.isdir(a_cache_dir):
		os.makedirs(a_cache_dir)
	if not os.path.isdir(b_cache_dir):
		os.makedirs(b_cache_dir)
	if not os.path.isdir(r_cache_dir):
		os.makedirs(r_cache_dir)

	if not (user_directory / "artist-pictures").is_dir():
		os.makedirs(user_directory / "artist-pictures")

	if not (user_directory / "theme").is_dir():
		os.makedirs(user_directory / "theme")

	if platform_system == "Linux":
		system_config_directory = Path(GLib.get_user_config_dir())
		xdg_dir_file = system_config_directory / "user-dirs.dirs"

		if xdg_dir_file.is_file():
			with xdg_dir_file.open() as f:
				for line in f:
					if line.startswith("XDG_MUSIC_DIR="):
						music_directory = Path(os.path.expandvars(line.split("=")[1].strip().replace('"', ""))).expanduser()
						logging.debug(f"Found XDG-Music:     {music_directory}     in {xdg_dir_file}")
					if line.startswith("XDG_DOWNLOAD_DIR="):
						target = Path(os.path.expandvars(line.split("=")[1].strip().replace('"', ""))).expanduser()
						if Path(target).is_dir():
							download_directory = target
						logging.debug(f"Found XDG-Downloads: {download_directory} in {xdg_dir_file}")


	if os.getenv("XDG_MUSIC_DIR"):
		music_directory = Path(os.getenv("XDG_MUSIC_DIR"))
		logging.debug(f"Override music to: {music_directory}")

	if os.getenv("XDG_DOWNLOAD_DIR"):
		download_directory = Path(os.getenv("XDG_DOWNLOAD_DIR"))
		logging.debug(f"Override downloads to: {download_directory}")

	if music_directory:
		music_directory = Path(os.path.expandvars(music_directory))
	if download_directory:
		download_directory = Path(os.path.expandvars(download_directory))

	if not music_directory.is_dir():
		music_directory = None

	locale_directory = install_directory / "locale"
	if flatpak_mode:
		locale_directory = Path("/app/share/locale")
	#elif str(install_directory).startswith(("/opt/", "/usr/")):
	#	locale_directory = Path("/usr/share/locale")

	dirs = Directories(
		install_directory=install_directory,
		svg_directory=svg_directory,
		asset_directory=asset_directory,
		scaled_asset_directory=scaled_asset_directory,
		locale_directory=locale_directory,
		user_directory=user_directory,
		config_directory=config_directory,
		cache_directory=cache_directory,
		home_directory=home_directory,
		music_directory=music_directory,
		download_directory=download_directory,
		n_cache_directory=n_cache_dir,
		e_cache_directory=e_cache_dir,
		g_cache_directory=g_cache_dir,
		a_cache_directory=a_cache_dir,
		r_cache_directory=r_cache_dir,
		b_cache_directory=b_cache_dir,
	)

	logging.info(f"Install directory:         {install_directory}")
	#logging.info(f"SVG directory:             {svg_directory}")
	logging.info(f"Asset directory:           {asset_directory}")
	#logging.info(f"Scaled Asset Directory:    {scaled_asset_directory}")
	if locale_directory.exists():
		logging.info(f"Locale directory:          {locale_directory}")
	else:
		logging.error(f"Locale directory MISSING:  {locale_directory}")
	logging.info(f"Userdata directory:        {user_directory}")
	logging.info(f"Config directory:          {config_directory}")
	logging.info(f"Cache directory:           {cache_directory}")
	logging.info(f"Home directory:            {home_directory}")
	logging.info(f"Music directory:           {music_directory}")
	logging.info(f"Downloads directory:       {download_directory}")

	launch_prefix = ""
	if flatpak_mode:
		launch_prefix = "flatpak-spawn --host "

	if not macos:
		icon = sdl3.IMG_Load(str(asset_directory / "icon-64.png").encode())
	else:
		icon = sdl3.IMG_Load(str(asset_directory / "tau-mac.png").encode())

	sdl3.SDL_SetWindowIcon(t_window, icon)

	if not phone:
		if window_size[0] != logical_size[0]:
			sdl3.SDL_SetWindowMinimumSize(t_window, 560, 330)
		else:
			sdl3.SDL_SetWindowMinimumSize(t_window, round(560 * scale), round(330 * scale))

	max_window_tex = 1000
	if window_size[0] > max_window_tex or window_size[1] > max_window_tex:
		while window_size[0] > max_window_tex:
			max_window_tex += 1000
		while window_size[1] > max_window_tex:
			max_window_tex += 1000

	main_texture = sdl3.SDL_CreateTexture(
		renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, max_window_tex,
		max_window_tex)
	main_texture_overlay_temp = sdl3.SDL_CreateTexture(
		renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET,
		max_window_tex, max_window_tex)

	overlay_texture_texture = sdl3.SDL_CreateTexture(renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, 300, 300)
	sdl3.SDL_SetTextureBlendMode(overlay_texture_texture, sdl3.SDL_BLENDMODE_BLEND)
	sdl3.SDL_SetRenderTarget(renderer, overlay_texture_texture)
	sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
	sdl3.SDL_RenderClear(renderer)
	sdl3.SDL_SetRenderTarget(renderer, None)

	tracklist_texture = sdl3.SDL_CreateTexture(
		renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, max_window_tex,
		max_window_tex)
	tracklist_texture_rect = sdl3.SDL_FRect(0, 0, max_window_tex, max_window_tex)
	sdl3.SDL_SetTextureBlendMode(tracklist_texture, sdl3.SDL_BLENDMODE_BLEND)

	sdl3.SDL_SetRenderTarget(renderer, None)

	# Paint main texture
	sdl3.SDL_SetRenderTarget(renderer, main_texture)
	sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)

	sdl3.SDL_SetRenderTarget(renderer, main_texture_overlay_temp)
	sdl3.SDL_SetTextureBlendMode(main_texture_overlay_temp, sdl3.SDL_BLENDMODE_BLEND)
	sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
	sdl3.SDL_RenderClear(renderer)



	# sdl3.SDL_SetRenderTarget(renderer, None)
	# sdl3.SDL_SetRenderDrawColor(renderer, 7, 7, 7, 255)
	# sdl3.SDL_RenderClear(renderer)
	# #sdl3.SDL_RenderPresent(renderer)

	# sdl3.SDL_SetWindowOpacity(t_window, window_opacity)

	loaded_asset_dc: dict[str, WhiteModImageAsset | LoadImageAsset] = {}
	# loading_image = asset_loader(bag, bag.loaded_asset_dc, "loading.png")

	if maximized:
		i_x = pointer(c_int(0))
		i_y = pointer(c_int(0))

		time.sleep(0.02)
		sdl3.SDL_PumpEvents()
		sdl3.SDL_GetWindowSize(t_window, i_x, i_y)
		logical_size[0] = i_x.contents.value
		logical_size[1] = i_y.contents.value
		sdl3.SDL_GetWindowSizeInPixels(t_window, i_x, i_y)
		window_size[0] = i_x.contents.value
		window_size[1] = i_y.contents.value

	# loading_image.render(window_size[0] // 2 - loading_image.w // 2, window_size[1] // 2 - loading_image.h // 2)
	# SDL_RenderPresent(renderer)

	if install_directory != config_directory and not (config_directory / "input.txt").is_file():
		logging.warning("Input config file is missing, first run? Copying input.txt template from templates directory")
		#logging.warning(install_directory)
		#logging.warning(config_directory)
		shutil.copy(install_directory / "templates" / "input.txt", config_directory)

	if snap_mode:
		discord_allow = False

	musicbrainzngs.set_useragent("TauonMusicBox", n_version, "https://github.com/Taiko2k/Tauon")

	# Detect locale for translations
	try:
		py_locale.setlocale(py_locale.LC_ALL, "")
	except Exception:
		logging.exception("SET LOCALE ERROR")

	if system == "Windows":
		os.environ["SDL_BINARY_PATH"] = str(install_directory / "lib")

	wayland = True
	if os.environ.get("SDL_VIDEODRIVER") != "wayland":
		wayland = False
		os.environ["GDK_BACKEND"] = "x11"

	vis_update = False


	# Player Variables----------------------------------------------------------------------------
	Archive_Formats = {"zip"}

	if whicher("unrar", flatpak_mode):
		Archive_Formats.add("rar")

	if whicher("7z", flatpak_mode):
		Archive_Formats.add("7z")

	MOD_Formats = {"xm", "mod", "s3m", "it", "mptm", "umx", "okt", "mtm", "669", "far", "wow", "dmf", "med", "mt2", "ult"}
	GME_Formats = {"ay", "gbs", "gym", "hes", "kss", "nsf", "nsfe", "sap", "spc", "vgm", "vgz"}
	formats = Formats(
		colours = {
			"MP3":   ColourRGBA(255, 130, 80,  255),  # Burnt orange
			"FLAC":  ColourRGBA(156, 249, 79,  255),  # Bright lime green
			"M4A":   ColourRGBA(81,  220, 225, 255),  # Soft cyan
			"AIFF":  ColourRGBA(81,  220, 225, 255),  # Soft cyan
			"OGG":   ColourRGBA(244, 244, 78,  255),  # Light yellow
			"OGA":   ColourRGBA(244, 244, 78,  255),  # Light yellow
			"WMA":   ColourRGBA(213, 79,  247, 255),  # Magenta
			"APE":   ColourRGBA(247, 79,  79,  255),  # Deep pink
			"TTA":   ColourRGBA(94,  78,  244, 255),  # Purple
			"OPUS":  ColourRGBA(247, 79,  146, 255),  # Pink
			"AAC":   ColourRGBA(79,  247, 168, 255),  # Teal
			"WV":    ColourRGBA(229, 23,  18,  255),  # Deep red
			"PLEX":  ColourRGBA(229, 160, 13,  255),  # Orange-brown
			"KOEL":  ColourRGBA(111, 98,  190, 255),  # Lavender
			"TAU":   ColourRGBA(111, 98,  190, 255),  # Lavender
			"SUB":   ColourRGBA(235, 140, 20,  255),  # Golden yellow
			"SPTY":  ColourRGBA(30,  215, 96,  255),  # Bright green
			"TIDAL": ColourRGBA(0,   0,   0,   255),  # Black
			"JELY":  ColourRGBA(190, 100, 210, 255),  # Fuchsia
			"XM":    ColourRGBA(50,  50,  50,  255),  # Grey
			"MOD":   ColourRGBA(50,  50,  50,  255),  # Grey
			"S3M":   ColourRGBA(50,  50,  50,  255),  # Grey
			"IT":    ColourRGBA(50,  50,  50,  255),  # Grey
			"MPTM":  ColourRGBA(50,  50,  50,  255),  # Grey
			"AY":    ColourRGBA(237, 212, 255, 255),  # Pastel purple
			"GBS":   ColourRGBA(255, 165, 0,   255),  # Vibrant orange
			"GYM":   ColourRGBA(0,   191, 255, 255),  # Bright blue
			"HES":   ColourRGBA(176, 224, 230, 255),  # Light blue-green
			"KSS":   ColourRGBA(255, 255, 153, 255),  # Bright yellow
			"NSF":   ColourRGBA(255, 140, 0,   255),  # Deep orange
			"NSFE":  ColourRGBA(255, 140, 0,   255),  # Deep orange
			"SAP":   ColourRGBA(152, 255, 152, 255),  # Light green
			"SPC":   ColourRGBA(255, 128, 0,   255),  # Bright orange
			"VGM":   ColourRGBA(0,   128, 255, 255),  # Deep blue
			"VGZ":   ColourRGBA(0,   128, 255, 255),  # Deep blue
		},
		VID = {"mp4", "webm"},
		MOD = MOD_Formats,
		GME = GME_Formats,
		DA = {
			"mp3", "wav", "opus", "flac", "ape", "aiff",
			"m4a", "ogg", "oga", "aac", "tta", "wv", "wma",
		} | MOD_Formats | GME_Formats,
		Archive = Archive_Formats,
	)


	# ---------------------------------------------------------------------
	# Player variables
	# pl_follow = False
	draw_sep_hl = False

	# -------------------------------------------------------------------------------
	# Playlist Variables
	default_playlist: list[int] = []

	# Library and loader Variables--------------------------------------------------------
	master_library: dict[int, TrackClass] = {}

	db_version: float = 0.0
	latest_db_version: float = 73

	rename_files_previous = ""
	rename_folder_previous = ""
	p_force_queue: list[TauonQueueItem] = []

	radio_playlists: list[RadioPlaylist] = [RadioPlaylist(uid=uid_gen(), name="Default", stations=[])]

	fonts = Fonts()
	colours = ColoursClass()
	colours.post_config()

	mpt: CDLL | None = None
	p = ctypes.util.find_library("openmpt") # Linux
	p = p if p else ctypes.util.find_library("libopenmpt-0") # Windows
	try:
		if p:
			mpt = ctypes.cdll.LoadLibrary(p)
		elif msys:
			mpt = ctypes.cdll.LoadLibrary("libopenmpt-0.dll")
		else:
			mpt = ctypes.cdll.LoadLibrary("libopenmpt.so.0")

		mpt.openmpt_module_create_from_memory.restype = c_void_p
		mpt.openmpt_module_get_metadata.restype = c_char_p
		mpt.openmpt_module_get_duration_seconds.restype = c_double
	except Exception:
		logging.exception("Failed to load libopenmpt!")

	gme: CDLL | None = None
	p = ctypes.util.find_library("gme") # Linux
	p = p if p else ctypes.util.find_library("libgme") # Windows
	try:
		if p:
			gme = ctypes.cdll.LoadLibrary(p)
		elif msys:
			gme = ctypes.cdll.LoadLibrary("libgme.dll")
		else:
			gme = ctypes.cdll.LoadLibrary("libgme.so.0")

		gme.gme_free_info.argtypes = [ctypes.POINTER(GMETrackInfo)]
		gme.gme_track_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(GMETrackInfo)), ctypes.c_int]
		gme.gme_track_info.restype = ctypes.c_char_p
		gme.gme_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
		gme.gme_open_file.restype = ctypes.c_char_p
	except Exception:
		logging.exception("Cannot find libgme")

	force_subpixel_text = False
	if gtk_settings and gtk_settings.get_property("gtk-xft-rgba") == "rgb":
		force_subpixel_text = True
	dc_device = False  # (BASS) Disconnect device on pause
	if desktop == "KDE":
		dc_device = True
	encoder_output = user_directory / "encoder" if music_directory is None else music_directory / "encode-output"
	power_save = False
	if macos or phone:
		power_save = True

	# TODO(Taiko): This is legacy. New settings are added straight to the save list (need to overhaul)
	view_prefs = {
		"split-line": True,
		"update-title": False,
		"star-lines": False,
		"side-panel": True,
		"dim-art": False,
		"pl-follow": False,
		"scroll-enable": True,
	}

	prefs = Prefs(
		view_prefs=view_prefs,
		power_save=power_save,
		encoder_output=encoder_output,
		force_subpixel_text=force_subpixel_text,
		dc_device=dc_device,
		macos=macos,
		macstyle=macos or detect_macstyle,
		left_window_control=macos or left_window_control,
		phone=phone,
		discord_allow=discord_allow,
		desktop=desktop,
		window_opacity=window_opacity,
		ui_scale=scale,
	)
	prefs.theme = get_theme_number(dirs, prefs.theme_name)

	bag = Bag(
		cf=Config(),
		gme=gme,
		mpt=mpt,
		colours=colours,
		console=DConsole(),
		dirs=dirs,
		prefs=prefs,
		fonts=fonts,
		formats=formats,
		renderer=renderer,
		#sdl_syswminfo=sss,
		system=system,
		pump=True,
		wayland=wayland,
		# de_notify_support = desktop == 'GNOME' or desktop == 'KDE'
		de_notify_support=False,
		draw_min_button=draw_min_button,
		draw_max_button=draw_max_button,
		download_directories=[],
		overlay_texture_texture=overlay_texture_texture,
		smtc=False,
		macos=macos,
		mac_close=mac_close,
		mac_maximize=mac_maximize,
		mac_minimize=mac_minimize,
		msys=msys,
		phone=phone,
		should_save_state=True,
		old_window_position=old_window_position,
		desktop=desktop,
		platform_system=platform_system,
		last_fm_enable=last_fm_enable,
		launch_prefix=launch_prefix,
		latest_db_version=latest_db_version,
		flatpak_mode=flatpak_mode,
		snap_mode=snap_mode,
		master_count=0,
		playing_in_queue=0,
		playlist_playing=-1,
		playlist_view_position=0,
		selected_in_playlist=-1,
		album_mode_art_size=int(200 * scale),
		primary_stations=[],
		tls_context=tls_context,
		track_queue=[],
		volume=75,
		multi_playlist=[],
		cue_list=[],
		p_force_queue=p_force_queue,
		logical_size=logical_size,
		window_size=window_size,
		gen_codes={},
		master_library=master_library,
		loaded_asset_dc=loaded_asset_dc,
		radio_playlist_viewing=0,
		radio_playlists=radio_playlists,
		folder_image_offsets={},
	)
	del radio_playlists

	# If scaled-icons directory exists, use it even for initial loading
	if (user_directory / "scaled-icons").exists() and bag.prefs.ui_scale != 1:
		bag.dirs.scaled_asset_directory = user_directory / "scaled-icons"

	gui = GuiVar(
		bag=bag,
		tracklist_texture_rect=tracklist_texture_rect,
		tracklist_texture=tracklist_texture,
		main_texture_overlay_temp=main_texture_overlay_temp,
		main_texture=main_texture,
		max_window_tex=max_window_tex,
	)
	del max_window_tex

	inp = gui.inp
	keymaps = gui.keymaps
	# GUI Variables -------------------------------------------------------------------------------------------
	# Variables now go in the gui, pctl, input and prefs class instances. The following just haven't been moved yet
	spot_cache_saved_albums = [] # TODO(Martin): This isn't really used? It's just fed to spot_ctl as [] or saved, but we never save it
	# TODO(Martin): Move these 6 vars
	resize_mode = False
	spec_smoothing = True
	row_len = 5
	time_last_save = 0
	b_info_y = int(window_size[1] * 0.7)  # For future possible panel below playlist
	# Playlist Panel
	scroll_opacity = 0

	# -----------------------------------------------------
	# STATE LOADING
	# Loading of program data from previous run
	gbc.disable()
	ggc = 2

	if (user_directory / "lyrics_substitutions.json").is_file():
		try:
			with (user_directory / "lyrics_substitutions.json").open() as f:
				prefs.lyrics_subs = json.load(f)
		except FileNotFoundError:
			logging.error("No existing lyrics_substitutions.json file")
		except Exception:
			logging.exception("Unknown error loading lyrics_substitutions.json")

	for station in bag.primary_stations:
		bag.radio_playlists[0].stations.append(station)

	shoot_pump = threading.Thread(target=pumper, args=(bag,))
	shoot_pump.daemon = True
	shoot_pump.start()

	after_scan: list[TrackClass] = []
	search_string_cache          = {}
	search_dia_string_cache      = {}
	state_path1 = user_directory / "state.p"
	state_path2 = user_directory / "state.p.backup"
	for t in range(2):
		#	 os.path.getsize(user_directory / "state.p") < 100
		try:
			if t == 0:
				if not state_path1.is_file():
					continue
				with state_path1.open("rb") as file:
					save = pickle.load(file)
			if t == 1:
				if not state_path2.is_file():
					logging.warning("State database file is missing, first run? Will create one anew!")
					break
				logging.warning("Loading backup state.p!")
				with state_path2.open("rb") as file:
					save = pickle.load(file)

			# def tt():
			#	 while True:
			#		 logging.info(state_file.tell())
			#		 time.sleep(0.01)
			# shooter(tt)

			db_version = save[17]
			if db_version != latest_db_version:
				if db_version > latest_db_version:
					logging.critical(f"Loaded DB version: '{db_version}' is newer than latest known DB version '{latest_db_version}', refusing to load!\nAre you running an out of date Tauon version using Configuration directory from a newer one?")
					sys.exit(42)
				logging.warning(f"Loaded older DB version: {db_version}")
			if len(save) > 63 and save[63] is not None:
				prefs.ui_scale = save[63]
				# prefs.ui_scale = 1.3
				# gui.__init__()

			if len(save) > 0 and save[0] is not None:
				master_library = save[0]
			bag.master_count = save[1]
			bag.playlist_playing = save[2]
			bag.active_playlist_viewing = save[3]
			bag.playlist_view_position = save[4]
			if len(save) > 5 and save[5] is not None:
				if db_version > 68:
					bag.multi_playlist = []
					tauonplaylist_jar = save[5]
					for i, d in enumerate(tauonplaylist_jar):
						p = TauonPlaylist(**d)
						bag.multi_playlist.append(p)
						if i == bag.active_playlist_viewing:
							default_playlist = p.playlist_ids
				else:
					bag.multi_playlist = save[5]
			bag.volume = save[6]
			bag.track_queue = save[7]
			bag.playing_in_queue = save[8]
			# default_playlist = save[9]  # value is now set above
			# bag.playlist_playing = save[10]
			# cue_list = save[11]
			# radio_field_text = save[12]
			prefs.theme = save[13]
			bag.folder_image_offsets = save[14]
			# lfm_username = save[15]
			# lfm_hash = save[16]
			prefs.view_prefs = save[18]
			# window_size = save[19]
			gui.save_size = copy.copy(save[19])
			gui.rspw = save[20]
			# savetime = save[21]
			gui.vis_want = save[22]
			bag.selected_in_playlist = save[23]
			if len(save) > 24 and save[24] is not None:
				bag.album_mode_art_size = save[24]
			if len(save) > 25 and save[25] is not None:
				draw_border = save[25]
			if len(save) > 26 and save[26] is not None:
				prefs.enable_web = save[26]
			if len(save) > 27 and save[27] is not None:
				prefs.allow_remote = save[27]
			if len(save) > 28 and save[28] is not None:
				prefs.expose_web = save[28]
			if len(save) > 29 and save[29] is not None:
				prefs.enable_transcode = save[29]
			if len(save) > 30 and save[30] is not None:
				prefs.show_rym = save[30]
			# if len(save) > 31 and save[31] is not None:
			#	 combo_mode_art_size = save[31]
			if len(save) > 32 and save[32] is not None:
				gui.maximized = save[32]
			if len(save) > 33 and save[33] is not None:
				prefs.prefer_bottom_title = save[33]
			if len(save) > 34 and save[34] is not None:
				gui.display_time_mode = save[34]
			# if len(save) > 35 and save[35] is not None:
			#	 prefs.transcode_mode = save[35]
			if len(save) > 36 and save[36] is not None:
				prefs.transcode_codec = save[36]
			if len(save) > 37 and save[37] is not None:
				prefs.transcode_bitrate = save[37]
			# if len(save) > 38 and save[38] is not None:
			#	 prefs.line_style = save[38]
			# if len(save) > 39 and save[39] is not None:
			#	 prefs.cache_gallery = save[39]
			if len(save) > 40 and save[40] is not None:
				prefs.playlist_font_size = save[40]
			if len(save) > 41 and save[41] is not None:
				prefs.use_title = save[41]
			if len(save) > 42 and save[42] is not None:
				gui.pl_st = save[42]
			# if len(save) > 43 and save[43] is not None:
			#	 gui.set_mode = save[43]
			#	 gui.set_bar = gui.set_mode
			if len(save) > 45 and save[45] is not None:
				prefs.playlist_row_height = save[45]
			if len(save) > 46 and save[46] is not None:
				prefs.show_wiki = save[46]
			if len(save) > 47 and save[47] is not None:
				prefs.auto_extract = save[47]
			if len(save) > 48 and save[48] is not None:
				prefs.colour_from_image = save[48]
			if len(save) > 49 and save[49] is not None:
				gui.set_bar = save[49]
			if len(save) > 50 and save[50] is not None:
				gui.gallery_show_text = save[50]
			if len(save) > 51 and save[51] is not None:
				gui.bb_show_art = save[51]
			# if len(save) > 52 and save[52] is not None:
			#	 gui.show_stars = save[52]
			if len(save) > 53 and save[53] is not None:
				prefs.auto_lfm = save[53]
			if len(save) > 54 and save[54] is not None:
				prefs.scrobble_mark = save[54]
			if len(save) > 55 and save[55] is not None:
				prefs.replay_gain = save[55]
			# if len(save) > 56 and save[56] is not None:
			#	 prefs.radio_page_lyrics = save[56]
			if len(save) > 57 and save[57] is not None:
				prefs.show_gimage = save[57]
			if len(save) > 58 and save[58] is not None:
				prefs.end_setting = save[58]
			if len(save) > 59 and save[59] is not None:
				prefs.show_gen = save[59]
			# if len(save) > 60 and save[60] is not None:
			#	 url_saves = save[60]
			if len(save) > 61 and save[61] is not None:
				prefs.auto_del_zip = save[61]
			if len(save) > 62 and save[62] is not None:
				gui.level_meter_colour_mode = save[62]
			if len(save) > 64 and save[64] is not None:
				prefs.show_lyrics_side = save[64]
			# if len(save) > 65 and save[65] is not None:
			#	 prefs.last_device = save[65]
			if len(save) > 66 and save[66] is not None:
				gui.restart_album_mode = save[66]
			if len(save) > 67 and save[67] is not None:
				gui.album_playlist_width = save[67]
			if len(save) > 68 and save[68] is not None:
				prefs.transcode_opus_as = save[68]
			if len(save) > 69 and save[69] is not None:
				gui.star_mode = save[69]
			del save
			break

		except IndexError:
			logging.exception("Index error")
			break
		except Exception:
			logging.exception("Failed to load save file")

	tauon = Tauon(
		holder=holder,
		bag=bag,
		gui=gui,
	)
	tauon.after_scan              = after_scan
	tauon.search_string_cache     = search_string_cache
	tauon.search_dia_string_cache = search_dia_string_cache
	signal.signal(signal.SIGINT, tauon.signal_handler)
	radiobox = tauon.radiobox
	pctl = tauon.pctl

#type_enforced.Enforcer(sys.modules[__name__])
