import colorsys
import copy
import ctypes
import ctypes.util
import datetime
import gc as gbc
import logging
import math
import os
import pickle
import shutil
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from ctypes import (
	c_int,
	pointer,
)
from pathlib import Path

import sdl3

from tauon.t_modules.t_enums import LoaderCommand, PlayingState, StopMode
from tauon.t_modules.t_extra import (
	ColourRGBA,
	TestTimer,
	Timer,
	alpha_blend,
	alpha_mod,
	check_equal,
	clean_string,
	colour_value,
	d_date_display,
	get_filesize_string,
	grow_rect,
	hls_to_rgb,
	point_distance,
	point_proximity_test,
	rgb_to_hls,
	test_lumi,
	tmp_cache_dir,
)
from tauon.t_modules.t_main import (
	LoadImageAsset,
	Menu,
	MetaBox,
	Notify,
	Showcase,
	StandardPlaylist,
	StarRecord,
	Tauon,
	TextBox,
	WhiteModImageAsset,
	auto_scale,
	close_all_menus,
	coll_point,
	copy_to_clipboard,
	encode_folder_name,
	get_global_mouse,
	get_themes,
	get_window_position,
	macos,
	menu_is_open,
	parse_template2,
	queue_item_gen,
	system,
	unidecode,
	window_is_focused,
)
from tauon.t_modules.t_themeload import load_theme


def main_loop(tauon: Tauon) -> None:
	bag            = tauon.bag
	ddt            = tauon.ddt
	gui            = tauon.gui
	inp            = tauon.inp
	dirs           = tauon.dirs
	pctl           = tauon.pctl
	prefs          = tauon.prefs
	colours        = tauon.colours
	radiobox       = tauon.radiobox
	renderer       = tauon.renderer
	t_window       = tauon.t_window
	pref_box       = tauon.pref_box
	keymaps        = tauon.gui.keymaps
	user_directory = tauon.dirs.user_directory
	window_size    = tauon.window_size
	logical_size   = tauon.logical_size
	center_info_menu      = tauon.center_info_menu
	gallery_menu          = tauon.gallery_menu
	lightning_menu        = tauon.lightning_menu
	tab_menu              = tauon.tab_menu

	# MAIN LOOP
	event = sdl3.SDL_Event()

	# ---------------------------------------------------------------------
	# Player variables
	draw_sep_hl = False

	# Playlist Panel
	scroll_opacity = 0

	row_len = 5
	b_info_y = int(window_size[1] * 0.7)  # For future possible panel below playlist

	gal_up = False
	gal_down = False
	gal_left = False
	gal_right = False

	scroll_hold = False
	album_scroll_hold = False
	scroll_point = 0
	scroll_bpoint = 0
	sbl = 50
	sbp = 100

	time_last_save = 0
	spec_smoothing = True # TODO(Martin): Always true
	resize_mode = False   # TODO(Martin): Always false
	power = 0
	reset_render = False
	c_yax = 0
	c_yax_timer = Timer()
	c_xax = 0
	c_xax_timer = Timer()
	c_xay = 0
	c_xay_timer = Timer()
	rt = 0
	ggc = 2
	pl_bg = None
	if (tauon.user_directory / "bg.png").exists():
		pl_bg = LoadImageAsset(
			scaled_asset_directory=tauon.dirs.scaled_asset_directory, path=str(tauon.user_directory / "bg.png"), is_full_path=True)

	playlist_render = StandardPlaylist(tauon, pl_bg)
	meta_box = MetaBox(tauon)
	showcase = Showcase(tauon)

	while pctl.running:
		# bm.get('main')
		# time.sleep(100)

		if inp.k_input:
			keymaps.hits.clear()

			inp.d_mouse_click = False
			inp.right_click = False
			inp.level_2_right_click = False
			inp.mouse_click = False
			inp.middle_click = False
			inp.mouse_up = False
			inp.key_return_press = False
			inp.key_down_press = False
			inp.key_up_press = False
			inp.key_right_press = False
			inp.key_left_press = False
			inp.key_esc_press = False
			inp.key_del = False
			inp.backspace_press = 0
			inp.key_backspace_press = False
			inp.key_tab_press = False
			inp.key_c_press = False
			inp.key_v_press = False
			inp.key_a_press = False
			inp.key_s_press = False
			inp.key_z_press = False
			inp.key_x_press = False
			inp.key_home_press = False
			inp.key_end_press = False
			inp.mouse_wheel = 0
			pref_box.scroll = 0
			gui.new_playlist_cooldown = False
			inp.input_text = ""
			inp.level_2_enter = False

			mouse_enter_window = False
			gui.mouse_in_window = True
			if inp.key_focused:
				inp.key_focused -= 1

		# f not inp.mouse_down:
		inp.k_input = False
		inp.global_clicked = False
		focused = False
		mouse_moved = False
		gui.level_2_click = False

		# gui.update = 2

		while sdl3.SDL_PollEvent(ctypes.byref(event)) != 0:
			# if event.type == sdl3.SDL_SYSWMEVENT:
			#      logging.info(event.syswm.msg.contents) # Not implemented by pysdl2

			if event.type == sdl3.SDL_EVENT_GAMEPAD_ADDED and prefs.use_gamepad:
				if sdl3.SDL_IsGamepad(event.gdevice.which):
					sdl3.SDL_OpenGamepad(event.gdevice.which)
					try:
						logging.info(f"Found game controller: {sdl3.SDL_GetGamepadNameForID(event.gdevice.which).decode()}")
					except Exception:
						logging.exception("Error getting game controller")

			if event.type == sdl3.SDL_EVENT_GAMEPAD_AXIS_MOTION and prefs.use_gamepad:
				if event.gaxis.axis == sdl3.SDL_GAMEPAD_AXIS_LEFT_TRIGGER:
					rt = event.gaxis.value > 5000
				if event.gaxis.axis == sdl3.SDL_GAMEPAD_AXIS_LEFTY:
					if event.gaxis.value < -10000:
						new = -1
					elif event.gaxis.value > 10000:
						new = 1
					else:
						new = 0
					if new != c_yax:
						c_yax_timer.force_set(1)
					c_yax = new
					power += 5
					gui.update += 1
				if event.gaxis.axis == sdl3.SDL_GAMEPAD_AXIS_RIGHTX:
					if event.gaxis.value < -15000:
						new = -1
					elif event.gaxis.value > 15000:
						new = 1
					else:
						new = 0
					if new != c_xax:
						c_xax_timer.force_set(1)
					c_xax = new
					power += 5
					gui.update += 1
				if event.gaxis.axis == sdl3.SDL_GAMEPAD_AXIS_RIGHTY:
					if event.gaxis.value < -15000:
						new = -1
					elif event.gaxis.value > 15000:
						new = 1
					else:
						new = 0
					if new != c_xay:
						c_xay_timer.force_set(1)
					c_xay = new
					power += 5
					gui.update += 1

			if event.type == sdl3.SDL_EVENT_GAMEPAD_BUTTON_DOWN and prefs.use_gamepad:
				inp.k_input = True
				power += 5
				gui.update += 2
				#print(event.gbutton.button)
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER:
					if rt:
						tauon.toggle_random()
					else:
						pctl.advance()
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_LEFT_SHOULDER:
					if rt:
						tauon.toggle_repeat()
					else:
						pctl.back()
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_SOUTH:
					if rt:
						pctl.show_current(highlight=True)
					elif pctl.playing_ready() and pctl.active_playlist_playing == pctl.active_playlist_viewing and \
							pctl.selected_ready() and pctl.default_playlist[
						pctl.selected_in_playlist] == pctl.playing_object().index:
						pctl.play_pause()
					else:
						inp.key_return_press = True
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_WEST:
					if rt:
						tauon.random_track()
					else:
						tauon.toggle_gallery_keycontrol(always_exit=True)
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_NORTH:
					if rt:
						pctl.advance(rr=True)
					else:
						pctl.play_pause()
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_EAST:
					if rt:
						pctl.revert()
					elif tauon.is_level_zero():
						pctl.stop()
					else:
						inp.key_esc_press = True
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_DPAD_UP:
					inp.key_up_press = True
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_DPAD_DOWN:
					inp.key_down_press = True
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_DPAD_LEFT:
					if gui.album_tab_mode:
						inp.key_left_press = True
					elif ( tauon.is_level_zero() or gui.quick_search_mode ) and not gui.timed_lyrics_editing_now:
						pctl.cycle_playlist_pinned(1)
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_DPAD_RIGHT:
					if gui.album_tab_mode:
						inp.key_right_press = True
					elif ( tauon.is_level_zero() or gui.quick_search_mode ) and not gui.timed_lyrics_editing_now:
						pctl.cycle_playlist_pinned(-1)

			if event.type == sdl3.SDL_EVENT_RENDER_TARGETS_RESET and not tauon.msys:
				reset_render = True

			if event.type == sdl3.SDL_EVENT_DROP_TEXT:
				power += 5

				link = event.drop.file.decode()
				#logging.info(link)

				if pctl.playing_ready() and link.startswith("http"):
					if system != "Windows" and sdl3.SDL_version >= 204:
						gmp = get_global_mouse()
						gwp = get_window_position(t_window)
						i_x = gmp[0] - gwp[0]
						i_x = max(i_x, 0)
						i_x = min(i_x, window_size[0])
						i_y = gmp[1] - gwp[1]
						i_y = max(i_y, 0)
						i_y = min(i_y, window_size[1])
					else:
						i_y = pointer(c_int(0))
						i_x = pointer(c_int(0))

						sdl3.SDL_GetMouseState(i_x, i_y)
						i_y = i_y.contents.value / logical_size[0] * window_size[0]
						i_x = i_x.contents.value / logical_size[0] * window_size[0]

					if coll_point((i_x, i_y), gui.main_art_box):
						logging.info("Drop picture...")
						#logging.info(link)
						gui.image_downloading = True
						track = pctl.playing_object()
						target_dir = track.parent_folder_path

						shoot_dl = threading.Thread(target=tauon.download_img, args=(link, target_dir, track))
						shoot_dl.daemon = True
						shoot_dl.start()

						gui.update = True

				elif link.startswith("file:///"):
					link = link.replace("\r", "")
					for line in link.split("\n"):
						target = str(urllib.parse.unquote(line)).replace("file:///", "/")
						tauon.drop_file(target)

			if event.type == sdl3.SDL_EVENT_DROP_BEGIN:
				gui.ext_drop_mode = True
			elif event.type == sdl3.SDL_EVENT_DROP_POSITION:
				inp.mouse_position[0] = int(event.drop.x / logical_size[0] * window_size[0])
				inp.mouse_position[1] = int(event.drop.y / logical_size[0] * window_size[0])
				mouse_moved = True
				gui.mouse_unknown = False
				gui.ext_drop_mode = True
				gui.pl_update += 1
				gui.update += 2
			elif event.type == sdl3.SDL_EVENT_DROP_COMPLETE:
				gui.ext_drop_mode = False
			elif event.type == sdl3.SDL_EVENT_DROP_FILE:
				gui.ext_drop_mode = False
				power += 5
				dropped_file_sdl = event.drop.data
				inp.mouse_position[0] = int(event.drop.x / logical_size[0] * window_size[0])
				inp.mouse_position[1] = int(event.drop.y / logical_size[0] * window_size[0])
				logging.info(f"Dropped data: {dropped_file_sdl}")
				target = str(urllib.parse.unquote(
					dropped_file_sdl.decode("utf-8", errors="surrogateescape"))).replace("file:///", "/").replace("\r", "")
				#logging.info(target)
				tauon.drop_file(target)

			elif event.type == 8192:
				gui.pl_update = 1
				gui.update += 2

			elif event.type == sdl3.SDL_EVENT_QUIT:
				power += 5

				if gui.tray_active and prefs.min_to_tray and not inp.key_shift_down:
					tauon.min_to_tray()
				else:
					tauon.exit("Window received exit signal")
					break
			elif event.type == sdl3.SDL_EVENT_TEXT_EDITING:
				power += 5
				#logging.info("edit text")
				gui.editline = event.edit.text
				#logging.info(gui.editline)
				gui.editline = gui.editline.decode("utf-8", "ignore")
				inp.k_input = True
				gui.update += 1

			elif event.type == sdl3.SDL_EVENT_MOUSE_MOTION:
				inp.mouse_position[0] = int(event.motion.x / logical_size[0] * window_size[0])
				inp.mouse_position[1] = int(event.motion.y / logical_size[0] * window_size[0])
				mouse_moved = True
				gui.mouse_unknown = False
			elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_DOWN:
				inp.k_input = True
				focused = True
				power += 5
				gui.update += 1
				gui.mouse_in_window = True

				if ggc == 2:  # dont click on first full frame
					continue

				if event.button.button == sdl3.SDL_BUTTON_RIGHT:
					inp.right_click = True
					inp.right_down = True
					#logging.info("RIGHT DOWN")
				elif event.button.button == sdl3.SDL_BUTTON_LEFT:
					#logging.info("LEFT DOWN")

					# if inp.mouse_position[1] > 1 and inp.mouse_position[0] > 1:
					#     inp.mouse_down = True

					inp.mouse_click = True

					inp.mouse_down = True
				elif event.button.button == sdl3.SDL_BUTTON_MIDDLE:
					if not tauon.search_over.active:
						inp.middle_click = True
					gui.update += 1
				elif event.button.button == sdl3.SDL_BUTTON_X1:
					keymaps.hits.append("MB4")
				elif event.button.button == sdl3.SDL_BUTTON_X2:
					keymaps.hits.append("MB5")
			elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_UP:
				inp.k_input = True
				power += 5
				gui.update += 1
				if event.button.button == sdl3.SDL_BUTTON_RIGHT:
					inp.right_down = False
				elif event.button.button == sdl3.SDL_BUTTON_LEFT:
					if inp.mouse_down:
						inp.mouse_up = True
						inp.mouse_up_position[0] = event.motion.x / logical_size[0] * window_size[0]
						inp.mouse_up_position[1] = event.motion.y / logical_size[0] * window_size[0]

					inp.mouse_down = False
					gui.update += 1
			elif event.type == sdl3.SDL_EVENT_KEY_DOWN and inp.key_focused == 0:
				inp.k_input = True
				power += 5
				gui.update += 2
				if prefs.use_scancodes:
					keymaps.hits.append(event.key.scancode)
				else:
					keymaps.hits.append(event.key.key)

				if prefs.use_scancodes:
					if event.key.scancode == sdl3.SDL_SCANCODE_V:
						inp.key_v_press = True
					elif event.key.scancode == sdl3.SDL_SCANCODE_A:
						inp.key_a_press = True
					elif event.key.scancode == sdl3.SDL_SCANCODE_S:
						inp.key_s_press = True
					elif event.key.scancode == sdl3.SDL_SCANCODE_C:
						inp.key_c_press = True
					elif event.key.scancode == sdl3.SDL_SCANCODE_Z:
						inp.key_z_press = True
					elif event.key.scancode == sdl3.SDL_SCANCODE_X:
						inp.key_x_press = True
				elif event.key.key == sdl3.SDLK_V:
					inp.key_v_press = True
				elif event.key.key == sdl3.SDLK_A:
					inp.key_a_press = True
				elif event.key.key == sdl3.SDLK_S:
					inp.key_s_press = True
				elif event.key.key == sdl3.SDLK_C:
					inp.key_c_press = True
				elif event.key.key == sdl3.SDLK_Z:
					inp.key_z_press = True
				elif event.key.key == sdl3.SDLK_X:
					inp.key_x_press = True

				if (event.key.key == (sdl3.SDLK_RETURN or sdl3.SDLK_RETURN2) and len(gui.editline) == 0) or (event.key.key == sdl3.SDLK_KP_ENTER and len(gui.editline) == 0):
					inp.key_return_press = True
				elif event.key.key == sdl3.SDLK_TAB:
					inp.key_tab_press = True
				elif event.key.key == sdl3.SDLK_BACKSPACE:
					inp.backspace_press += 1
					inp.key_backspace_press = True
				elif event.key.key == sdl3.SDLK_DELETE:
					inp.key_del = True
				elif event.key.key == sdl3.SDLK_RALT:
					inp.key_ralt = True
				elif event.key.key == sdl3.SDLK_LALT:
					inp.key_lalt = True
				elif event.key.key == sdl3.SDLK_DOWN:
					inp.key_down_press = True
				elif event.key.key == sdl3.SDLK_UP:
					inp.key_up_press = True
				elif event.key.key == sdl3.SDLK_LEFT:
					inp.key_left_press = True
				elif event.key.key == sdl3.SDLK_RIGHT:
					inp.key_right_press = True
				elif event.key.key == sdl3.SDLK_LSHIFT:
					inp.key_shift_down = True
				elif event.key.key == sdl3.SDLK_RSHIFT:
					inp.key_shiftr_down = True
				elif event.key.key == sdl3.SDLK_LCTRL:
					inp.key_ctrl_down = True
				elif event.key.key == sdl3.SDLK_RCTRL:
					inp.key_rctrl_down = True
				elif event.key.key == sdl3.SDLK_HOME:
					inp.key_home_press = True
				elif event.key.key == sdl3.SDLK_END:
					inp.key_end_press = True
				elif event.key.key == sdl3.SDLK_LGUI:
					if macos:
						inp.key_ctrl_down = True
					else:
						inp.key_meta = True
						inp.key_focused = 1

			elif event.type == sdl3.SDL_EVENT_KEY_UP:
				inp.k_input = True
				power += 5
				gui.update += 2
				if event.key.key == sdl3.SDLK_LSHIFT:
					inp.key_shift_down = False
				elif event.key.key == sdl3.SDLK_LCTRL:
					inp.key_ctrl_down = False
				elif event.key.key == sdl3.SDLK_RCTRL:
					inp.key_rctrl_down = False
				elif event.key.key == sdl3.SDLK_RSHIFT:
					inp.key_shiftr_down = False
				elif event.key.key == sdl3.SDLK_RALT:
					gui.album_tab_mode = False
					inp.key_ralt = False
				elif event.key.key == sdl3.SDLK_LALT:
					gui.album_tab_mode = False
					inp.key_lalt = False
				elif event.key.key == sdl3.SDLK_LGUI:
					if macos:
						inp.key_ctrl_down = False
					else:
						inp.key_meta = False
						inp.key_focused = 1

			elif event.type == sdl3.SDL_EVENT_TEXT_INPUT:
				inp.k_input = True
				power += 5
				inp.input_text += event.text.text.decode("utf-8")

				gui.update += 1
				#logging.info(inp.input_text)

			elif event.type == sdl3.SDL_EVENT_MOUSE_WHEEL:
				inp.k_input = True
				power += 6
				inp.mouse_wheel += event.wheel.y

				gui.update += 1
			elif event.type >= sdl3.SDL_EVENT_WINDOW_FIRST and event.type <= sdl3.SDL_EVENT_WINDOW_LAST:
				power += 5
				#logging.info(event.type)

				if event.type == sdl3.SDL_EVENT_WINDOW_FOCUS_GAINED:
					#logging.info("sdl3.SDL_WINDOWEVENT_FOCUS_GAINED")

					if system == "Linux" and not macos and not tauon.msys:
						tauon.gnome.focus()
					inp.k_input = True

					mouse_enter_window = True
					focused = True
					gui.lowered = False
					inp.key_focused = 1
					inp.mouse_down = False
					gui.album_tab_mode = False
					gui.pl_update = 1
					gui.update += 1

				elif event.type == sdl3.SDL_EVENT_WINDOW_FOCUS_LOST:
					close_all_menus()
					inp.key_focused = 1
					gui.update += 1

				elif event.type == sdl3.SDL_EVENT_WINDOW_DISPLAY_CHANGED:
					# sdl3.SDL_WINDOWEVENT_DISPLAY_CHANGED logs new display ID as data1 (0 or 1 or 2...), it not width, and data 2 is always 0
					pass
				elif event.type == sdl3.SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED:
					i_x = pointer(c_int(0))
					i_y = pointer(c_int(0))
					sdl3.SDL_GetWindowSizeInPixels(t_window, i_x, i_y)
					window_size[0] = i_x.contents.value
					window_size[1] = i_y.contents.value
					auto_scale(bag)
					gui.update_layout = True
					gui.update = 2
				elif event.type == sdl3.SDL_EVENT_WINDOW_RESIZED:
					# sdl3.SDL_WINDOWEVENT_RESIZED logs width to data1 and height to data2
					#if event.window.data1 < 500:
					#	logging.error("Window width is less than 500, grrr why does this happen, stupid bug")
					#	sdl3.SDL_SetWindowSize(t_window, logical_size[0], logical_size[1])
					#elif tauon.restore_ignore_timer.get() > 1:  # Hacky
					#	gui.update = 2

					#	logical_size[0] = event.window.data1
					#	logical_size[1] = event.window.data2

					#	if gui.mode != 3:
					#		logical_size[0] = max(300, logical_size[0])
					#		logical_size[1] = max(300, logical_size[1])

					gui.update = 2
					logical_size[0] = event.window.data1
					logical_size[1] = event.window.data2
					#	auto_scale(bag)
					#	gui.update_layout = True


				elif event.type == sdl3.SDL_EVENT_WINDOW_MOUSE_ENTER:
					#logging.info("ENTER")
					mouse_enter_window = True
					gui.mouse_in_window = True
					gui.update += 1

				# elif event.type == sdl3.SDL_WINDOWEVENT_HIDDEN:
				#
				elif event.type == sdl3.SDL_EVENT_WINDOW_EXPOSED:
					#logging.info("expose")
					gui.lowered = False

				elif event.type == sdl3.SDL_EVENT_WINDOW_MINIMIZED:
					gui.lowered = True
					# if prefs.min_to_tray:
					# 	tray.down()
					# tauon.thread_manager.sleep()

				elif event.type == sdl3.SDL_EVENT_WINDOW_RESTORED:
					gui.lowered = False
					gui.maximized = False
					gui.pl_update = 1
					gui.update += 2

					if prefs.update_title:
						tauon.update_title_do()
						#logging.info("restore")

				elif event.type == sdl3.SDL_EVENT_WINDOW_SHOWN:
					focused = True
					gui.pl_update = 1
					gui.update += 1

				# elif event.type == sdl3.SDL_WINDOWEVENT_FOCUS_GAINED:
				#     logging.info("FOCUS GAINED")
				#     # input.mouse_enter_event = True
				#     # gui.update += 1
				#     # inp.k_input = True

				elif event.type == sdl3.SDL_EVENT_WINDOW_MAXIMIZED:
					if gui.mode != 3:  # TODO(Taiko): workaround. sdl bug? gives event on window size set
						gui.maximized = True
					gui.update_layout = True
					gui.pl_update = 1
					gui.update += 1

				elif event.type == sdl3.SDL_EVENT_WINDOW_MOUSE_LEAVE:
					gui.mouse_in_window = False
					gui.update += 1
					power = 1000

		if mouse_moved and tauon.fields.test():
			gui.update += 1


		# if tauon.thread_manager.sleeping:
		#     if not gui.lowered:
		#         tauon.thread_manager.wake()
		if gui.lowered:
			gui.update = 0
		# ----------------
		# This section of code controls the internal processing speed or 'frame-rate'
		# It's pretty messy
		# if not gui.pl_update and gui.rendered_playlist_position != pctl.playlist_view_position:
		#     logging.warning("The playlist failed to render at the latest position!!!!")

		power += 1

		if pctl.playerCommandReady and tauon.thread_manager.player_lock.locked():
			try:
				tauon.thread_manager.player_lock.release()
			except RuntimeError as e:
				if str(e) == "release unlocked lock":
					logging.error("RuntimeError: Attempted to release already unlocked player_lock")  # noqa: TRY400
				else:
					logging.exception("Unknown RuntimeError trying to release player_lock")
			except Exception:
				logging.exception("Unknown exception trying to release player_lock")

		if gui.frame_callback_list:
			i = len(gui.frame_callback_list) - 1
			while i >= 0:
				if gui.frame_callback_list[i].test():
					gui.update = 1
					power = 1000
					del gui.frame_callback_list[i]
				i -= 1

		if tauon.animate_monitor_timer.get() < 1 or tauon.load_orders:
			if tauon.cursor_blink_timer.get() > 0.65:
				tauon.cursor_blink_timer.set()
				TextBox.cursor ^= True
				gui.update = 1

			if inp.k_input:
				tauon.cursor_blink_timer.set()
				TextBox.cursor = True

			sdl3.SDL_Delay(3)
			power = 1000

		if inp.mouse_wheel or inp.k_input or gui.pl_update or gui.update or tauon.top_panel.adds:  # or mouse_moved:
			power = 1000

		if prefs.art_bg and tauon.core_timer.get() < 3:
			power = 1000

		if inp.mouse_down and mouse_moved:
			power = 1000
			if gui.update_on_drag:
				gui.update += 1
			if gui.pl_update_on_drag:
				gui.pl_update += 1

		if pctl.wake_past_time and tauon.get_real_time() > pctl.wake_past_time:
			pctl.wake_past_time = 0
			power = 1000
			gui.update += 1

		if gui.level_update and not album_scroll_hold and not scroll_hold:
			power = 500

		# if gui.vis == 3 and (pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM)):
		# 	power = 500
		# 	if len(gui.spec2_buffers) > 0 and gui.spec2_timer.get() > 0.04:
		# 		gui.spec2_timer.set()
		# 		gui.level_update = True
		# 		vis_update = True
		# 	else:
		# 		sdl3.SDL_Delay(5)

		if not pctl.running:
			break

		if tauon.requested_raise:
			tauon.raise_window()
			tauon.requested_raise = False

		if pctl.playing_state != PlayingState.STOPPED:
			power += 400

		if power < 500:

			if (pctl.playing_state in (PlayingState.STOPPED, PlayingState.PAUSED)) and not tauon.load_orders and gui.update == 0 \
			and not tauon.gall_ren.queue and not tauon.transcode_list and not gui.frame_callback_list:
				pass
			else:
				tauon.sleep_timer.set()
			if tauon.sleep_timer.get() > 2:
				sdl3.SDL_WaitEventTimeout(None, 1000)
			continue
		power = 0

		gui.pl_update = min(gui.pl_update, 2)

		gui.new_playlist_cooldown = False

		if prefs.auto_extract and prefs.monitor_downloads:
			tauon.dl_mon.scan()

		if inp.mouse_down and not tauon.coll((2, 2, window_size[0] - 4, window_size[1] - 4)):
			#logging.info(sdl3.SDL_GetMouseState(None, None))
			if sdl3.SDL_GetGlobalMouseState(None, None) == 0:
				inp.mouse_down = False
				inp.mouse_up = True
				inp.quick_drag = False

		#logging.info(window_size)
		# if window_size[0] / window_size[1] == 16 / 9:
		#     logging.info('OK')
		# if window_size[0] / window_size[1] > 16 / 9:
		#     logging.info("A")

		if inp.key_meta:
			inp.input_text = ""
			inp.k_input = False
			inp.key_return_press = False
			inp.key_tab_press = False

		if inp.k_input:
			if inp.mouse_click or inp.right_click or inp.mouse_up:
				inp.last_click_location = copy.deepcopy(inp.click_location)
				inp.click_location = copy.deepcopy(inp.mouse_position)

			if inp.key_focused != 0:
				keymaps.hits.clear()

				# inp.d_mouse_click = False
				# inp.right_click = False
				# inp.level_2_right_click = False
				# inp.mouse_click = False
				# inp.middle_click = False
				inp.mouse_up = False
				inp.key_return_press = False
				inp.key_down_press = False
				inp.key_up_press = False
				inp.key_right_press = False
				inp.key_left_press = False
				inp.key_esc_press = False
				inp.key_del = False
				inp.backspace_press = 0
				inp.key_backspace_press = False
				inp.key_tab_press = False
				inp.key_c_press = False
				inp.key_v_press = False
				# inp.key_f_press = False
				inp.key_a_press = False
				inp.key_s_press = False
				# inp.key_t_press = False
				inp.key_z_press = False
				inp.key_x_press = False
				inp.key_home_press = False
				inp.key_end_press = False
				inp.mouse_wheel = 0
				pref_box.scroll = 0
				inp.input_text = ""
				inp.level_2_enter = False

		if c_yax != 0:
			if c_yax_timer.get() >= 0:
				if c_yax == -1:
					inp.key_up_press = True
				if c_yax == 1:
					inp.key_down_press = True
				c_yax_timer.force_set(-0.01)
				gui.delay_frame(0.02)
				inp.k_input = True
		if c_xax != 0:
			if c_xax_timer.get() >= 0:
				if c_xax == 1:
					pctl.seek_time(pctl.playing_time + 2)
				if c_xax == -1:
					pctl.seek_time(pctl.playing_time - 2)
				c_xax_timer.force_set(-0.01)
				gui.delay_frame(0.02)
				inp.k_input = True
		if c_xay != 0:
			if c_xay_timer.get() >= 0:
				if c_xay == -1:
					pctl.player_volume += 1
					pctl.player_volume = min(pctl.player_volume, 100)
					pctl.set_volume()
				if c_xay == 1:
					if pctl.player_volume > 1:
						pctl.player_volume -= 1
					else:
						pctl.player_volume = 0
					pctl.set_volume()
				c_xay_timer.force_set(-0.01)
				gui.delay_frame(0.02)
				inp.k_input = True

		if inp.k_input and inp.key_focused == 0:
			if gui.timed_lyrics_editing_now:
				keymaps.hits.clear()
			if keymaps.hits:
				n = 1
				while n < 10:
					if keymaps.test(f"jump-playlist-{n}"):
						if len(pctl.multi_playlist) > n - 1:
							pctl.switch_playlist(n - 1)
					n += 1

				if keymaps.test("cycle-playlist-left"):
					if ( gui.album_tab_mode and inp.key_left_press ):
						pass
					elif tauon.is_level_zero() or gui.quick_search_mode:
						pctl.cycle_playlist_pinned(1)
				if keymaps.test("cycle-playlist-right"):
					if ( gui.album_tab_mode and inp.key_right_press ):
						pass
					elif tauon.is_level_zero() or gui.quick_search_mode:
						pctl.cycle_playlist_pinned(-1)

				if keymaps.test("toggle-console"):
					tauon.console.toggle()

				if keymaps.test("toggle-fullscreen"):
					if not gui.fullscreen and gui.mode != 3:
						gui.fullscreen = True
						sdl3.SDL_SetWindowFullscreenMode(t_window, None)
						sdl3.SDL_SetWindowFullscreen(t_window, True)
					elif gui.fullscreen:
						gui.fullscreen = False
						sdl3.SDL_SetWindowFullscreen(t_window, False)

				if keymaps.test("playlist-toggle-breaks"):
					# Toggle force off folder break for viewed playlist
					pctl.multi_playlist[pctl.active_playlist_viewing].hide_title ^= 1
					gui.pl_update = 1

				if keymaps.test("find-playing-artist"):
					# standard_size()
					if len(pctl.track_queue) > 0:
						gui.quick_search_mode = True
						tauon.search_over.search_text.text = ""
						inp.input_text = pctl.playing_object().artist

				if keymaps.test("show-encode-folder"):
					tauon.open_encode_out()

				if keymaps.test("toggle-left-panel"):
					gui.lsp ^= True
					tauon.update_layout_do()

				if keymaps.test("toggle-last-left-panel"):
					tauon.toggle_left_last()
					tauon.update_layout_do()

				if keymaps.test("escape"):
					inp.key_esc_press = True

			if inp.key_ctrl_down:
				gui.pl_update += 1

			if mouse_enter_window:
				inp.key_return_press = False

			if gui.fullscreen and inp.key_esc_press:
				gui.fullscreen = False
				sdl3.SDL_SetWindowFullscreen(t_window, 0)

			# Disable keys for text cursor control
			if not gui.rename_folder_box and not tauon.rename_track_box.active and not gui.rename_playlist_box and not radiobox.active and not pref_box.enabled and not tauon.trans_edit_box.active and not gui.timed_lyrics_editing_now:
				if not gui.quick_search_mode and not tauon.search_over.active:
					if prefs.album_mode and gui.album_tab_mode \
							and not inp.key_ctrl_down \
							and not inp.key_meta \
							and not inp.key_lalt:
						if inp.key_left_press:
							gal_left = True
							inp.key_left_press = False
						if inp.key_right_press:
							gal_right = True
							inp.key_right_press = False
						if inp.key_up_press:
							gal_up = True
							inp.key_up_press = False
						if inp.key_down_press:
							gal_down = True
							inp.key_down_press = False

				if not tauon.search_over.active:
					if inp.key_del:
						close_all_menus()
						tauon.del_selected()

					# Arrow keys to change playlist
					if (inp.key_left_press or inp.key_right_press) and len(pctl.multi_playlist) > 1:
						gui.pl_update = 1
						gui.update += 1

				if keymaps.test("start"):
					if pctl.playing_time < 4:
						pctl.back()
					else:
						pctl.new_time = 0
						pctl.playing_time = 0
						pctl.decode_time = 0
						pctl.playerCommand = "seek"
						pctl.playerCommandReady = True

				if keymaps.test("goto-top"):
					pctl.playlist_view_position = 0
					logging.debug("Position changed by key")
					pctl.selected_in_playlist = 0
					gui.pl_update = 1

				if keymaps.test("goto-bottom"):
					n = len(pctl.default_playlist) - gui.playlist_view_length + 1
					n = max(n, 0)
					pctl.playlist_view_position = n
					logging.debug("Position changed by key")
					pctl.selected_in_playlist = len(pctl.default_playlist) - 1
					gui.pl_update = 1

			if not pref_box.enabled and not radiobox.active and not tauon.rename_track_box.active \
					and not gui.rename_folder_box \
					and not gui.rename_playlist_box and not tauon.search_over.active \
					and not gui.box_over and not tauon.trans_edit_box.active and not gui.timed_lyrics_editing_now:

				if gui.quick_search_mode:
					if keymaps.test("add-to-queue") and pctl.selected_ready():
						tauon.add_selected_to_queue()
						inp.input_text = ""
				else:
					if inp.key_c_press and inp.key_ctrl_down:
						gui.pl_update = 1
						tauon.s_copy()

					if inp.key_x_press and inp.key_ctrl_down:
						gui.pl_update = 1
						tauon.s_cut()

					if inp.key_v_press and inp.key_ctrl_down:
						gui.pl_update = 1
						tauon.paste()

					if keymaps.test("playpause"):
						pctl.play_pause()


			if inp.key_return_press and (gui.rename_folder_box or tauon.rename_track_box.active or radiobox.active):
				inp.key_return_press = False
				inp.level_2_enter = True

			if inp.key_ctrl_down and inp.key_z_press:
				tauon.undo.undo()

			if keymaps.test("quit"):
				tauon.exit("Quit keyboard shortcut pressed")

			if keymaps.test("testkey"):  # F7: test
				try:
					shutil.copy(tauon.milky.projectm.loaded_preset, tauon.user_directory / "presets")
				except:
					pass
				pass

			if gui.mode < 3:
				if keymaps.test("toggle-auto-theme"):
					prefs.colour_from_image ^= True
					if prefs.colour_from_image:
						tauon.show_message(_("Enabled auto theme"))
					else:
						tauon.show_message(_("Disabled auto theme"))
						gui.reload_theme = True
						gui.theme_temp_current = -1

				if keymaps.test("transfer-playtime-to"):
					if len(pctl.cargo) == 1 and tauon.copied_track is not None and -1 < pctl.selected_in_playlist < len(
							pctl.default_playlist):
						fr = pctl.get_track(tauon.copied_track)
						to = pctl.get_track(pctl.default_playlist[pctl.selected_in_playlist])

						fr_s = tauon.star_store.full_get(fr.index)
						to_s = tauon.star_store.full_get(to.index)

						fr_scr = fr.lfm_scrobbles
						to_scr = to.lfm_scrobbles

						tauon.undo.bk_playtime_transfer(fr, fr_s, fr_scr, to, to_s, to_scr)

						if to_s is None:
							to_s = StarRecord()
						if fr_s is None:
							fr_s = StarRecord()

						new = StarRecord()

						new.playtime = fr_s.playtime + to_s.playtime
						new.rating = fr_s.rating
						if to_s.rating > 0 and fr_s.rating == 0:
							new.rating = to_s.rating  # keep target rating
						to.lfm_scrobbles = fr.lfm_scrobbles

						tauon.star_store.remove(fr.index)
						tauon.star_store.remove(to.index)
						if new.playtime or new.rating:
							tauon.star_store.insert(to.index, new)

						tauon.copied_track = None
						gui.pl_update += 1
						logging.info("Transferred track stats!")
					elif tauon.copied_track is None:
						tauon.show_message(_("First select a source track by copying it into clipboard"))

				if keymaps.test("toggle-gallery"):
					tauon.toggle_album_mode()

				if keymaps.test("toggle-right-panel"):
					if gui.combo_mode:
						tauon.exit_combo()
					elif not prefs.album_mode:
						tauon.toggle_side_panel()
					else:
						tauon.toggle_album_mode()

				if keymaps.test("toggle-minimode"):
					tauon.set_mini_mode()
					gui.update += 1

				if keymaps.test("cycle-layouts"):
					if tauon.view_box.tracks():
						tauon.view_box.side(True)
					elif tauon.view_box.side():
						tauon.view_box.gallery1(True)
					elif tauon.view_box.gallery1():
						tauon.view_box.lyrics(True)
					else:
						tauon.view_box.tracks(True)

				if keymaps.test("cycle-layouts-reverse"):
					if tauon.view_box.tracks():
						tauon.view_box.lyrics(True)
					elif tauon.view_box.lyrics():
						tauon.view_box.gallery1(True)
					elif tauon.view_box.gallery1():
						tauon.view_box.side(True)
					else:
						tauon.view_box.tracks(True)

				if keymaps.test("toggle-columns"):
					tauon.view_box.col(True)

				if keymaps.test("toggle-artistinfo"):
					tauon.view_box.artist_info(True)

				if keymaps.test("toggle-showcase"):
					tauon.view_box.lyrics(True)

				if keymaps.test("toggle-gallery-keycontrol"):
					tauon.toggle_gallery_keycontrol()

				if keymaps.test("toggle-show-art"):
					tauon.toggle_side_art()

			elif gui.mode == 3:
				if keymaps.test("toggle-minimode"):
					tauon.restore_full_mode()
					gui.update += 1

			inp.ab_click = False

			if keymaps.test("new-playlist"):
				tauon.new_playlist()

			if keymaps.test("edit-generator"):
				tauon.edit_generator_box(pctl.active_playlist_viewing)

			if keymaps.test("new-generator-playlist"):
				tauon.new_playlist()
				tauon.edit_generator_box(pctl.active_playlist_viewing)

			if keymaps.test("delete-playlist"):
				pctl.delete_playlist(pctl.active_playlist_viewing)

			if keymaps.test("delete-playlist-force"):
				pctl.delete_playlist(pctl.active_playlist_viewing, force=True)

			if keymaps.test("rename-playlist"):
				if gui.radio_view:
					tauon.rename_playlist(pctl.radio_playlist_viewing)
				else:
					tauon.rename_playlist(pctl.active_playlist_viewing)
				tauon.rename_playlist_box.x = 60 * gui.scale
				tauon.rename_playlist_box.y = 60 * gui.scale

			# Transfer click register to menus
			if inp.mouse_click:
				for instance in Menu.instances:
					if instance.active:
						instance.click()
						inp.mouse_click = False
						inp.ab_click = True
				if tauon.view_box.active:
					tauon.view_box.clicked = True

			if inp.mouse_click and (
					prefs.show_nag or gui.box_over or radiobox.active or tauon.search_over.active or gui.rename_folder_box or gui.rename_playlist_box or tauon.rename_track_box.active or tauon.view_box.active or tauon.trans_edit_box.active):  # and not gui.message_box:
				inp.mouse_click = False
				gui.level_2_click = True
			else:
				gui.level_2_click = False

			if gui.track_box and inp.mouse_click:
				w = 540
				h = 240
				x = int(window_size[0] / 2) - int(w / 2)
				y = int(window_size[1] / 2) - int(h / 2)
				if tauon.coll([x, y, w, h]):
					inp.mouse_click = False
					gui.level_2_click = True

			if inp.right_click:
				inp.level_2_right_click = True

			if pref_box.enabled:
				if pref_box.inside():
					if inp.mouse_click:  # and not gui.message_box:
						pref_box.click = True
						inp.mouse_click = False
					if inp.right_click:
						inp.right_click = False
						pref_box.right_click = True

					pref_box.scroll = inp.mouse_wheel
					inp.mouse_wheel = 0
				else:
					if inp.mouse_click:
						inp.mouse_click = False
						pref_box.close()
					if inp.right_click:
						inp.right_click = False
						pref_box.close()
					if pref_box.lock is False:
						pass

			if inp.right_click and (
					radiobox.active or tauon.rename_track_box.active or gui.rename_playlist_box or gui.rename_folder_box or tauon.search_over.active):
				inp.right_click = False

			if inp.mouse_wheel != 0:
				gui.update += 1
			if inp.mouse_down is True:
				gui.update += 1

			if keymaps.test("pagedown"):  # key_PGD:
				if len(pctl.default_playlist) > 10:
					pctl.playlist_view_position += gui.playlist_view_length - 4
					if pctl.playlist_view_position > len(pctl.default_playlist):
						pctl.playlist_view_position = len(pctl.default_playlist) - 2
					gui.pl_update = 1
					pctl.selected_in_playlist = pctl.playlist_view_position
					logging.debug("Position changed by page key")
					gui.shift_selection.clear()
			if keymaps.test("pageup"):
				if len(pctl.default_playlist) > 0:
					pctl.playlist_view_position -= gui.playlist_view_length - 4
					pctl.playlist_view_position = max(pctl.playlist_view_position, 0)
					gui.pl_update = 1
					pctl.selected_in_playlist = pctl.playlist_view_position
					logging.debug("Position changed by page key")
					gui.shift_selection.clear()

			if gui.quick_search_mode is False and tauon.rename_track_box.active is False and gui.rename_folder_box is False and gui.rename_playlist_box is False and not pref_box.enabled and not radiobox.active:
				if keymaps.test("info-playing"):
					if pctl.selected_in_playlist < len(pctl.default_playlist):
						pctl.r_menu_index = pctl.get_track(pctl.default_playlist[pctl.selected_in_playlist]).index
						gui.track_box = True

				if keymaps.test("info-show"):
					if pctl.selected_in_playlist < len(pctl.default_playlist):
						pctl.r_menu_index = pctl.get_track(pctl.default_playlist[pctl.selected_in_playlist]).index
						gui.track_box = True

				# These need to be disabled when text fields are active
				if not tauon.search_over.active and not gui.box_over and not radiobox.active and not gui.rename_folder_box and not tauon.rename_track_box.active and not gui.rename_playlist_box and not tauon.trans_edit_box.active and not gui.timed_lyrics_editing_now:
					if keymaps.test("advance"):
						inp.key_right_press = False
						pctl.advance()

					if keymaps.test("previous"):
						inp.key_left_press = False
						pctl.back()

					if inp.key_a_press and inp.key_ctrl_down:
						gui.pl_update = 1
						gui.shift_selection = range(len(pctl.default_playlist)) # TODO(Martin): This can under some circumstances end up doing a range.clear()

					if keymaps.test("revert"):
						pctl.revert()

					if keymaps.test("random-track-start"):
						pctl.advance(rr=True)

					if keymaps.test("vol-down"):
						if pctl.player_volume > 3:
							pctl.player_volume -= 3
						else:
							pctl.player_volume = 0
						pctl.set_volume()

					if keymaps.test("toggle-mute"):
						pctl.toggle_mute()

					if keymaps.test("vol-up"):
						pctl.player_volume += 3
						pctl.player_volume = min(pctl.player_volume, 100)
						pctl.set_volume()

					if keymaps.test("shift-down") and len(pctl.default_playlist) > 0:
						gui.pl_update += 1
						if pctl.selected_in_playlist > len(pctl.default_playlist) - 1:
							pctl.selected_in_playlist = 0

						if not gui.shift_selection:
							gui.shift_selection.append(pctl.selected_in_playlist)
						if pctl.selected_in_playlist < len(pctl.default_playlist) - 1:
							r = pctl.selected_in_playlist
							pctl.selected_in_playlist += 1
							if pctl.selected_in_playlist not in gui.shift_selection:
								gui.shift_selection.append(pctl.selected_in_playlist)
							else:
								gui.shift_selection.remove(r)

					if keymaps.test("shift-up") and pctl.selected_in_playlist > -1:
						gui.pl_update += 1
						pctl.selected_in_playlist = min(pctl.selected_in_playlist, len(pctl.default_playlist) - 1)

						if not gui.shift_selection:
							gui.shift_selection.append(pctl.selected_in_playlist)
						if pctl.selected_in_playlist > 0:
							r = pctl.selected_in_playlist
							pctl.selected_in_playlist -= 1
							if pctl.selected_in_playlist not in gui.shift_selection:
								gui.shift_selection.insert(0, pctl.selected_in_playlist)
							else:
								gui.shift_selection.remove(r)

					if keymaps.test("toggle-shuffle"):
						# pctl.random_mode ^= True
						tauon.toggle_random()

					if keymaps.test("goto-playing"):
						pctl.show_current()
					if keymaps.test("goto-previous"):
						if pctl.queue_step > 1:
							pctl.show_current(index=pctl.track_queue[pctl.queue_step - 1])

					if keymaps.test("toggle-repeat"):
						tauon.toggle_repeat()

					if keymaps.test("random-track"):
						tauon.random_track()

					if keymaps.test("random-album"):
						tauon.random_album()

					if keymaps.test("opacity-up"):
						prefs.window_opacity += .05
						prefs.window_opacity = min(prefs.window_opacity, 1)
						sdl3.SDL_SetWindowOpacity(t_window, prefs.window_opacity)

					if keymaps.test("opacity-down"):
						prefs.window_opacity -= .05
						prefs.window_opacity = max(prefs.window_opacity, .30)
						sdl3.SDL_SetWindowOpacity(t_window, prefs.window_opacity)

					if keymaps.test("seek-forward"):
						pctl.seek_time(pctl.playing_time + prefs.seek_interval)

					if keymaps.test("seek-back"):
						pctl.seek_time(pctl.playing_time - prefs.seek_interval)

					if keymaps.test("play"):
						pctl.play()

					if keymaps.test("stop"):
						pctl.stop()

					if keymaps.test("pause"):
						pctl.pause_only()

					if keymaps.test("love-playing"):
						tauon.bar_love(notify=True)

					if keymaps.test("love-selected"):
						tauon.select_love(notify=True)

					if keymaps.test("search-lyrics-selected"):
						if pctl.selected_ready():
							track = pctl.get_track(pctl.default_playlist[pctl.selected_in_playlist])
							if track.lyrics:
								tauon.show_message(_("Track already has lyrics"))
							else:
								tauon.get_lyric_wiki(track)

					if keymaps.test("substitute-search-selected"):
						if pctl.selected_ready():
							tauon.show_sub_search(pctl.get_track(pctl.default_playlist[pctl.selected_in_playlist]))

					if keymaps.test("global-search"):
						tauon.activate_search_overlay()

					if keymaps.test("add-to-queue") and pctl.selected_ready():
						tauon.add_selected_to_queue()

					if keymaps.test("clear-queue"):
						tauon.clear_queue()

					if keymaps.test("regenerate-playlist"):
						tauon.regenerate_playlist(pctl.active_playlist_viewing)

			if keymaps.test("cycle-theme"):
				gui.reload_theme = True
				gui.theme_temp_current = -1
				gui.temp_themes.clear()
				prefs.theme += 1

			if keymaps.test("cycle-theme-reverse"):
				gui.theme_temp_current = -1
				gui.temp_themes.clear()
				pref_box.previous_theme()

			if keymaps.test("reload-theme"):
				gui.reload_theme = True

		# if inp.mouse_position[1] < 1:
		#     inp.mouse_down = False

		if inp.mouse_down is False:
			scroll_hold = False

		# if focused is True:
		#     inp.mouse_down = False

		if inp.media_key:
			if inp.media_key == "Play":
				if pctl.playing_state == PlayingState.STOPPED:
					pctl.play()
				else:
					pctl.pause()
			elif inp.media_key == "Pause":
				pctl.pause_only()
			elif inp.media_key == "Stop":
				pctl.stop()
			elif inp.media_key == "Next":
				pctl.advance()
			elif inp.media_key == "Previous":
				pctl.back()

			elif inp.media_key == "Rewind":
				pctl.seek_time(pctl.playing_time - 10)
			elif inp.media_key == "FastForward":
				pctl.seek_time(pctl.playing_time + 10)
			elif inp.media_key == "Repeat":
				tauon.toggle_repeat()
			elif inp.media_key == "Shuffle":
				tauon.toggle_random()

			inp.media_key = ""

		if len(tauon.load_orders) > 0:
			pctl.loading_in_progress = True
			pctl.after_import_flag = True
			tauon.thread_manager.ready("worker")
			if tauon.loaderCommand == LoaderCommand.NONE:

				# Filter out files matching CUE filenames
				# This isn't the only mechanism that does this. This one helps in the situation
				# where the user drags and drops multiple files at onec. CUEs in folders are handled elsewhere
				if len(tauon.load_orders) > 1:
					for order in tauon.load_orders:
						if order.stage == 0 and order.target.endswith(".cue"):
							for order2 in tauon.load_orders:
								if not order2.target.endswith(".cue") and\
										os.path.splitext(order2.target)[0] == os.path.splitext(order.target)[0] and\
										os.path.isfile(order2.target):
									order2.stage = -1
					for i in reversed(range(len(tauon.load_orders))):
						order = tauon.load_orders[i]
						if order.stage == -1:
							del tauon.load_orders[i]

				# Prepare loader thread with load order
				for order in tauon.load_orders:
					if order.stage == 0:
						order.target = order.target.replace("\\", "/")
						order.stage = 1
						if os.path.isdir(order.target):
							tauon.loaderCommand = LoaderCommand.FOLDER
						else:
							tauon.loaderCommand = LoaderCommand.FILE
							if order.target.endswith(".xspf"):
								gui.to_got = "xspf"
								gui.to_get = 0
							else:
								gui.to_got = 1
								gui.to_get = 1
						tauon.loaderCommandReady = True
						tauon.thread_manager.ready("worker")
						break

		elif pctl.loading_in_progress is True:
			pctl.loading_in_progress = False
			pctl.notify_change()

		if tauon.loaderCommand == LoaderCommand.DONE:
			tauon.loaderCommand = LoaderCommand.NONE
			gui.update += 1
			# gui.pl_update = 1
			# pctl.loading_in_progress = False

		if gui.update_layout:
			tauon.update_layout_do()
			gui.update_layout = False

		# if tauon.worker_save_state and\
		# 		not gui.pl_pulse and\
		# 		not pctl.loading_in_progress and\
		# 		not tauon.to_scan and\
		# 		not tauon.plex.scanning and\
		# 		not tauon.cm_clean_db and\
		# 		not tauon.lastfm.scanning_friends and\
		# 		not tauon.move_in_progress:
		# 	tauon.save_state()
		# 	cue_list.clear()
		# 	tauon.worker_save_state = False

		# -----------------------------------------------------
		# THEME SWITCHER--------------------------------------------------------------------

		if gui.reload_theme is True:
			gui.pl_update = 1
			theme_files = get_themes(dirs)

			if prefs.theme > len(theme_files):  # sic
				prefs.theme = 0

			if prefs.theme > 0:
				theme_number = prefs.theme - 1
				try:
					colours.column_colours.clear()
					colours.column_colours_playing.clear()

					theme_item = theme_files[theme_number]

					gui.theme_name = theme_item[1]
					colours.lm = False
					colours.__init__()

					load_theme(colours, Path(theme_item[0]))
					tauon.deco.load(colours.deco)
					logging.info(f"Applying theme: {gui.theme_name}")

					if colours.lm:
						gui.info_icon.colour = ColourRGBA(60, 60, 60, 255)
					else:
						gui.info_icon.colour = ColourRGBA(61, 247, 163, 255)

					if colours.lm:
						gui.folder_icon.colour = ColourRGBA(255, 190, 80, 255)
					else:
						gui.folder_icon.colour = ColourRGBA(244, 220, 66, 255)

					if colours.lm:
						gui.settings_icon.colour = ColourRGBA(85, 187, 250, 255)
					else:
						gui.settings_icon.colour = ColourRGBA(232, 200, 96, 255)

					if colours.lm:
						gui.radiorandom_icon.colour = ColourRGBA(120, 200, 120, 255)
					else:
						gui.radiorandom_icon.colour = ColourRGBA(153, 229, 133, 255)

				except Exception:
					logging.exception("Error loading theme file")
					tauon.show_message(_("Error loading theme file"), "", mode="warning")

			if prefs.theme == 0:
				gui.theme_name = "Mindaro"
				logging.info("Applying default theme: Mindaro")
				colours.lm = False
				colours.__init__()
				colours.post_config()
				tauon.deco.unload()

			if prefs.transparent_mode:
				colours.apply_transparency()

			prefs.theme_name = gui.theme_name

			#logging.info("Theme number: " + str(prefs.theme))
			gui.reload_theme = False
			ddt.text_background_colour = colours.playlist_panel_background

		# ---------------------------------------------------------------------------------------------------------
		# GUI DRAWING------
		#logging.info(gui.update)
		#logging.info(gui.lowered)
		if gui.mode == 3:
			gui.pl_update = 0

		if gui.pl_update and not gui.update:
			gui.update = 1

		if gui.update > 0 and not resize_mode:
			gui.update = min(gui.update, 2)

			if reset_render:
				logging.info("Reset render targets!")
				tauon.clear_img_cache(delete_disk=False)
				ddt.clear_text_cache()
				for item in WhiteModImageAsset.assets:
					item.reload()
				reset_render = False

			sdl3.SDL_SetRenderTarget(renderer, None)
			sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
			sdl3.SDL_SetRenderDrawColor(
				renderer, 0, 0,
				0, 0)
			sdl3.SDL_RenderClear(renderer)
			sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
			sdl3.SDL_RenderClear(renderer)
			sdl3.SDL_SetRenderTarget(renderer, gui.main_texture)
			sdl3.SDL_RenderClear(renderer)

			# tauon.perf_timer.set()
			gui.update_on_drag = False
			gui.pl_update_on_drag = False

			# inp.mouse_position[0], inp.mouse_position[1] = tauon.input_sdl.mouse()
			gui.showed_title = False

			if not gui.ext_drop_mode and not gui.mouse_in_window and not tauon.bottom_bar1.volume_bar_being_dragged and not tauon.bottom_bar1.volume_hit and not tauon.bottom_bar1.seek_hit:
				inp.mouse_position[0] = -300.
				inp.mouse_position[1] = -300.

			if gui.clear_image_cache_next:
				gui.clear_image_cache_next -= 1
				tauon.album_art_gen.clear_cache()
				tauon.style_overlay.radio_meta = None
				if prefs.art_bg:
					tauon.thread_manager.ready("style")

			tauon.fields.clear()
			gui.cursor_want = 0

			gui.layer_focus = 0

			if inp.mouse_click or inp.mouse_wheel or inp.right_click:
				inp.mouse_position[0], inp.mouse_position[1] = tauon.input_sdl.mouse()

			if inp.mouse_click:
				n_click_time = time.time()
				if n_click_time - gui.click_time < 0.42:
					inp.d_mouse_click = True
				gui.click_time = n_click_time

				# Don't register bottom level click when closing message box
				if gui.message_box and pref_box.enabled and not inp.key_focused and not tauon.coll(tauon.message_box.get_rect()):
					inp.mouse_click = False
					gui.message_box = False

			# Enable the garbage collector (since we disabled it during startup)
			if ggc > 0:
				if ggc == 2:
					ggc = 1
				elif ggc == 1:
					ggc = 0
					gbc.enable()
					#logging.info("Enabling garbage collecting")

			if gui.mode in (1, 2):

				ddt.text_background_colour = colours.playlist_panel_background

				# Side Bar Draging----------

				if not inp.mouse_down:
					gui.side_drag = False

				rect = (window_size[0] - gui.rspw - 5 * gui.scale, gui.panelY, 12 * gui.scale,
						window_size[1] - gui.panelY - gui.panelBY)
				tauon.fields.add(rect)

				if (tauon.coll(rect) or gui.side_drag is True) \
					and tauon.rename_track_box.active is False \
					and radiobox.active is False \
					and gui.rename_playlist_box is False \
					and gui.message_box is False \
					and pref_box.enabled is False \
					and gui.track_box is False \
					and not gui.rename_folder_box \
					and not gui.timed_lyrics_editing_now \
					and not Menu.active \
					and (gui.rsp or prefs.album_mode) \
					and not tauon.artist_info_scroll.held \
					and gui.layer_focus == 0 and gui.show_playlist:

					if gui.side_drag is True:
						draw_sep_hl = True
						# gui.update += 1
						gui.update_on_drag = True

					if inp.mouse_click:
						gui.side_drag = True
						gui.side_bar_drag_source = inp.mouse_position[0]
						gui.side_bar_drag_original = gui.rspw

					if not inp.quick_drag:
						gui.cursor_want = 1

				# side drag update
				if gui.side_drag:

					offset = gui.side_bar_drag_source - inp.mouse_position[0]

					target = gui.side_bar_drag_original + offset

					# Snap to album mode position if close
					if not prefs.album_mode and prefs.side_panel_layout == 1:
						if abs(target - gui.pref_gallery_w) < 35 * gui.scale:
							target = gui.pref_gallery_w

					# Reset max ratio if drag drops below ratio width
					if prefs.side_panel_layout == 0:
						if target < round((window_size[1] - gui.panelY - gui.panelBY) * gui.art_aspect_ratio):
							gui.art_max_ratio_lock = gui.art_aspect_ratio

						max_w = round(((window_size[
											1] - gui.panelY - gui.panelBY - 17 * gui.scale) * gui.art_max_ratio_lock) + 17 * gui.scale)
						# 17 here is the art box inset value

					else:
						max_w = window_size[0]

					if not prefs.album_mode and target > max_w - 12 * gui.scale:
						target = max_w
						gui.rspw = target
						gui.rsp_full_lock = True

					else:
						gui.rspw = target
						gui.rsp_full_lock = False

					if prefs.album_mode:
						pass
						# gui.rspw = target

					if prefs.album_mode and gui.rspw < tauon.album_mode_art_size + 50 * gui.scale:
						target = tauon.album_mode_art_size + 50 * gui.scale

					# Prevent side bar getting too small
					target = max(target, 120 * gui.scale)

					# Remember size for this view mode
					if not prefs.album_mode:
						gui.pref_rspw = target
					else:
						gui.pref_gallery_w = target

					tauon.update_layout_do()

				# ALBUM GALLERY RENDERING:
				# Gallery view
				# C-AR

				if prefs.album_mode:
					try:
						# Arrow key input
						if gal_right:
							gal_right = False
							tauon.gal_jump_select(False, 1)
							tauon.goto_album(pctl.selected_in_playlist)
							pctl.playlist_view_position = pctl.selected_in_playlist
							logging.debug("Position changed by gallery key press")
							gui.pl_update = 1
						if gal_down:
							gal_down = False
							tauon.gal_jump_select(False, row_len)
							tauon.goto_album(pctl.selected_in_playlist, down=True)
							pctl.playlist_view_position = pctl.selected_in_playlist
							logging.debug("Position changed by gallery key press")
							gui.pl_update = 1
						if gal_left:
							gal_left = False
							tauon.gal_jump_select(True, 1)
							tauon.goto_album(pctl.selected_in_playlist)
							pctl.playlist_view_position = pctl.selected_in_playlist
							logging.debug("Position changed by gallery key press")
							gui.pl_update = 1
						if gal_up:
							gal_up = False
							tauon.gal_jump_select(True, row_len)
							tauon.goto_album(pctl.selected_in_playlist)
							pctl.playlist_view_position = pctl.selected_in_playlist
							logging.debug("Position changed by gallery key press")
							gui.pl_update = 1

						w = gui.rspw

						if window_size[0] < 750 * gui.scale:
							w = window_size[0] - 20 * gui.scale
							if gui.lsp:
								w -= gui.lspw

						x = window_size[0] - w
						# sx = x
						# sw = w
						h = window_size[1] - gui.panelY - gui.panelBY

						if not gui.show_playlist and inp.mouse_click:
							left = 0
							if gui.lsp:
								left = gui.lspw

							if left < inp.mouse_position[0] < left + 20 * gui.scale and window_size[1] - gui.panelBY > \
									inp.mouse_position[1] > gui.panelY:
								tauon.toggle_album_mode()
								inp.mouse_click = False
								inp.mouse_down = False

						rect = [x, gui.panelY, w, h]
						ddt.rect(rect, colours.gallery_background)

						# ddt.rect_r(rect, [255, 0, 0, 200], True)

						area_x = w + 38 * gui.scale
						# area_x = w - 40 * gui.scale

						row_len = int((area_x - gui.album_h_gap) / (tauon.album_mode_art_size + gui.album_h_gap))

						#logging.info(row_len)

						compact = 40 * gui.scale
						a_offset = 7 * gui.scale

						l_area = x
						r_area = w
						# c_area = r_area // 2 + l_area

						ddt.text_background_colour = colours.gallery_background

						line1_colour = colours.gallery_artist_line
						line2_colour = colours.grey(240)  # colours.side_bar_line1

						if colours.side_panel_background != colours.gallery_background:
							line2_colour = ColourRGBA(240, 240, 240, 255)
							line1_colour = alpha_mod(ColourRGBA(20, 220, 220, 255), 120)

						if test_lumi(colours.gallery_background) < 0.5 or (prefs.use_card_style and colours.lm):
							line1_colour = colours.grey(80)
							line2_colour = colours.grey(40)

						if row_len == 0:
							row_len = 1

						dev = int((r_area - compact) / (row_len + 0))

						render_pos = 0
						album_on = 0

						max_scroll = round(
							(math.ceil((len(tauon.album_dex)) / row_len) - 1) * (tauon.album_mode_art_size + gui.album_v_gap)) - round(
							50 * gui.scale)

						# Mouse wheel scrolling
						if not tauon.search_over.active and not radiobox.active \
								and inp.mouse_position[0] > window_size[0] - w and gui.panelY < inp.mouse_position[1] < window_size[
							1] - gui.panelBY:

							if inp.mouse_wheel != 0:
								tauon.scroll_gallery_hide_timer.set()
								gui.frame_callback_list.append(TestTimer(0.9))

							if prefs.gallery_row_scroll:
								gui.album_scroll_px -= inp.mouse_wheel * (tauon.album_mode_art_size + gui.album_v_gap)  # 90
							else:
								gui.album_scroll_px -= inp.mouse_wheel * prefs.gallery_scroll_wheel_px

							if gui.album_scroll_px < round(gui.album_v_slide_value * -1):
								gui.album_scroll_px = round(gui.album_v_slide_value * -1)
								if tauon.album_dex:
									tauon.gallery_pulse_top.pulse()

							if gui.album_scroll_px > max_scroll:
								gui.album_scroll_px = max_scroll
								gui.album_scroll_px = max(gui.album_scroll_px, round(gui.album_v_slide_value * -1))

						rect = (
						gui.gallery_scroll_field_left, gui.panelY, window_size[0] - gui.gallery_scroll_field_left - 2, h)

						card_mode = False
						if prefs.use_card_style and colours.lm and gui.gallery_show_text:
							card_mode = True

						rect = (window_size[0] - 40 * gui.scale, gui.panelY, 38 * gui.scale, h)
						tauon.fields.add(rect)

						# Show scroll area
						if tauon.coll(rect) or tauon.gallery_scroll.held or tauon.scroll_gallery_hide_timer.get() < 0.9 or gui.album_tab_mode:
							if tauon.gallery_scroll.held:
								while len(tauon.gall_ren.queue) > 2:
									tauon.gall_ren.queue.pop()

							# Draw power bar button
							if gui.pt == 0 and gui.power_bar is not None and len(gui.power_bar) > 3:
								rect = (window_size[0] - (15 + 20) * gui.scale, gui.panelY + 3 * gui.scale, 18 * gui.scale,
										24 * gui.scale)
								tauon.fields.add(rect)
								colour = ColourRGBA(255, 255, 255, 35)
								if colours.lm:
									colour = ColourRGBA(0, 0, 0, 30)
								if tauon.coll(rect) and not tauon.gallery_scroll.held:
									colour = ColourRGBA(255, 220, 100, 245)
									if colours.lm:
										colour = ColourRGBA(250, 100, 0, 255)
									if inp.mouse_click:
										gui.pt = 1

								gui.power_bar_icon.render(rect[0] + round(5 * gui.scale), rect[1] + round(3 * gui.scale), colour)

							# Draw scroll bar
							if gui.pt == 0:
								gui.album_scroll_px = tauon.gallery_scroll.draw(
									window_size[0] - 16 * gui.scale, gui.panelY,
									15 * gui.scale,
									window_size[1] - (gui.panelY + gui.panelBY),
									gui.album_scroll_px + gui.album_v_slide_value,
									max_scroll + gui.album_v_slide_value,
									jump_distance=1400 * gui.scale,
									r_click=inp.right_click,
									extend_field=15 * gui.scale) - gui.album_v_slide_value

						if gui.last_row != row_len:
							gui.last_row = row_len

							if pctl.selected_in_playlist < len(pctl.playing_playlist()):
								tauon.goto_album(pctl.selected_in_playlist)
							# else:
							# 	tauon.goto_album(pctl.playlist_playing_position)

						extend = 0
						if card_mode:  # gui.gallery_show_text:
							extend = 40 * gui.scale

						# Process inputs first
						if (inp.mouse_click or inp.right_click or inp.middle_click or inp.mouse_down or inp.mouse_up) and pctl.default_playlist:
							while render_pos < gui.album_scroll_px + window_size[1]:
								if gui.b_info_bar and render_pos > gui.album_scroll_px + b_info_y:
									break

								if render_pos < gui.album_scroll_px - tauon.album_mode_art_size - gui.album_v_gap:
									# Skip row
									render_pos += tauon.album_mode_art_size + gui.album_v_gap
									album_on += row_len
								else:
									# render row
									y = render_pos - gui.album_scroll_px
									row_x = 0
									for a in range(row_len):
										if album_on > len(tauon.album_dex) - 1:
											break

										x = (l_area + dev * a) - int(tauon.album_mode_art_size / 2) + int(dev / 2) + int(
											compact / 2) - a_offset

										if tauon.album_dex[album_on] > len(pctl.default_playlist):
											break

										rect = (x, y, tauon.album_mode_art_size, tauon.album_mode_art_size + extend * gui.scale)
										# tauon.fields.add(rect)
										m_in = tauon.coll(rect) and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY

										# if m_in:
										#     ddt.rect_r((x - 7, y - 7, tauon.album_mode_art_size + 14, tauon.album_mode_art_size + extend + 55), [80, 80, 80, 80], True)

										# Quick drag and drop
										if inp.mouse_up and (gui.playlist_hold and m_in) and not gui.side_drag and gui.shift_selection:
											info = tauon.get_album_info(tauon.album_dex[album_on])
											if info[1]:
												track_position = info[1][0]

												if track_position > gui.shift_selection[0]:
													track_position = info[1][-1] + 1

												ref = []
												for item in gui.shift_selection:
													ref.append(pctl.default_playlist[item])

												for item in gui.shift_selection:
													pctl.default_playlist[item] = "old"

												for item in gui.shift_selection:
													pctl.default_playlist.insert(track_position, "new")

												for b in reversed(range(len(pctl.default_playlist))):
													if pctl.default_playlist[b] == "old":
														del pctl.default_playlist[b]
												gui.shift_selection = []
												for b in range(len(pctl.default_playlist)):
													if pctl.default_playlist[b] == "new":
														gui.shift_selection.append(b)
														pctl.default_playlist[b] = ref.pop(0)

												pctl.selected_in_playlist = gui.shift_selection[0]
												gui.pl_update += 1
												gui.playlist_hold = False

												tauon.reload_albums(True)
												pctl.notify_change()
										elif not gui.side_drag and tauon.is_level_zero():
											if coll_point(inp.click_location, rect) and gui.panelY < inp.mouse_position[1] < \
													window_size[1] - gui.panelBY:
												info = tauon.get_album_info(tauon.album_dex[album_on])

												if m_in and inp.mouse_up and prefs.gallery_single_click:
													if tauon.is_level_zero() and gui.d_click_ref == tauon.album_dex[album_on]:
														if info[0] == 1 and pctl.playing_state == PlayingState.PAUSED:
															pctl.play()
														elif info[0] == 1 and pctl.playing_state != PlayingState.STOPPED:
															pctl.playlist_view_position = tauon.album_dex[album_on]
															logging.debug("Position changed by gallery click")
														else:
															pctl.playlist_view_position = tauon.album_dex[album_on]
															logging.debug("Position changed by gallery click")
															pctl.jump(pctl.default_playlist[tauon.album_dex[album_on]], tauon.album_dex[album_on])
														pctl.show_current()
												elif inp.mouse_down and not m_in:
													info = tauon.get_album_info(tauon.album_dex[album_on])
													inp.quick_drag = True
													if not tauon.pl_is_locked(pctl.active_playlist_viewing) or inp.key_shift_down:
														gui.playlist_hold = True
													gui.shift_selection = info[1]
													gui.pl_update += 1
													inp.click_location = [0, 0]

										if m_in:
											info = tauon.get_album_info(tauon.album_dex[album_on])
											if inp.mouse_click:
												if prefs.gallery_single_click:
													gui.d_click_ref = tauon.album_dex[album_on]
												else:
													if tauon.d_click_timer.get() < 0.5 and gui.d_click_ref == tauon.album_dex[album_on]:
														if info[0] == 1 and pctl.playing_state == PlayingState.PAUSED:
															pctl.play()
														elif info[0] == 1 and pctl.playing_state != PlayingState.STOPPED:
															pctl.playlist_view_position = tauon.album_dex[album_on]
															logging.debug("Position changed by gallery click")
														else:
															pctl.playlist_view_position = tauon.album_dex[album_on]
															logging.debug("Position changed by gallery click")
															pctl.jump(pctl.default_playlist[tauon.album_dex[album_on]], tauon.album_dex[album_on])
													else:
														gui.d_click_ref = tauon.album_dex[album_on]
														tauon.d_click_timer.set()

													pctl.playlist_view_position = tauon.album_dex[album_on]
													logging.debug("Position changed by gallery click")
													pctl.selected_in_playlist = tauon.album_dex[album_on]
													gui.pl_update += 1
											elif inp.middle_click and tauon.is_level_zero():
												# Middle click to add album to queue
												if inp.key_ctrl_down:
													# Add to queue ungrouped
													album = tauon.get_album_info(tauon.album_dex[album_on])[1]
													for item in album:
														pctl.force_queue.append(
															queue_item_gen(pctl.default_playlist[item], item, pctl.pl_to_id(
																pctl.active_playlist_viewing)))
													tauon.queue_timer_set(plural=True)
													if prefs.stop_end_queue:
														pctl.stop_mode = StopMode.OFF
												else:
													# Add to queue grouped
													tauon.add_album_to_queue(pctl.default_playlist[tauon.album_dex[album_on]])
											elif inp.right_click:
												if pctl.quick_add_target:
													pl = pctl.id_to_pl(pctl.quick_add_target)
													if pl is not None:
														parent = pctl.get_track(
															pctl.default_playlist[tauon.album_dex[album_on]]).parent_folder_path
														# remove from target pl
														if pctl.default_playlist[tauon.album_dex[album_on]] in pctl.multi_playlist[pl].playlist_ids:
															for i in reversed(range(len(pctl.multi_playlist[pl].playlist_ids))):
																if pctl.get_track(pctl.multi_playlist[pl].playlist_ids[i]).parent_folder_path == parent:
																	del pctl.multi_playlist[pl].playlist_ids[i]
														else:
															# add
															for i in range(len(pctl.default_playlist)):
																if pctl.get_track(pctl.default_playlist[i]).parent_folder_path == parent:
																	pctl.multi_playlist[pl].playlist_ids.append(pctl.default_playlist[i])
													tauon.reload_albums(True)
												else:
													pctl.selected_in_playlist = tauon.album_dex[album_on]
													# playlist_position = pctl.playlist_selected
													gui.shift_selection = [pctl.selected_in_playlist]
													gallery_menu.activate(pctl.default_playlist[pctl.selected_in_playlist])
													pctl.r_menu_position = pctl.selected_in_playlist

													gui.shift_selection = []
													u = pctl.selected_in_playlist
													while u < len(pctl.default_playlist) and pctl.master_library[
														pctl.default_playlist[u]].parent_folder_path == \
															pctl.master_library[
																pctl.default_playlist[pctl.selected_in_playlist]].parent_folder_path:
														gui.shift_selection.append(u)
														u += 1
													pctl.render_playlist()

										album_on += 1

									if album_on > len(tauon.album_dex):
										break
									render_pos += tauon.album_mode_art_size + gui.album_v_gap

						render_pos = 0
						album_on = 0
						album_count = 0

						if not pref_box.enabled or inp.mouse_wheel != 0:
							gui.first_in_grid = None

						# Render album grid
						while render_pos < gui.album_scroll_px + window_size[1] and pctl.default_playlist:
							if gui.b_info_bar and render_pos > gui.album_scroll_px + b_info_y:
								break

							if render_pos < gui.album_scroll_px - tauon.album_mode_art_size - gui.album_v_gap:
								# Skip row
								render_pos += tauon.album_mode_art_size + gui.album_v_gap
								album_on += row_len
							else:
								# render row
								y = render_pos - gui.album_scroll_px

								row_x = 0

								if y > window_size[1] - gui.panelBY - 30 * gui.scale and window_size[1] < 340 * gui.scale:
									break
								# if y >

								for a in range(row_len):
									if album_on > len(tauon.album_dex) - 1:
										break

									x = (l_area + dev * a) - int(tauon.album_mode_art_size / 2) + int(dev / 2) + int(
										compact / 2) - a_offset

									if tauon.album_dex[album_on] > len(pctl.default_playlist):
										break

									track = pctl.master_library[pctl.default_playlist[tauon.album_dex[album_on]]]

									info = tauon.get_album_info(tauon.album_dex[album_on])
									album = info[1]
									# info = (0, 0, 0)

									# rect = (x, y, tauon.album_mode_art_size, tauon.album_mode_art_size + extend * gui.scale)
									# tauon.fields.add(rect)
									# m_in = tauon.coll(rect) and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY

									if gui.first_in_grid is None and y > gui.panelY:  # This marks what track is the first in the grid
										gui.first_in_grid = tauon.album_dex[album_on]

									# artisttitle = colours.side_bar_line2
									# albumtitle = colours.side_bar_line1  # grey(220)

									if card_mode:
										ddt.text_background_colour = colours.grey(250)
										tauon.drop_shadow.render(
											x + 3 * gui.scale, y + 3 * gui.scale,
											tauon.album_mode_art_size + 11 * gui.scale,
											tauon.album_mode_art_size + 45 * gui.scale + 13 * gui.scale)
										ddt.rect(
											(x, y, tauon.album_mode_art_size, tauon.album_mode_art_size + 45 * gui.scale), colours.grey(250))

									# White background needs extra border
									if colours.lm and not card_mode:
										ddt.rect_a((x - 2, y - 2), (tauon.album_mode_art_size + 4, tauon.album_mode_art_size + 4), colours.grey(200))

									if a == row_len - 1:
										gui.gallery_scroll_field_left = max(
											x + tauon.album_mode_art_size,
											window_size[0] - round(50 * gui.scale))

									if info[0] == 1 and (pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED)):
										ddt.rect_a(
											(x - 4, y - 4), (tauon.album_mode_art_size + 8, tauon.album_mode_art_size + 8),
											colours.gallery_highlight)
										# ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size),
										#            colours.gallery_background, True)

									# Draw quick add highlight
									if pctl.quick_add_target:
										pl = pctl.id_to_pl(pctl.quick_add_target)
										if pl is not None and pctl.default_playlist[tauon.album_dex[album_on]] in \
												pctl.multi_playlist[pl].playlist_ids:
											c = ColourRGBA(110, 233, 90, 255)
											if colours.lm:
												c = ColourRGBA(66, 244, 66, 255)
											ddt.rect_a((x - 4, y - 4), (tauon.album_mode_art_size + 8, tauon.album_mode_art_size + 8), c)

									# Draw transcode highlight
									if tauon.transcode_list and os.path.isdir(prefs.encoder_output):
										tr = False

										if (encode_folder_name(track) in os.listdir(prefs.encoder_output)):
											tr = True
										else:
											for folder in tauon.transcode_list:
												if pctl.get_track(folder[0]).parent_folder_path == track.parent_folder_path:
													tr = True
													break
										if tr:
											c = ColourRGBA(244, 212, 66, 255)
											if colours.lm:
												c = ColourRGBA(244, 64, 244, 255)
											ddt.rect_a((x - 4, y - 4), (tauon.album_mode_art_size + 8, tauon.album_mode_art_size + 8), c)
											# ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size),
											#            colours.gallery_background, True)

									# Draw selection

									if (gui.album_tab_mode or gallery_menu.active) and info[2] is True:
										c = colours.gallery_highlight
										c = ColourRGBA(c.g, c.b, c.r, c.a)
										ddt.rect_a((x - 4, y - 4), (tauon.album_mode_art_size + 8, tauon.album_mode_art_size + 8), c)  # [150, 80, 222, 255]
										# ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size),
										#            colours.gallery_background, True)

									# Draw selection animation
									if gui.gallery_animate_highlight_on == tauon.album_dex[
										album_on] and tauon.gallery_select_animate_timer.get() < 1.5:

										t = tauon.gallery_select_animate_timer.get()
										c = colours.gallery_highlight
										if t < 0.2:
											a = int(255 * (t / 0.2))
										elif t < 0.5:
											a = 255
										else:
											a = int(255 - 255 * (t - 0.5))

										c = ColourRGBA(c.g, c.b, c.r, a)
										ddt.rect_a((x - 5, y - 5), (tauon.album_mode_art_size + 10, tauon.album_mode_art_size + 10), c)  # [150, 80, 222, 255]

										gui.update += 1

									# Draw faint outline
									ddt.rect(
										(x - 1, y - 1, tauon.album_mode_art_size + 2, tauon.album_mode_art_size + 2),
										ColourRGBA(255, 255, 255, 11))

									if gui.album_tab_mode or gallery_menu.active:
										if info[2] is False and info[0] != 1 and not colours.lm:
											ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size), ColourRGBA(0, 0, 0, 110))
											albumtitle = colours.grey(160)

									elif info[0] != 1 and pctl.playing_state != PlayingState.STOPPED and prefs.dim_art:
										ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size), ColourRGBA(0, 0, 0, 110))
										albumtitle = colours.grey(160)

									# Determine meta info
									singles = False
									artists = 0
									last_album = ""
									last_artist = ""
									s = 0
									ones = 0
									for id in album:
										tr = pctl.get_track(pctl.default_playlist[id])
										if tr.album != last_album:
											if last_album:
												s += 1
											last_album = tr.album
											if str(tr.track_number) == "1":
												ones += 1
										if tr.artist != last_artist:
											artists += 1
									if s > 2 or ones > 2:
										singles = True

									# Draw blank back colour
									back_colour = ColourRGBA(40, 40, 40, 50)
									if colours.lm:
										back_colour = ColourRGBA(10, 10, 10, 15)

									back_colour = alpha_blend(ColourRGBA(10, 10, 10, 15), colours.gallery_background)

									ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size), back_colour)

									# Draw album art
									if singles:
										dia = math.sqrt(tauon.album_mode_art_size * tauon.album_mode_art_size * 2)
										ran = dia * 0.25
										off = (dia - ran) / 2
										albs = min(len(album), 5)
										spacing = ran / (albs - 1)
										size = round(tauon.album_mode_art_size * 0.5)

										i = 0
										for p in album[:albs]:

											pp = spacing * i
											pp += off
											xx = pp / math.sqrt(2)

											xx -= size / 2
											drawn_art = tauon.gall_ren.render(
												pctl.get_track(pctl.default_playlist[p]), (x + xx, y + xx),
												size=size, force_offset=0)
											if not drawn_art:
												g = 50 + round(100 / albs) * i
												ddt.rect((x + xx, y + xx, size, size), ColourRGBA(g, g, g, 100))
											drawn_art = True
											i += 1
									else:
										album_count += 1
										if (album_count * 1.5) + 10 > tauon.gall_ren.limit:
											tauon.gall_ren.limit = round((album_count * 1.5) + 30)
										drawn_art = tauon.gall_ren.render(track, (x, y))

									# Determine mouse collision
									rect = (x, y, tauon.album_mode_art_size, tauon.album_mode_art_size + extend * gui.scale)
									m_in = tauon.coll(rect) and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY
									tauon.fields.add(rect)

									# Draw mouse-over highlight
									if (not gallery_menu.active and m_in) or (gallery_menu.active and info[2]):
										if tauon.is_level_zero():
											ddt.rect(rect, ColourRGBA(255, 255, 255, 10))

									if drawn_art is False and gui.gallery_show_text is False:
										ddt.text(
											(x + int(tauon.album_mode_art_size / 2), y + tauon.album_mode_art_size - 22 * gui.scale, 2),
											pctl.master_library[pctl.default_playlist[tauon.album_dex[album_on]]].parent_folder_name,
											colours.gallery_artist_line,
											13,
											tauon.album_mode_art_size - 15 * gui.scale,
											bg=alpha_blend(back_colour, colours.gallery_background))

									if prefs.art_bg and drawn_art:
										rect = sdl3.SDL_FRect(round(x), round(y), tauon.album_mode_art_size, tauon.album_mode_art_size)
										if rect.y < gui.panelY:
											diff = round(gui.panelY - rect.y)
											rect.y += diff
											rect.h -= diff
										elif (rect.y + rect.h) > window_size[1] - gui.panelBY:
											diff = round((rect.y + rect.h) - (window_size[1] - gui.panelBY))
											rect.h -= diff

										if rect.h > 0:
											tauon.style_overlay.hole_punches.append(rect)

									# # Drag over highlight
									# if inp.quick_drag and gui.playlist_hold and inp.mouse_down:
									# 	rect = (x, y, tauon.album_mode_art_size, tauon.album_mode_art_size + extend * gui.scale)
									# 	m_in = tauon.coll(rect) and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY
									# 	if m_in:
									# 		ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size), [120, 10, 255, 100], True)

									if gui.gallery_show_text:
										c_index = pctl.default_playlist[tauon.album_dex[album_on]]
										if c_index in gui.album_artist_dict:
											pass
										else:
											i = tauon.album_dex[album_on]
											if pctl.master_library[pctl.default_playlist[i]].album_artist:
												gui.album_artist_dict[c_index] = pctl.master_library[
													pctl.default_playlist[i]].album_artist
											else:
												while i < len(pctl.default_playlist) - 1:
													if pctl.master_library[pctl.default_playlist[i]].parent_folder_name != \
															pctl.master_library[
																pctl.default_playlist[tauon.album_dex[album_on]]].parent_folder_name:
														gui.album_artist_dict[c_index] = pctl.master_library[
															pctl.default_playlist[tauon.album_dex[album_on]]].artist
														break
													if pctl.master_library[pctl.default_playlist[i]].artist != \
															pctl.master_library[
																pctl.default_playlist[tauon.album_dex[album_on]]].artist:
														gui.album_artist_dict[c_index] = _("Various Artists")
														break
													i += 1
												else:
													gui.album_artist_dict[c_index] = pctl.master_library[
														pctl.default_playlist[tauon.album_dex[album_on]]].artist

										line = gui.album_artist_dict[c_index]
										line2 = pctl.master_library[pctl.default_playlist[tauon.album_dex[album_on]]].album
										if singles:
											line2 = pctl.master_library[
												pctl.default_playlist[tauon.album_dex[album_on]]].parent_folder_name
											if artists > 1:
												line = _("Various Artists")

										text_align = 0
										if prefs.center_gallery_text:
											x += tauon.album_mode_art_size // 2
											text_align = 2
										elif card_mode:
											x += round(6 * gui.scale)

										if card_mode:
											if line2 == "":
												ddt.text(
													(x, y + tauon.album_mode_art_size + 8 * gui.scale, text_align),
													line,
													line1_colour,
													310,
													tauon.album_mode_art_size - 18 * gui.scale)
											else:
												ddt.text(
													(x, y + tauon.album_mode_art_size + 7 * gui.scale, text_align),
													line2,
													line2_colour,
													311,
													tauon.album_mode_art_size - 18 * gui.scale)

												ddt.text(
													(x, y + tauon.album_mode_art_size + (10 + 14) * gui.scale, text_align),
													line,
													line1_colour,
													10,
													tauon.album_mode_art_size - 18 * gui.scale)
										elif line2 == "":
											ddt.text(
												(x, y + tauon.album_mode_art_size + 9 * gui.scale, text_align),
												line,
												line1_colour,
												311,
												tauon.album_mode_art_size - 5 * gui.scale)
										else:
											ddt.text(
												(x, y + tauon.album_mode_art_size + 8 * gui.scale, text_align),
												line2,
												line2_colour,
												212,
												tauon.album_mode_art_size)

											ddt.text(
												(x, y + tauon.album_mode_art_size + (10 + 14) * gui.scale, text_align),
												line,
												line1_colour,
												311,
												tauon.album_mode_art_size - 5 * gui.scale)

									album_on += 1

								if album_on > len(tauon.album_dex):
									break
								render_pos += tauon.album_mode_art_size + gui.album_v_gap


						# POWER TAG BAR --------------

						if gui.pt > 0:  # gui.pt > 0 or (gui.power_bar is not None and len(gui.power_bar) > 1):

							top = gui.panelY
							run_y = top + 1

							hot_r = (window_size[0] - 47 * gui.scale, top, 45 * gui.scale, h)
							tauon.fields.add(hot_r)

							if gui.pt == 0:  # mouse moves in
								if tauon.coll(hot_r) and window_is_focused(t_window):
									gui.pt_on.set()
									gui.pt = 1
							elif gui.pt == 1:  # wait then trigger if stays, reset if goes out
								if not tauon.coll(hot_r):
									gui.pt = 0
								elif gui.pt_on.get() > 0.2:
									gui.pt = 2

									off = 0
									for item in gui.power_bar:
										item.ani_timer.force_set(off)
										off -= 0.005

							elif gui.pt == 2:  # wait to turn off

								if tauon.coll(hot_r):
									gui.pt_off.set()
								if gui.pt_off.get() > 0.6 and not lightning_menu.active:
									gui.pt = 3

									off = 0
									for item in gui.power_bar:
										item.ani_timer.force_set(off)
										off -= 0.01

							done = True
							# Animate tags on
							if gui.pt == 2:
								for item in gui.power_bar:
									t = item.ani_timer.get()
									if t < 0:
										break
									if t > 0.2:
										item.peak_x = 9 * gui.scale
									else:
										item.peak_x = (t / 0.2) * 9 * gui.scale

							# Animate tags off
							if gui.pt == 3:
								for item in gui.power_bar:
									t = item.ani_timer.get()
									if t < 0:
										done = False
										break
									if t > 0.2:
										item.peak_x = 0
									else:
										item.peak_x = 9 * gui.scale - ((t / 0.2) * 9 * gui.scale)
										done = False
								if done:
									gui.pt = 0
									gui.update += 1

							# Keep draw loop running while on
							if gui.pt > 0:
								gui.update = 2

							# Draw tags

							block_h = round(27 * gui.scale)
							block_gap = 1 * gui.scale
							if gui.scale == 1.25:
								block_gap = 1

							if tauon.coll(hot_r) or gui.pt > 0:
								for i, item in enumerate(gui.power_bar):
									if run_y + block_h > top + h:
										break

									rect = [window_size[0] - item.peak_x, run_y, 7 * gui.scale, block_h]
									i_rect = [window_size[0] - 36 * gui.scale, run_y, 34 * gui.scale, block_h]
									tauon.fields.add(i_rect)

									if (tauon.coll(i_rect) or (lightning_menu.active and lightning_menu.reference == item)) \
									and item.peak_x == 9 * gui.scale:
										if not lightning_menu.active or lightning_menu.reference == item or inp.right_click:
											minx = 100 * gui.scale
											maxx = minx * 2

											ww = ddt.get_text_w(item.name, 213)

											w = max(minx, ww)
											w = min(maxx, w)

											ddt.rect(
												(rect[0] - w - 25 * gui.scale, run_y, w + 26 * gui.scale, block_h),
												ColourRGBA(230, 230, 230, 255))
											ddt.text(
												(rect[0] - 10 * gui.scale, run_y + 5 * gui.scale, 1), item.name,
												ColourRGBA(5, 5, 5, 255), 213, w, bg=ColourRGBA(230, 230, 230, 255))

											if inp.mouse_click:
												tauon.goto_album(item.position)
											if inp.right_click:
												lightning_menu.activate(item, position=(
												window_size[0] - 180 * gui.scale, rect[1] + rect[3] + 5 * gui.scale))
											if inp.middle_click:
												tauon.path_stem_to_playlist(item.path, item.name)

									ddt.rect(rect, item.colour)
									run_y += block_h + block_gap

						tauon.gallery_pulse_top.render(
							window_size[0] - gui.rspw, gui.panelY, gui.rspw - round(16 * gui.scale), 20 * gui.scale)
					except Exception:
						logging.exception("Gallery render error!")
					# END POWER BAR ------------------------

				# End of gallery view
				# --------------------------------------------------------------------------
				# Main Playlist:
				if len(tauon.load_orders) > 0:
					for i, order in enumerate(tauon.load_orders):
						if order.stage == 2:
							target_pl = 0

							# Sort the tracks by track number
							tauon.sort_track_2(None, order.tracks)

							for p, playlist in enumerate(pctl.multi_playlist):
								if playlist.uuid_int == order.playlist:
									target_pl = p
									break
							else:
								del tauon.load_orders[i]
								logging.error("Target playlist lost")
								break

							if order.replace_stem:
								for ii, id in reversed(list(enumerate(pctl.multi_playlist[target_pl].playlist_ids))):
									pfp = pctl.get_track(id).parent_folder_path
									if pfp.startswith(order.target.replace("\\", "/")):
										if pfp.rstrip("/\\") == order.target.rstrip("/\\") or \
												(len(pfp) > len(order.target) and pfp[
													len(order.target.rstrip("/\\"))] in ("/", "\\")):
											del pctl.multi_playlist[target_pl].playlist_ids[ii]

							#logging.info(order.tracks)
							if order.playlist_position is not None:
								#logging.info(order.playlist_position)
								pctl.multi_playlist[target_pl].playlist_ids[
								order.playlist_position:order.playlist_position] = order.tracks
							# else:

							else:
								pctl.multi_playlist[target_pl].playlist_ids += order.tracks

							pctl.update_shuffle_pool(pctl.multi_playlist[target_pl].uuid_int)

							gui.update += 2
							gui.pl_update += 2
							if order.notify and gui.message_box and len(tauon.load_orders) == 1:
								tauon.show_message(_("Rescan folders complete."), mode="done")
							tauon.reload()
							tauon.tree_view_box.clear_target_pl(target_pl)

							if order.play and order.tracks:

								for p, plst in enumerate(pctl.multi_playlist):
									if order.tracks[0] in plst.playlist_ids:
										target_pl = p
										break

								pctl.switch_playlist(target_pl)

								pctl.active_playlist_playing = pctl.active_playlist_viewing

								# If already in playlist, delete latest add
								if pctl.multi_playlist[target_pl].title == "Default":
									if pctl.default_playlist.count(order.tracks[0]) > 1:
										for q in reversed(range(len(pctl.default_playlist))):
											if pctl.default_playlist[q] == order.tracks[0]:
												del pctl.default_playlist[q]
												break

								pctl.jump(order.tracks[0], pl_position=pctl.default_playlist.index(order.tracks[0]))

								pctl.show_current(True, True, True, True, True)

							del tauon.load_orders[i]

							# Are there more orders for this playlist?
							# If not, decide on a name for the playlist
							for item in tauon.load_orders:
								if item.playlist == order.playlist:
									break
							else:

								if _("New Playlist") in pctl.multi_playlist[target_pl].title:
									tauon.auto_name_pl(target_pl)

								if prefs.auto_sort:
									if pctl.multi_playlist[target_pl].locked:
										tauon.show_message(_("Auto sort skipped because playlist is locked."))
									else:
										logging.info("Auto sorting")
										tauon.standard_sort(target_pl)
										tauon.year_sort(target_pl)

							if not tauon.load_orders:
								pctl.loading_in_progress = False
								pctl.notify_change()
								gui.auto_play_import = False
								gui.album_artist_dict.clear()
							break

				if gui.show_playlist:

					# playlist hit test
					if tauon.coll((
							gui.playlist_left, gui.playlist_top, gui.plw,
							window_size[1] - gui.panelY - gui.panelBY)) and not inp.drag_mode and (
							inp.mouse_click or inp.mouse_wheel != 0 or inp.right_click or inp.middle_click or inp.mouse_up or inp.mouse_down):
						gui.pl_update = 1

					if gui.combo_mode and inp.mouse_wheel != 0:
						gui.pl_update = 1

					# MAIN PLAYLIST
					# C-PR

					top = gui.panelY
					if gui.artist_info_panel:
						top += gui.artist_panel_height

					if gui.set_mode and not gui.set_bar:
						left = 0
						if gui.lsp:
							left = gui.lspw
						rect = [left, top, gui.plw, 12 * gui.scale]
						if inp.right_click and tauon.coll(rect):
							tauon.set_menu_hidden.activate()
							inp.right_click = False

					width = gui.plw
					if gui.set_bar and gui.set_mode:
						left = 0
						if gui.lsp:
							left = gui.lspw

						if gui.tracklist_center_mode:
							left = gui.tracklist_inset_left - round(20 * gui.scale)
							width = gui.tracklist_inset_width + round(20 * gui.scale)

						rect = [left, top, width, gui.set_height]
						start = left + 16 * gui.scale
						run = 0
						in_grip = False

						if not inp.mouse_down and gui.set_hold != -1:
							gui.set_hold = -1

						for h, item in enumerate(gui.pl_st):
							box = (start + run, rect[1], item[1], rect[3])
							grip = (start + run, rect[1], 3 * gui.scale, rect[3])
							m_grip = (grip[0] - 4 * gui.scale, grip[1], grip[2] + 8 * gui.scale, grip[3])
							l_grip = (grip[0] + 9 * gui.scale, grip[1], box[2] - 14 * gui.scale, grip[3])
							tauon.fields.add(m_grip)

							if tauon.coll(l_grip):
								if inp.mouse_up and gui.set_label_hold != -1:
									if point_distance(inp.mouse_position, gui.set_label_point) < 8 * gui.scale:
										sort_direction = 0
										if h != gui.column_d_click_on or gui.column_d_click_timer.get() > 2.5:
											gui.column_d_click_timer.set()
											gui.column_d_click_on = h

											sort_direction = 1

											gui.column_sort_ani_direction = 1
											gui.column_sort_ani_x = start + run + item[1]
										elif gui.column_d_click_on == h:
											gui.column_d_click_on = -1
											gui.column_d_click_timer.force_set(10)

											sort_direction = -1

											gui.column_sort_ani_direction = -1
											gui.column_sort_ani_x = start + run + item[1]

										if sort_direction:
											if gui.pl_st[h][0] in {"Starline", "Rating", "❤", "P", "S", "Time", "Date"}:
												sort_direction *= -1

											if sort_direction == 1:
												tauon.sort_ass(h)
											else:
												tauon.sort_ass(h, True)
											gui.column_sort_ani_timer.set()
									else:
										gui.column_d_click_on = -1
										if h != gui.set_label_hold:
											dest = h
											if dest > gui.set_label_hold:
												dest += 1
											temp = gui.pl_st[gui.set_label_hold]
											gui.pl_st[gui.set_label_hold] = "old"
											gui.pl_st.insert(dest, temp)
											gui.pl_st.remove("old")

											gui.pl_update = 1
											gui.set_label_hold = -1
											#logging.info("MOVE")
											break

										gui.set_label_hold = -1

								if inp.mouse_click:
									gui.set_label_hold = h
									gui.set_label_point = copy.deepcopy(inp.mouse_position)
								if inp.right_click:
									tauon.set_menu.activate(h)

							if h != 0:
								if tauon.coll(m_grip):
									in_grip = True
									if inp.mouse_click:
										gui.set_hold = h
										gui.set_point = inp.mouse_position[0]
										gui.set_old = gui.pl_st[h - 1][1]

								if inp.mouse_down and gui.set_hold == h:
									gui.pl_st[h - 1][1] = gui.set_old + (inp.mouse_position[0] - gui.set_point)
									gui.pl_st[h - 1][1] = max(gui.pl_st[h - 1][1], 25)

									gui.update = 1
									# gui.pl_update = 1

									total = 0
									for i in range(len(gui.pl_st) - 1):
										total += gui.pl_st[i][1]

									wid = gui.plw - round(16 * gui.scale)
									if gui.tracklist_center_mode:
										wid = gui.tracklist_highlight_width - round(16 * gui.scale)
									gui.pl_st[len(gui.pl_st) - 1][1] = wid - total

							run += item[1]

						if not inp.mouse_down:
							gui.set_label_hold = -1
						#logging.info(in_grip)
						if gui.set_label_hold == -1:
							if in_grip and not tauon.x_menu.active and not tauon.view_menu.active and not tab_menu.active and not tauon.set_menu.active:
								gui.cursor_want = 1
							if gui.set_hold != -1:
								gui.cursor_want = 1
								gui.pl_update_on_drag = True

					# heart field test
					if gui.heart_fields:
						for field in gui.heart_fields:
							tauon.fields.add(field, tauon.update_playlist_call)

					if not gui.showcase_mode:
						showcase.timed_lyrics_edit.continuous = False

					if gui.pl_update > 0:
						gui.rendered_playlist_position = pctl.playlist_view_position

						gui.pl_update -= 1
						if gui.combo_mode:
							if gui.radio_view:
								tauon.radio_view.render()
							elif gui.showcase_mode:
								showcase.render()

							# else:
							#     combo_pl_render.full_render()
						else:
							gui.heart_fields.clear()
							playlist_render.full_render()
					elif gui.combo_mode:
						if gui.radio_view:
							tauon.radio_view.render()
						elif gui.showcase_mode:
							showcase.render()
						# else:
						#     combo_pl_render.cache_render()
					else:
						playlist_render.cache_render()

					rect = (gui.playlist_left, gui.panelY, gui.plw, window_size[1] - (gui.panelBY + gui.panelY))

					if gui.ext_drop_mode and tauon.coll(rect):
						ddt.rect_si(rect, ColourRGBA(80, 200, 180, 255), round(3 * gui.scale))
					tauon.fields.add(rect)

					if gui.combo_mode and inp.key_esc_press and tauon.is_level_zero():
						tauon.exit_combo()

					if not gui.set_bar and gui.set_mode and not gui.combo_mode:
						width = gui.plw
						left = 0
						if gui.lsp:
							left = gui.lspw
						if gui.tracklist_center_mode:
							left = gui.tracklist_highlight_left
							width = gui.tracklist_highlight_width
						rect = [left, top, width, gui.set_height // 2.5]
						tauon.fields.add(rect)
						gui.delay_frame(0.26)

						if tauon.coll(rect) and gui.bar_hover_timer.get() > 0.25:
							ddt.rect(rect, colours.column_bar_background)
							if inp.mouse_click:
								gui.set_bar = True
								tauon.update_layout_do()
						if not tauon.coll(rect):
							gui.bar_hover_timer.set()

					if gui.set_bar and gui.set_mode and not gui.combo_mode:

						x = 0
						if gui.lsp:
							x = gui.lspw

						width = gui.plw

						if gui.tracklist_center_mode:
							x = gui.tracklist_highlight_left
							width = gui.tracklist_highlight_width

						rect = [x, top, width, gui.set_height]

						c_bar_background = colours.column_bar_background

						# if colours.lm:
						#     c_bar_background = [235, 110, 160, 255]

						if gui.tracklist_center_mode:
							ddt.rect((0, top, window_size[0], gui.set_height), c_bar_background)
						else:
							ddt.rect(rect, c_bar_background)

						start = x + 16 * gui.scale
						c_width = width - 16 * gui.scale

						run = 0

						for i, item in enumerate(gui.pl_st):
							# if run > rect[2] - 55 * gui.scale:
							#     break

							wid = item[1]

							if run + wid > c_width:
								wid = c_width - run

							if run > c_width - 22 * gui.scale:
								break

							# if run > c_width - 20 * gui.scale:
							#     run = run - 20 * gui.scale

							wid = max(0, wid)

							# ddt.rect_r((run, 40, wid, 10), [255, 0, 0, 100])
							box = (start + run, rect[1], wid, rect[3])

							grip = (start + run, rect[1], 3 * gui.scale, rect[3])

							bg = c_bar_background

							if tauon.coll(box) and gui.set_label_hold != -1:
								bg = ColourRGBA(39, 39, 39, 255)

							if i == gui.set_label_hold:
								bg = ColourRGBA(22, 22, 22, 255)

							ddt.rect(box, bg)
							ddt.rect(grip, colours.column_grip)

							line = _(item[0])
							ddt.text_background_colour = bg

							# # Remove columns if positioned out of view
							# if box[0] + 10 * gui.scale > start + (gui.plw - 25 * gui.scale):
							#
							#     if box[0] + 10 * gui.scale > start + gui.plw:
							#         del gui.pl_st[i]
							#
							#     i += 1
							#     while i < len(gui.pl_st):
							#         del gui.pl_st[i]
							#         i += 1
							#
							#     break
							if line == "❤":
								gui.heart_row_icon.render(box[0] + 9 * gui.scale, top + 8 * gui.scale, colours.column_bar_text)
							else:
								ddt.text(
									(box[0] + 10 * gui.scale, top + 4 * gui.scale), line, colours.column_bar_text, 312,
									bg=bg, max_w=box[2] - 25 * gui.scale)

							run += box[2]

						t = gui.column_sort_ani_timer.get()
						if t < 0.30:
							gui.update += 1
							x = round(gui.column_sort_ani_x - 22 * gui.scale)
							p = t / 0.30

							if gui.column_sort_ani_direction == 1:
								y = top + 8 * p + 3 * gui.scale
								gui.column_sort_down_icon.render(x, round(y), ColourRGBA(255, 255, 255, 90))
							else:
								p = 1 - p
								y = top + 8 * p + 2 * gui.scale
								gui.column_sort_up_icon.render(x, round(y), ColourRGBA(255, 255, 255, 90))

					# Switch Vis:
					if inp.right_click and tauon.coll(
						(window_size[0] - 130 * gui.scale - gui.offset_extra, 0, 125 * gui.scale,
						gui.panelY)) and not gui.top_bar_mode2:
						tauon.vis_menu.activate(None, (window_size[0] - 100 * gui.scale - gui.offset_extra, 30 * gui.scale))
					elif inp.right_click and tauon.top_panel.tabs_right_x < inp.mouse_position[0] and \
							inp.mouse_position[1] < gui.panelY and \
							inp.mouse_position[0] > tauon.top_panel.tabs_right_x and \
							inp.mouse_position[0] < window_size[0] - 130 * gui.scale - gui.offset_extra:

						tauon.window_menu.activate(None, (inp.mouse_position[0], 30 * gui.scale))

					elif inp.middle_click and tauon.top_panel.tabs_right_x < inp.mouse_position[0] and \
							inp.mouse_position[1] < gui.panelY and \
							inp.mouse_position[0] > tauon.top_panel.tabs_right_x and \
							inp.mouse_position[0] < window_size[0] - gui.offset_extra:

						tauon.do_minimize_button()

					# edge_playlist.render(gui.playlist_left, gui.panelY, gui.plw, 2 * gui.scale)

					tauon.bottom_playlist2.render(
						gui.playlist_left, window_size[1] - gui.panelBY, gui.plw, 25 * gui.scale, bottom=True)
					# --------------------------------------------
					# ALBUM ART

					# Right side panel drawing

					if gui.rsp and not prefs.album_mode:
						gui.showing_l_panel = False
						target_track = pctl.show_object()

						if inp.middle_click:
							if tauon.coll(
								(window_size[0] - gui.rspw, gui.panelY, gui.rspw,
								window_size[1] - gui.panelY - gui.panelBY)):

								if (target_track and target_track.lyrics and prefs.show_lyrics_side) or \
										(prefs.show_lyrics_side and prefs.prefer_synced_lyrics and target_track is not None and tauon.timed_lyrics_ren.generate(
											target_track)):
									prefs.show_lyrics_side ^= True
									prefs.side_panel_layout = 1
								elif prefs.side_panel_layout == 0:
									if (target_track and target_track.lyrics and not prefs.show_lyrics_side) or \
											(prefs.prefer_synced_lyrics and target_track is not None and tauon.timed_lyrics_ren.generate(
												target_track)):
										prefs.show_lyrics_side = True
										prefs.side_panel_layout = 1
									else:
										prefs.side_panel_layout = 1
								else:
									prefs.side_panel_layout = 0

						if prefs.show_lyrics_side and prefs.prefer_synced_lyrics and target_track is not None and tauon.timed_lyrics_ren.generate(
								target_track):
							if prefs.show_side_lyrics_art_panel:
								gui.l_panel_h = round(200 * gui.scale)
								gui.l_panel_y = window_size[1] - (gui.panelBY + gui.l_panel_h)
								gui.showing_l_panel = True

								if not prefs.lyric_metadata_panel_top:
									tauon.timed_lyrics_ren.render(
										target_track.index, (window_size[0] - gui.rspw) + 9 * gui.scale,
										gui.panelY, side_panel=True, w=gui.rspw,
										h=window_size[1] - gui.panelY - gui.panelBY - gui.l_panel_h)
									meta_box.l_panel(window_size[0] - gui.rspw, gui.l_panel_y, gui.rspw, gui.l_panel_h, target_track)
								else:
									tauon.timed_lyrics_ren.render(
										target_track.index, (window_size[0] - gui.rspw) + 9 * gui.scale,
										gui.panelY + gui.l_panel_h, side_panel=True,
										w=gui.rspw,
										h=window_size[1] - gui.panelY - gui.panelBY - gui.l_panel_h)
									meta_box.l_panel(window_size[0] - gui.rspw, gui.panelY, gui.rspw, gui.l_panel_h, target_track)
							else:
								tauon.timed_lyrics_ren.render(
									target_track.index, (window_size[0] - gui.rspw) + 9 * gui.scale,
									gui.panelY, side_panel=True, w=gui.rspw,
									h=window_size[1] - gui.panelY - gui.panelBY)

								if inp.right_click and tauon.coll(
									(window_size[0] - gui.rspw, gui.panelY, gui.rspw, window_size[1] - (gui.panelBY + gui.panelY))):
									center_info_menu.activate(target_track)
						elif prefs.show_lyrics_side and target_track is not None and target_track.lyrics and gui.rspw > 192 * gui.scale:
							if prefs.show_side_lyrics_art_panel:
								gui.l_panel_h = round(200 * gui.scale)
								gui.l_panel_y = window_size[1] - (gui.panelBY + gui.l_panel_h)
								gui.showing_l_panel = True

								if not prefs.lyric_metadata_panel_top:
									meta_box.lyrics(
										window_size[0] - gui.rspw, gui.panelY, gui.rspw,
										window_size[1] - gui.panelY - gui.panelBY - gui.l_panel_h, target_track)
									meta_box.l_panel(window_size[0] - gui.rspw, gui.l_panel_y, gui.rspw, gui.l_panel_h, target_track)
								else:
									meta_box.lyrics(
										window_size[0] - gui.rspw, gui.panelY + gui.l_panel_h, gui.rspw,
										window_size[1] - (gui.panelY + gui.panelBY + gui.l_panel_h), target_track)

									meta_box.l_panel(
										window_size[0] - gui.rspw, gui.panelY, gui.rspw, gui.l_panel_h,
										target_track, top_border=False)
							else:
								meta_box.lyrics(
									window_size[0] - gui.rspw, gui.panelY, gui.rspw,
									window_size[1] - gui.panelY - gui.panelBY, target_track)

						elif prefs.side_panel_layout == 0:
							boxw = gui.rspw
							boxh = gui.rspw

							if prefs.show_side_art:
								meta_box.draw(
									window_size[0] - gui.rspw, gui.panelY + boxh, gui.rspw,
									window_size[1] - gui.panelY - gui.panelBY - boxh, track=target_track)

								boxh = min(boxh, window_size[1] - gui.panelY - gui.panelBY)

								tauon.art_box.draw(window_size[0] - gui.rspw, gui.panelY, boxw, boxh, target_track=target_track)

							else:
								meta_box.draw(
									window_size[0] - gui.rspw, gui.panelY, gui.rspw,
									window_size[1] - gui.panelY - gui.panelBY, track=target_track)

						elif prefs.side_panel_layout == 1:
							h = window_size[1] - (gui.panelY + gui.panelBY)
							x = window_size[0] - gui.rspw
							y = gui.panelY
							w = gui.rspw

							ddt.clear_rect((x, y, w, h))
							ddt.rect((x, y, w, h), colours.side_panel_background)
							tauon.test_auto_lyrics(target_track)
							# Draw lyrics if available
							if prefs.show_lyrics_side and target_track and target_track.lyrics:  # and not prefs.show_side_art:
								# meta_box.lyrics(x, y, w, h, target_track)
								if inp.right_click and tauon.coll((x, y, w, h)) and target_track:
									center_info_menu.activate(target_track)
							else:
								box_wide_w = round(w * 0.98)
								boxx = round(min(h * 0.7, w * 0.9))
								boxy = round(min(h * 0.7, w * 0.9))

								bx = (x + w // 2) - (boxx // 2)
								bx_wide = (x + w // 2) - (box_wide_w // 2)
								by = round(h * 0.1)

								bby = by + boxy

								# We want the text in the center, but slightly raised when area is large
								text_y = y + by + boxy + ((h - bby) // 2) - 44 * gui.scale - round(
									(h - bby - 94 * gui.scale) * 0.08)

								small_mode = False
								if window_size[1] < 550 * gui.scale:
									small_mode = True
									text_y = y + by + boxy + ((h - bby) // 2) - 38 * gui.scale

								text_x = x + w // 2

								if prefs.show_side_art:
									gui.art_drawn_rect = None
									default_border = (bx, by, boxx, boxy)
									coll_border = default_border

									tauon.art_box.draw(
										bx_wide, by, box_wide_w, boxy, target_track=target_track,
										tight_border=True, default_border=default_border)

									if gui.art_drawn_rect:
										coll_border = gui.art_drawn_rect

									if inp.right_click and tauon.coll((x, y, w, h)) and not tauon.coll(coll_border):
										if tauon.is_level_zero(include_menus=False) and target_track:
											center_info_menu.activate(target_track)

								else:
									text_y = y + round(h * 0.40)
									if inp.right_click and tauon.coll((x, y, w, h)) and target_track:
										center_info_menu.activate(target_track)

								ww = w - 25 * gui.scale

								gui.showed_title = True

								if target_track:
									ddt.text_background_colour = colours.side_panel_background

									if pctl.playing_state == PlayingState.URL_STREAM and not radiobox.dummy_track.title:
										title = pctl.tag_meta
									else:
										title = target_track.title
										if not title:
											title = clean_string(target_track.filename)

									if small_mode:
										ddt.text(
											(text_x, text_y - 15 * gui.scale, 2), target_track.artist,
											colours.side_bar_line1, 315, max_w=ww)

										ddt.text(
											(text_x, text_y + 12 * gui.scale, 2), title, colours.side_bar_line1, 216, max_w=ww)

										line = " | ".join(
											filter(None, (target_track.album, target_track.date, target_track.genre)))
										ddt.text((text_x, text_y + 35 * gui.scale, 2), line, colours.side_bar_line2, 313, max_w=ww)

									else:
										ddt.text((text_x, text_y - 15 * gui.scale, 2), target_track.artist, colours.side_bar_line1, 317, max_w=ww)

										ddt.text((text_x, text_y + 17 * gui.scale, 2), title, colours.side_bar_line1, 218, max_w=ww)

										line = " | ".join(
											filter(None, (target_track.album, target_track.date, target_track.genre)))
										ddt.text((text_x, text_y + 45 * gui.scale, 2), line, colours.side_bar_line2, 314, max_w=ww)

					# Separation Line Drawing
					if gui.rsp:
						# Draw Highlight when mouse over
						if draw_sep_hl:
							ddt.line(
								window_size[0] - gui.rspw + 1 * gui.scale, gui.panelY + 1 * gui.scale,
								window_size[0] - gui.rspw + 1 * gui.scale,
								window_size[1] - 50 * gui.scale, ColourRGBA(100, 100, 100, 70))
							draw_sep_hl = False

				if (gui.artist_info_panel and not gui.combo_mode) and not (window_size[0] < 750 * gui.scale and prefs.album_mode):
					tauon.artist_info_box.draw(gui.playlist_left, gui.panelY, gui.plw, gui.artist_panel_height)

				if gui.lsp and not gui.combo_mode:
					# left side panel
					h_estimate = ((tauon.playlist_box.tab_h + tauon.playlist_box.gap) * gui.scale * len(
						pctl.multi_playlist)) + 13 * gui.scale

					full = (window_size[1] - (gui.panelY + gui.panelBY))
					half = round(full / 2)

					gui.pl_box_h = full

					panel_rect = (0, gui.panelY, gui.lspw, gui.pl_box_h)
					tauon.fields.add(panel_rect)

					if gui.force_side_on_drag and not inp.quick_drag and not tauon.coll(panel_rect):
						gui.force_side_on_drag = False
						tauon.update_layout_do()

					if inp.quick_drag and not coll_point(gui.drag_source_position_persist, panel_rect) and \
						not point_proximity_test(
							gui.drag_source_position,
							inp.mouse_position,
							10 * gui.scale):
						gui.force_side_on_drag = True
						if inp.mouse_up:
							tauon.update_layout_do()

					if prefs.left_panel_mode == "folder view" and not gui.force_side_on_drag:
						tauon.tree_view_box.render(0, gui.panelY, gui.lspw, gui.pl_box_h)
					elif prefs.left_panel_mode == "artist list" and not gui.force_side_on_drag:
						tauon.artist_list_box.render(*panel_rect)
					else:
						preview_queue = False
						if inp.quick_drag and tauon.coll(
								panel_rect) and not pctl.force_queue and prefs.show_playlist_list and prefs.hide_queue:
							preview_queue = True

						if pctl.force_queue or preview_queue or not prefs.hide_queue:
							if h_estimate < half:
								gui.pl_box_h = h_estimate
							else:
								gui.pl_box_h = half

							if preview_queue:
								gui.pl_box_h = round(full * 5 / 6)

						if prefs.left_panel_mode != "queue":
							tauon.playlist_box.draw(0, gui.panelY, gui.lspw, gui.pl_box_h)
						else:
							gui.pl_box_h = 0

						if pctl.force_queue or preview_queue or not prefs.show_playlist_list or not prefs.hide_queue:
							tauon.queue_box.draw(0, gui.panelY + gui.pl_box_h, gui.lspw, full - gui.pl_box_h)
						elif prefs.left_panel_mode == "queue":
							text = _("Queue is Empty")
							rect = (0, gui.panelY + gui.pl_box_h, gui.lspw, full - gui.pl_box_h)
							ddt.rect(rect, colours.queue_background)
							ddt.text_background_colour = colours.queue_background
							ddt.text(
								(0 + (gui.lspw // 2), gui.panelY + gui.pl_box_h + 15 * gui.scale, 2),
								text, alpha_mod(colours.index_text, 200), 212)

				# ------------------------------------------------
				# Scroll Bar

				# if not prefs.scroll_enable:
				top = gui.panelY
				if gui.artist_info_panel:
					top += gui.artist_panel_height

				edge_top = top
				if gui.set_bar and gui.set_mode:
					edge_top += gui.set_height
				tauon.edge_playlist2.render(gui.playlist_left, edge_top, gui.plw, 25 * gui.scale)

				width = 15 * gui.scale

				x = 0
				if gui.lsp:  # Move left so it sits over panel divide

					x = gui.lspw - 1 * gui.scale
					if not gui.set_mode:
						width = 11 * gui.scale
				if gui.set_mode and prefs.left_align_album_artist_title:
					width = 11 * gui.scale

				# x = gui.plw
				# width = round(14 * gui.scale)
				# if gui.lsp:
				#     x += gui.lspw
				# x -= width

				gui.scroll_hide_box = (
					x + 1 if not gui.maximized else x, top, 28 * gui.scale, window_size[1] - gui.panelBY - top)

				tauon.fields.add(gui.scroll_hide_box)
				if tauon.scroll_hide_timer.get() < 0.9 or ((tauon.coll(
						gui.scroll_hide_box) or scroll_hold or gui.quick_search_mode) and \
						not menu_is_open() and \
						not pref_box.enabled and \
						not gui.rename_playlist_box \
						and gui.layer_focus == 0 and gui.show_playlist and not tauon.search_over.active):

					scroll_opacity = 255

					if not gui.combo_mode:
						sy = 31 * gui.scale
						ey = window_size[1] - (30 + 22) * gui.scale

						if len(pctl.default_playlist) < 50:
							sbl = 85 * gui.scale
							if len(pctl.default_playlist) == 0:
								sbp = top
						else:
							sbl = 105 * gui.scale

						tauon.fields.add((x + 2 * gui.scale, sbp, 20 * gui.scale, sbl))
						if tauon.coll((x, top, 28 * gui.scale, ey - top)) and (
								inp.mouse_down or inp.right_click) \
								and coll_point(inp.click_location, (x, top, 28 * gui.scale, ey - top)):

							gui.pl_update = 1
							if inp.right_click:
								sbp = inp.mouse_position[1] - int(sbl / 2)
								if sbp + sbl > ey:
									sbp = ey - sbl
								elif sbp < top:
									sbp = top
								per = (sbp - top) / (ey - top - sbl)
								pctl.playlist_view_position = int(len(pctl.default_playlist) * per)
								logging.debug("Position set by scroll bar (right click)")
								pctl.playlist_view_position = max(pctl.playlist_view_position, 0)

								# if playlist_position == len(pctl.default_playlist):
								#     logging.info("END")

							# elif inp.mouse_position[1] < sbp:
							#     pctl.playlist_view_position -= 2
							# elif inp.mouse_position[1] > sbp + sbl:
							#     pctl.playlist_view_position += 2
							elif inp.mouse_click:

								if inp.mouse_position[1] < sbp:
									gui.scroll_direction = -1
								elif inp.mouse_position[1] > sbp + sbl:
									gui.scroll_direction = 1
								else:
									# p_y = pointer(c_int(0))
									# p_x = pointer(c_int(0))
									# sdl3.SDL_GetGlobalMouseState(p_x, p_y)
									tauon.input_sdl.mouse_capture_want = True

									scroll_hold = True
									# scroll_point = p_y.contents.value  # inp.mouse_position[1]
									scroll_point = inp.mouse_position[1]
									scroll_bpoint = sbp
							else:
								# gui.update += 1
								if sbp < inp.mouse_position[1] < sbp + sbl:
									gui.scroll_direction = 0
								pctl.playlist_view_position += gui.scroll_direction * 2
								logging.debug("Position set by scroll bar (slide)")
								pctl.playlist_view_position = max(pctl.playlist_view_position, 0)
								pctl.playlist_view_position = min(pctl.playlist_view_position, len(pctl.default_playlist))

								if sbp + sbl > ey:
									sbp = ey - sbl
								elif sbp < top:
									sbp = top

						if not inp.mouse_down:
							scroll_hold = False

						if scroll_hold and not inp.mouse_click:
							gui.pl_update = 1
							# p_y = pointer(c_int(0))
							# p_x = pointer(c_int(0))
							# sdl3.SDL_GetGlobalMouseState(p_x, p_y)
							tauon.input_sdl.mouse_capture_want = True

							sbp = inp.mouse_position[1] - (scroll_point - scroll_bpoint)
							if sbp + sbl > ey:
								sbp = ey - sbl
							elif sbp < top:
								sbp = top
							per = (sbp - top) / (ey - top - sbl)
							pctl.playlist_view_position = int(len(pctl.default_playlist) * per)
							logging.debug("Position set by scroll bar (drag)")


						elif len(pctl.default_playlist) > 0:
							per = pctl.playlist_view_position / len(pctl.default_playlist)
							sbp = int((ey - top - sbl) * per) + top + 1

						bg = ColourRGBA(255, 255, 255, 6)
						fg = colours.scroll_colour

						if colours.lm:
							bg = ColourRGBA(200, 200, 200, 100)
							fg = ColourRGBA(100, 100, 100, 200)

						ddt.rect_a((x, top), (width + 1 * gui.scale, window_size[1] - top - gui.panelBY), bg)
						ddt.rect_a((x + 1, sbp), (width, sbl), alpha_mod(fg, scroll_opacity))

						if (tauon.coll((x + 2 * gui.scale, sbp, 20 * gui.scale, sbl)) and inp.mouse_position[
							0] != 0) or scroll_hold:
							ddt.rect_a((x + 1 * gui.scale, sbp), (width, sbl), ColourRGBA(255, 255, 255, 19))

				# NEW TOP BAR
				# C-TBR

				if gui.mode == 1:
					tauon.top_panel.render()

				# RENDER EXTRA FRAME DOUBLE
				if colours.lm:
					if gui.lsp and not gui.combo_mode and not gui.compact_artist_list:
						ddt.rect(
							(0 + gui.lspw - 6 * gui.scale, gui.panelY, 6 * gui.scale,
							round(window_size[1] - gui.panelY - gui.panelBY)), colours.grey(200))
						ddt.rect(
							(0 + gui.lspw - 5 * gui.scale, gui.panelY - 1, 4 * gui.scale,
							round(window_size[1] - gui.panelY - gui.panelBY) + 1), colours.grey(245))
					if gui.rsp and gui.show_playlist:
						w = window_size[0] - gui.rspw
						ddt.rect(
							(w - round(3 * gui.scale), gui.panelY, 6 * gui.scale,
							round(window_size[1] - gui.panelY - gui.panelBY)), colours.grey(200))
						ddt.rect(
							(w - round(2 * gui.scale), gui.panelY - 1, 4 * gui.scale,
							round(window_size[1] - gui.panelY - gui.panelBY) + 1), colours.grey(245))
					if gui.queue_frame_draw is not None:
						if gui.lsp:
							ddt.rect((0, gui.queue_frame_draw, gui.lspw - 6 * gui.scale, 6 * gui.scale), colours.grey(200))
							ddt.rect(
								(0, gui.queue_frame_draw + 1 * gui.scale, gui.lspw - 5 * gui.scale, 4 * gui.scale), colours.grey(250))

						gui.queue_frame_draw = None

				# BOTTOM BAR!
				# C-BB

				ddt.text_background_colour = colours.bottom_panel_colour

				if prefs.shuffle_lock:
					tauon.bottom_bar_ao1.render()
				else:
					tauon.bottom_bar1.render()

				if prefs.art_bg and not prefs.bg_showcase_only:
					tauon.style_overlay.display()
					# if inp.key_shift_down:
					#     ddt.rect_r(gui.seek_bar_rect,
					#                alpha_mod([150, 150, 150 ,255], 20), True)
					#     ddt.rect_r(gui.volume_bar_rect,
					#                alpha_mod(colours.volume_bar_fill, 100), True)

				tauon.style_overlay.hole_punches.clear()

				if gui.set_mode:
					if tauon.rename_track_box.active is False \
							and radiobox.active is False \
							and gui.rename_playlist_box is False \
							and gui.message_box is False \
							and pref_box.enabled is False \
							and gui.track_box is False \
							and not gui.rename_folder_box \
							and not gui.timed_lyrics_editing_now \
							and not Menu.active \
							and not tauon.artist_info_scroll.held:

						tauon.columns_tool_tip.render()
					else:
						tauon.columns_tool_tip.show = False

				# Overlay GUI ----------------------

				if gui.rename_playlist_box:
					tauon.rename_playlist_box.render()

				if gui.preview_artist:

					border = round(4 * gui.scale)
					ddt.rect(
						(gui.preview_artist_location[0] - border,
						gui.preview_artist_location[1] - border,
						tauon.artist_preview_render.size[0] + border * 2,
						tauon.artist_preview_render.size[0] + border * 2), ColourRGBA(20, 20, 20, 255))

					tauon.artist_preview_render.draw(gui.preview_artist_location[0], gui.preview_artist_location[1])
					if inp.mouse_click or inp.right_click or inp.mouse_wheel:
						gui.preview_artist = ""

				if gui.track_box:
					if inp.key_return_press or inp.right_click or inp.key_esc_press or inp.backspace_press or keymaps.test(
							"quick-find"):
						gui.track_box = False

						inp.key_return_press = False

					if gui.level_2_click:
						inp.mouse_click = True
					gui.level_2_click = False

					tc = pctl.master_library[pctl.r_menu_index]

					w = round(540 * gui.scale)
					h = round(240 * gui.scale)
					comment_mode = 0

					if len(tc.comment) > 0:
						h += 22 * gui.scale
						if window_size[0] > 599:
							w += 25 * gui.scale
						if ddt.get_text_w(tc.comment, 12) > 330 * gui.scale or "\n" in tc.comment:
							h += 80 * gui.scale
							if window_size[0] > 599:
								w += 30 * gui.scale
							comment_mode = 1

					x = round((window_size[0] / 2) - (w / 2))
					y = round((window_size[1] / 2) - (h / 2))

					x1 = int(x + 18 * gui.scale)
					x2 = int(x + 98 * gui.scale)

					value_font_a = 312
					value_font = 12

					# if inp.key_shift_down:
					#     value_font = 12
					key_colour_off = colours.box_text_label  # colours.grey_blend_bg(90)
					key_colour_on = colours.box_title_text
					value_colour = colours.box_sub_text
					path_colour = alpha_mod(value_colour, 240)

					# if colours.lm:
					#     key_colour_off = colours.grey(80)
					#     key_colour_on = colours.grey(120)
					#     value_colour = colours.grey(50)
					#     path_colour = colours.grey(70)

					ddt.rect_a(
						(x - 3 * gui.scale, y - 3 * gui.scale), (w + 6 * gui.scale, h + 6 * gui.scale),
						colours.box_border)
					ddt.rect_a((x, y), (w, h), colours.box_background)
					ddt.text_background_colour = colours.box_background

					if inp.mouse_click and not tauon.coll([x, y, w, h]):
						gui.track_box = False
					else:
						art_size = int(115 * gui.scale)

						# if not tc.is_network: # Don't draw album art if from network location for better performance
						if comment_mode == 1:
							tauon.album_art_gen.display(
								tc, (int(x + w - 135 * gui.scale), int(y + 105 * gui.scale)),
								(art_size, art_size))  # Mirror this size in auto theme #mark2233
						else:
							tauon.album_art_gen.display(
								tc, (int(x + w - 135 * gui.scale), int(y + h - 135 * gui.scale)),
								(art_size, art_size))

						y -= int(24 * gui.scale)
						y1 = int(y + (40 * gui.scale))

						ext_rect = [x + w - round(38 * gui.scale), y + round(44 * gui.scale), round(38 * gui.scale),
									round(12 * gui.scale)]

						line = tc.file_ext
						ex_colour = ColourRGBA(130, 130, 130, 255)
						if line in tauon.formats.colours:
							ex_colour = tauon.formats.colours[line]

						# Spotify icon rendering
						if line == "SPTY":
							colour = ColourRGBA(30, 215, 96, 255)
							h, l, s = rgb_to_hls(colour.r, colour.g, colour.b)

							rect = (x + w - round(35 * gui.scale), y + round(30 * gui.scale), round(30 * gui.scale),
									round(30 * gui.scale))
							tauon.fields.add(rect)
							if tauon.coll(rect):
								l += 0.1
								gui.cursor_want = 3

								if inp.mouse_click:
									url = tc.misc.get("spotify-album-url")
									if url is None:
										url = tc.misc.get("spotify-track-url")
									if url:
										webbrowser.open(url, new=2, autoraise=True)

							colour = hls_to_rgb(h, l, s)

							gui.spot_info_icon.render(x + w - round(33 * gui.scale), y + round(35 * gui.scale), colour)

						# Codec tag rendering
						else:
							if tc.file_ext in ("JELY", "TIDAL"):
								e_colour = ColourRGBA(130, 130, 130, 255)
								if "container" in tc.misc:
									line = tc.misc["container"].upper()
									if line in tauon.formats.colours:
										e_colour = tauon.formats.colours[line]

								ddt.rect(ext_rect, e_colour)
								colour = alpha_blend(ColourRGBA(10, 10, 10, 235), e_colour)
								if colour_value(e_colour) < 180:
									colour = alpha_blend(ColourRGBA(200, 200, 200, 235), e_colour)
								ddt.text(
									(int(x + w - 35 * gui.scale), round(y + (41) * gui.scale)), line, colour, 211, bg=e_colour)
								ext_rect[1] += 16 * gui.scale
								y += 16 * gui.scale

							ddt.rect(ext_rect, ex_colour)
							colour = alpha_blend(ColourRGBA(10, 10, 10, 235), ex_colour)
							if colour_value(ex_colour) < 180:
								colour = alpha_blend(ColourRGBA(200, 200, 200, 235), ex_colour)
							ddt.text(
								(int(x + w - 35 * gui.scale), round(y + 41 * gui.scale)), tc.file_ext, colour, 211, bg=ex_colour)

							if tc.is_cue:
								ext_rect[1] += 16 * gui.scale
								colour = ColourRGBA(218, 222, 73, 255)
								if tc.is_embed_cue:
									colour = ColourRGBA(252, 199, 55, 255)
								ddt.rect(ext_rect, colour)
								ddt.text(
									(int(x + w - 35 * gui.scale), int(y + (41 + 16) * gui.scale)), "CUE",
									alpha_blend(ColourRGBA(10, 10, 10, 235), colour), 211, bg=colour)


						rect = [x1, y1 + int(2 * gui.scale), 450 * gui.scale, 14 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Title"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.title)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Title"), key_colour_off, 212)
						q = ddt.text(
							(x2, y1 - int(2 * gui.scale)), tc.title,
							value_colour, 314, max_w=w - 170 * gui.scale)

						if tauon.coll(rect):
							tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.title, 314)

						y1 += int(16 * gui.scale)

						rect = [x1, y1 + (2 * gui.scale), 450 * gui.scale, 14 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Artist"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.artist)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Artist"), key_colour_off, 212)

						q = ddt.text(
							(x2, y1 - (1 * gui.scale)), tc.artist,
							value_colour, value_font_a, max_w=390 * gui.scale)

						if tauon.coll(rect):
							tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.artist, value_font_a)

						y1 += int(16 * gui.scale)

						rect = [x1, y1 + (2 * gui.scale), 450 * gui.scale, 14 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Album"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.album)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Album"), key_colour_off, 212)

						q = ddt.text(
							(x2, y1 - 1 * gui.scale), tc.album,
							value_colour,
							value_font_a, max_w=390 * gui.scale)

						if tauon.coll(rect):
							tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.album, value_font_a)

						y1 += int(26 * gui.scale)

						rect = [x1, y1, 450 * gui.scale, 16 * gui.scale]
						tauon.fields.add(rect)
						path = tc.fullpath
						if tauon.msys:
							path = path.replace("/", "\\")
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Path"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(path)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Path"), key_colour_off, 212)

						q = ddt.text(
							(x2, y1 - int(3 * gui.scale)), clean_string(path),
							path_colour, 210, max_w=425 * gui.scale)

						if tauon.coll(rect):
							gui.frame_callback_list.append(TestTimer(0.71))
							if tauon.track_box_path_tool_timer.get() > 0.7:
								tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, clean_string(tc.fullpath), 210)
						else:
							tauon.track_box_path_tool_timer.set()

						y1 += int(15 * gui.scale)

						if tc.samplerate != 0:
							ddt.text((x1, y1), _("Samplerate"), key_colour_off, 212, max_w=70 * gui.scale)

							line = str(tc.samplerate) + " Hz"

							off = ddt.text((x2, y1), line, value_colour, value_font)

							if tc.bit_depth > 0:
								line = str(tc.bit_depth) + " bit"
								ddt.text((x2 + off + 9 * gui.scale, y1), line, value_colour, 311)

						y1 += int(15 * gui.scale)

						if tc.bitrate not in (0, "", "0"):
							ddt.text((x1, y1), _("Bitrate"), key_colour_off, 212, max_w=70 * gui.scale)
							line = str(tc.bitrate)
							if tc.file_ext in ("FLAC", "OPUS", "APE", "WV"):
								line = "≈" + line
							line += _(" kbps")
							ddt.text((x2, y1), line, value_colour, 312)

						# -----------
						if tc.artist != tc.album_artist:
							x += int(170 * gui.scale)
							rect = [x + 7 * gui.scale, y1 + (2 * gui.scale), 220 * gui.scale, 14 * gui.scale]
							tauon.fields.add(rect)
							if tauon.coll(rect):
								ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Album Artist"), key_colour_on, 212)
								if inp.mouse_click:
									tauon.show_message(_("Copied text to clipboard"))
									copy_to_clipboard(tc.album_artist)
									inp.mouse_click = False
							else:
								ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Album Artist"), key_colour_off, 212)

							q = ddt.text(
								(x + (8 + 88) * gui.scale, y1), tc.album_artist,
								value_colour, value_font, max_w=120 * gui.scale)
							if tauon.coll(rect):
								tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.album_artist, value_font)

							x -= int(170 * gui.scale)

						y1 += int(15 * gui.scale)

						rect = [x1, y1, 150 * gui.scale, 16 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Duration"), key_colour_on, 212)
							if inp.mouse_click:
								copy_to_clipboard(time.strftime("%M:%S", time.gmtime(tc.length)).lstrip("0"))
								tauon.show_message(_("Copied text to clipboard"))
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Duration"), key_colour_off, 212)
						line = time.strftime("%M:%S", time.gmtime(tc.length))
						ddt.text((x2, y1), line, value_colour, value_font)

						# -----------
						if tc.track_total not in ("", "0"):
							x += int(170 * gui.scale)
							line = str(tc.track_number) + _(" of ") + str(
								tc.track_total)
							ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Track"), key_colour_off, 212)
							ddt.text((x + (8 + 88) * gui.scale, y1), line, value_colour, value_font)
							x -= int(170 * gui.scale)

						y1 += int(15 * gui.scale)
						#logging.info(tc.size)
						if tc.is_cue and tc.misc.get("parent-length", 0) > 0 and tc.misc.get("parent-size", 0) > 0:
							ddt.text((x1, y1), _("File size"), key_colour_off, 212, max_w=70 * gui.scale)
							estimate = (tc.length / tc.misc.get("parent-length")) * tc.misc.get("parent-size")
							line = f"≈{get_filesize_string(estimate, rounding=0)} / {get_filesize_string(tc.misc.get('parent-size'))}"
							ddt.text((x2, y1), line, value_colour, value_font)

						elif tc.size != 0:
							ddt.text((x1, y1), _("File size"), key_colour_off, 212, max_w=70 * gui.scale)
							ddt.text((x2, y1), get_filesize_string(tc.size), value_colour, value_font)

						# -----------
						if tc.disc_total not in ("", "0", 0):
							x += int(170 * gui.scale)
							line = str(tc.disc_number) + _(" of ") + str(
								tc.disc_total)
							ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Disc"), key_colour_off, 212)
							ddt.text((x + (8 + 88) * gui.scale, y1), line, value_colour, value_font)
							x -= int(170 * gui.scale)

						y1 += int(23 * gui.scale)

						rect = [x1, y1 + (2 * gui.scale), 150 * gui.scale, 14 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Genre"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.genre)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Genre"), key_colour_off, 212)
						ddt.text(
							(x2, y1), tc.genre, value_colour,
							value_font, max_w=290 * gui.scale)

						y1 += int(15 * gui.scale)

						rect = [x1, y1 + (2 * gui.scale), 150 * gui.scale, 14 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Date"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.date)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Date"), key_colour_off, 212)
						ddt.text((x2, y1), d_date_display(tc), value_colour, value_font)

						if tc.composer and tc.composer != tc.artist:
							x += int(170 * gui.scale)
							rect = [x + 7 * gui.scale, y1 + (2 * gui.scale), 220 * gui.scale, 14 * gui.scale]
							tauon.fields.add(rect)
							if tauon.coll(rect):
								ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Composer"), key_colour_on, 212)
								if inp.mouse_click:
									tauon.show_message(_("Copied text to clipboard"))
									copy_to_clipboard(tc.album_artist)
									inp.mouse_click = False
							else:
								ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Composer"), key_colour_off, 212)
							q = ddt.text(
								(x + (8 + 88) * gui.scale, y1), tc.composer,
								value_colour, value_font, max_w=120 * gui.scale)
							if tauon.coll(rect):
								tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.composer, value_font_a)

							x -= int(170 * gui.scale)

						y1 += int(23 * gui.scale)

						total = tauon.star_store.get(pctl.r_menu_index)

						ratio = 0

						if total > 0 and pctl.master_library[
							pctl.r_menu_index].length > 1:
							ratio = total / (tc.length - 1)

						ddt.text((x1, y1), _("Play count"), key_colour_off, 212, max_w=70 * gui.scale)
						ddt.text((x2, y1), str(int(ratio)), value_colour, value_font)

						y1 += int(15 * gui.scale)

						rect = [x1, y1, 150, 14]

						if tauon.coll(rect) and inp.key_shift_down and inp.mouse_wheel != 0:
							tauon.star_store.add(pctl.r_menu_index, 60 * inp.mouse_wheel)

						line = time.strftime("%H:%M:%S", time.gmtime(total))

						ddt.text((x1, y1), _("Play time"), key_colour_off, 212, max_w=70 * gui.scale)
						ddt.text((x2, y1), str(line), value_colour, value_font)

						# -------
						if tc.lyrics:
							if pctl.draw.button(_("Lyrics"), x1 + 200 * gui.scale, y1 - 10 * gui.scale):
								prefs.show_lyrics_showcase = True
								gui.track_box = False
								tauon.enter_showcase_view(track_id=pctl.r_menu_index)
								inp.mouse_click = False

						if len(tc.comment) > 0:
							y1 += 20 * gui.scale
							rect = [x1, y1 + (2 * gui.scale), 60 * gui.scale, 14 * gui.scale]
							# ddt.rect_r((x2, y1, 335, 10), [255, 20, 20, 255])
							tauon.fields.add(rect)
							if tauon.coll(rect):
								ddt.text((x1, y1), _("Comment"), key_colour_on, 212)
								if inp.mouse_click:
									tauon.show_message(_("Copied text to clipboard"))
									copy_to_clipboard(tc.comment)
									inp.mouse_click = False
							else:
								ddt.text((x1, y1), _("Comment"), key_colour_off, 212)
							# ddt.draw_text((x1, y1), "Comment", key_colour_off, 12)

							if "\n" not in tc.comment and (
									"http://" in tc.comment or "www." in tc.comment or "https://" in tc.comment) and ddt.get_text_w(
									tc.comment, 12) < 335 * gui.scale:

								link_pa = tauon.draw_linked_text((x2, y1), tc.comment, value_colour, 12)
								link_rect = [x + 98 * gui.scale + link_pa[0], y1 - 2 * gui.scale, link_pa[1], 20 * gui.scale]

								tauon.fields.add(link_rect)
								if tauon.coll(link_rect):
									if not inp.mouse_click:
										gui.cursor_want = 3
									if inp.mouse_click:
										webbrowser.open(link_pa[2], new=2, autoraise=True)
										gui.track_box = True

							elif comment_mode == 1:
								ddt.text(
									(x + 18 * gui.scale, y1 + 18 * gui.scale, 4, w - 36 * gui.scale, 90 * gui.scale),
									tc.comment, value_colour, 12)
							else:
								ddt.text((x2, y1), tc.comment, value_colour, 12)

				if tauon.draw_border and gui.mode != 3:
					tool_rect = [window_size[0] - 110 * gui.scale, 2, 95 * gui.scale, 45 * gui.scale]
					if prefs.left_window_control:
						tool_rect[0] = 0
					tauon.fields.add(tool_rect)
					if not gui.top_bar_mode2 or tauon.coll(tool_rect):
						tauon.draw_window_tools()

					if not gui.fullscreen and not gui.maximized:
						tauon.draw_window_border()

				tauon.fader.render()
				if pref_box.enabled:
					# rect = [0, 0, window_size[0], window_size[1]]
					# ddt.rect_r(rect, [0, 0, 0, 90], True)
					pref_box.render()
				elif not Path(tauon.prefs.playlist_folder_path).is_dir():
					tauon.prefs.playlist_folder_path = ""
					prefs.autoscan_playlist_folder = False

				if gui.rename_folder_box:
					if gui.level_2_click:
						inp.mouse_click = True

					gui.level_2_click = False

					w = 500 * gui.scale
					h = 127 * gui.scale
					x = int(window_size[0] / 2) - int(w / 2)
					y = int(window_size[1] / 2) - int(h / 2)

					ddt.rect_a(
						(x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.box_border)
					ddt.rect_a((x, y), (w, h), colours.box_background)

					ddt.text_background_colour = colours.box_background

					if inp.key_esc_press or (
							(inp.mouse_click or inp.right_click or inp.level_2_right_click) and not tauon.coll((x, y, w, h))):
						gui.rename_folder_box = False

					p = ddt.text(
						(x + 10 * gui.scale, y + 9 * gui.scale), _("Folder Modification"), colours.box_title_text, 213)

					if tauon.rename_folder.text != prefs.rename_folder_template and pctl.draw.button(
						_("Default"),
						x + (300 - 63) * gui.scale,
						y + 11 * gui.scale,
						70 * gui.scale):
						tauon.rename_folder.text = prefs.rename_folder_template

					tauon.rename_folder.draw(x + 14 * gui.scale, y + 41 * gui.scale, colours.box_input_text, width=300)

					ddt.rect_s(
						(x + 8 * gui.scale, y + 38 * gui.scale, 300 * gui.scale, 22 * gui.scale),
						colours.box_text_border, 1 * gui.scale)

					if pctl.draw.button(
						_("Rename"), x + (8 + 300 + 10) * gui.scale, y + 38 * gui.scale, 80 * gui.scale,
						tooltip=_("Renames the physical folder based on the template")) or inp.level_2_enter:
						tauon.rename_parent(gui.rename_index, tauon.rename_folder.text)
						gui.rename_folder_box = False
						inp.mouse_click = False

					text = _("Trash")
					tt = _("Moves folder to system trash")
					if inp.key_shift_down:
						text = _("Delete")
						tt = _("Physically deletes folder from disk")
					if pctl.draw.button(
						text, x + (8 + 300 + 10) * gui.scale, y + 11 * gui.scale, 80 * gui.scale,
						text_highlight_colour=colours.grey(255), background_highlight_colour=ColourRGBA(180, 60, 60, 255),
						press=inp.mouse_up, tooltip=tt):
						if inp.key_shift_down:
							tauon.delete_folder(gui.rename_index, True)
						else:
							tauon.delete_folder(gui.rename_index)
						gui.rename_folder_box = False
						inp.mouse_click = False

					if tauon.move_folder_up(gui.rename_index):
						if pctl.draw.button(
							_("Raise"), x + 408 * gui.scale, y + 38 * gui.scale, 80 * gui.scale,
							tooltip=_("Moves folder up 2 levels and deletes the old container folder")):
							tauon.move_folder_up(gui.rename_index, True)
							inp.mouse_click = False

					to_clean = tauon.clean_folder(gui.rename_index)
					if to_clean > 0:
						if pctl.draw.button(
							"Clean (" + str(to_clean) + ")", x + 408 * gui.scale, y + 11 * gui.scale,
							80 * gui.scale, tooltip=_("Deletes some unnecessary files from folder")):
							tauon.clean_folder(gui.rename_index, True)
							inp.mouse_click = False

					ddt.text((x + 10 * gui.scale, y + 65 * gui.scale), _("PATH"), colours.box_text_label, 212)
					line = os.path.dirname(
						pctl.master_library[gui.rename_index].parent_folder_path.rstrip("\\/")).replace("\\","/") + "/"
					line = tauon.right_trunc(line, 12, 420 * gui.scale)
					line = clean_string(line)
					ddt.text((x + 60 * gui.scale, y + 65 * gui.scale), line, colours.grey(220), 211)

					ddt.text((x + 10 * gui.scale, y + 83 * gui.scale), _("OLD"), colours.box_text_label, 212)
					line = pctl.master_library[gui.rename_index].parent_folder_name
					line = clean_string(line)
					ddt.text((x + 60 * gui.scale, y + 83 * gui.scale), line, colours.grey(220), 211, max_w=420 * gui.scale)

					ddt.text((x + 10 * gui.scale, y + 101 * gui.scale), _("NEW"), colours.box_text_label, 212)
					line = parse_template2(tauon.rename_folder.text, pctl.master_library[gui.rename_index])
					ddt.text((x + 60 * gui.scale, y + 101 * gui.scale), line, colours.grey(220), 211, max_w=420 * gui.scale)

				if tauon.rename_track_box.active:
					tauon.rename_track_box.render()

				if tauon.sub_lyrics_box.active:
					tauon.sub_lyrics_box.render()

				if tauon.export_playlist_box.active:
					tauon.export_playlist_box.render()

				if tauon.trans_edit_box.active:
					tauon.trans_edit_box.render()

				if radiobox.active:
					radiobox.render()

				if gui.message_box:
					tauon.message_box.render()

				if prefs.show_nag:
					tauon.nagbox.draw()

				# SEARCH
				# if inp.key_ctrl_down and inp.key_v_press:
				# 	tauon.search_over.active = True

				tauon.search_over.render()
				search_over = tauon.search_over

				if keymaps.test("quick-find") and gui.quick_search_mode is False:
					if not tauon.search_over.active and not gui.box_over:
						gui.quick_search_mode = True
					if tauon.search_clear_timer.get() > 3:
						search_over.search_text.text = ""
					inp.input_text = ""
				elif (keymaps.test("quick-find") or (
						inp.key_esc_press and len(gui.editline) == 0)) or (inp.mouse_click and gui.quick_search_mode is True):
					gui.quick_search_mode = False
					search_over.search_text.text = ""

				# if (key_backslash_press or (inp.key_ctrl_down and key_f_press)) and gui.quick_search_mode is False:
				# 	if not tauon.search_over.active:
				# 		gui.quick_search_mode = True
				# 	if tauon.search_clear_timer.get() > 3:
				# 		search_over.search_text.text = ""
				# 	input_text = ""
				# elif ((key_backslash_press or (inp.key_ctrl_down and key_f_press)) or (
				# 		inp.key_esc_press and len(gui.editline) == 0)) or input.mouse_click and gui.quick_search_mode is True:
				# 	gui.quick_search_mode = False
				# 	search_over.search_text.text = ""

				if gui.quick_search_mode is True:
					rect2 = [0, window_size[1] - 85 * gui.scale, 420 * gui.scale, 25 * gui.scale]
					rect = [0, window_size[1] - 125 * gui.scale, 420 * gui.scale, 65 * gui.scale]
					rect[0] = int(window_size[0] / 2) - int(rect[2] / 2)
					rect2[0] = rect[0]

					ddt.rect((rect[0] - 2, rect[1] - 2, rect[2] + 4, rect[3] + 4), colours.box_border)  # [220, 100, 5, 255]
					# ddt.rect_r((rect[0], rect[1], rect[2], rect[3]), [255,120,5,255], True)

					ddt.text_background_colour = colours.box_background
					# ddt.text_background_colour = ColourRGBA(255,120,5,255)
					# ddt.text_background_colour = ColourRGBA(220,100,5,255)
					ddt.rect(rect, colours.box_background)

					if len(inp.input_text) > 0:
						gui.search_index = -1

					if inp.backspace_press and search_over.search_text.text == "":
						gui.quick_search_mode = False

					if len(search_over.search_text.text) == 0:
						gui.search_error = False

					if len(search_over.search_text.text) != 0 and search_over.search_text.text[0] == "/":
						# if "/love" in search_over.search_text.text:
						#     line = "last.fm loved tracks from user. Format: /love <username>"
						# else:
						line = _("Folder filter mode. Enter path segment.")
						ddt.text((rect[0] + 23 * gui.scale, window_size[1] - 87 * gui.scale), line, ColourRGBA(220, 220, 220, 100), 312)
					else:
						line = _("UP / DOWN to navigate. SHIFT + RETURN for new playlist.")
						if len(search_over.search_text.text) == 0:
							line = _("Quick find")
						ddt.text((rect[0] + int(rect[2] / 2), window_size[1] - 87 * gui.scale, 2), line, colours.box_text_label, 312)

						# ddt.draw_text((rect[0] + int(rect[2] / 2), window_size[1] - 118 * gui.scale, 2), "Find",
						#           colours.grey(90), 214)

					# if len(pctl.track_queue) > 0:

					# if inp.input_text == 'A':
					#     search_text.text = pctl.playing_object().artist
					#     inp.input_text = ""

					if gui.search_error:
						ddt.rect([rect[0], rect[1], rect[2], 30 * gui.scale], ColourRGBA(180, 40, 40, 255))
						ddt.text_background_colour = ColourRGBA(180, 40, 40, 255)  # alpha_blend(ColourRGBA(255,0,0,25), ddt.text_background_colour)
					# if input.backspace_press:
					#     gui.search_error = False

					search_over.search_text.draw(rect[0] + 8 * gui.scale, rect[1] + 6 * gui.scale, colours.grey(250), font=213)

					if (inp.key_shift_down or (
							len(search_over.search_text.text) > 0 and search_over.search_text.text[0] == "/")) and inp.key_return_press:
						inp.key_return_press = False
						playlist = []
						if len(search_over.search_text.text) > 0:
							if search_over.search_text.text[0] == "/":

								if search_over.search_text.text.lower() == "/random" or search_over.search_text.text.lower() == "/shuffle":
									tauon.gen_500_random(pctl.active_playlist_viewing)
								elif search_over.search_text.text.lower() == "/top" or search_over.search_text.text.lower() == "/most":
									tauon.gen_top_100(pctl.active_playlist_viewing)
								elif search_over.search_text.text.lower() == "/length" or search_over.search_text.text.lower() == "/duration" \
										or search_over.search_text.text.lower() == "/len":
									tauon.gen_sort_len(pctl.active_playlist_viewing)
								else:

									if search_over.search_text.text[-1] == "/":
										tt_title = search_over.search_text.text.replace("/", "")
									else:
										search_over.search_text.text = search_over.search_text.text.replace("/", "")
										tt_title = search_over.search_text.text
									search_over.search_text.text = search_over.search_text.text.lower()
									for item in pctl.default_playlist:
										if search_over.search_text.text in pctl.master_library[item].parent_folder_path.lower():
											playlist.append(item)
									if len(playlist) > 0:
										pctl.multi_playlist.append(tauon.pl_gen(title=tt_title, playlist_ids=copy.deepcopy(playlist)))
										pctl.switch_playlist(len(pctl.multi_playlist) - 1)

							else:
								search_terms = search_over.search_text.text.lower().split()
								for item in pctl.default_playlist:
									tr = pctl.get_track(item)
									line = " ".join(
										[
											tr.title, tr.artist, tr.album, tr.fullpath,
											tr.composer, tr.comment, tr.album_artist, tr.misc.get("artist_sort", "")]).lower()

									# if prefs.diacritic_search and all([ord(c) < 128 for c in search_over.search_text.text]):
									#     line = str(unidecode(line))

									if all(word in line for word in search_terms):
										playlist.append(item)
								if len(playlist) > 0:
									pctl.multi_playlist.append(tauon.pl_gen(
										title=_("Search Results"),
										playlist_ids=copy.deepcopy(playlist)))
									pctl.gen_codes[pctl.pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[
										pctl.active_playlist_viewing].title + "\" f\"" + search_over.search_text.text + "\""
									pctl.switch_playlist(len(pctl.multi_playlist) - 1)
							search_over.search_text.text = ""
							gui.quick_search_mode = False

					if (len(inp.input_text) > 0 and not gui.search_error) or inp.key_down_press is True or inp.backspace_press \
							or gui.force_search:

						gui.pl_update = 1

						if gui.force_search:
							gui.search_index = 0

						if inp.backspace_press:
							gui.search_index = 0

						if len(search_over.search_text.text) > 0 and search_over.search_text.text[0] != "/":
							oi = gui.search_index

							while gui.search_index < len(pctl.default_playlist) - 1:
								gui.search_index += 1
								if gui.search_index > len(pctl.default_playlist) - 1:
									gui.search_index = 0

								search_terms = search_over.search_text.text.lower().split()
								tr = pctl.get_track(pctl.default_playlist[gui.search_index])
								line = " ".join(
									[tr.title, tr.artist, tr.album, tr.fullpath, tr.composer, tr.comment,
									tr.album_artist, tr.misc.get("artist_sort", "")]).lower()

								# if prefs.diacritic_search and all([ord(c) < 128 for c in search_over.search_text.text]):
								#     line = str(unidecode(line))

								if all(word in line for word in search_terms):

									pctl.selected_in_playlist = gui.search_index
									if len(pctl.default_playlist) > 10 and gui.search_index > 10:
										pctl.playlist_view_position = gui.search_index - 7
										logging.debug("Position changed by search")
									else:
										pctl.playlist_view_position = 0

									if gui.combo_mode:
										pctl.show_selected()
									gui.search_error = False

									break

							else:
								gui.search_index = oi
								if len(inp.input_text) > 0 or gui.force_search:
									gui.search_error = True
								if inp.key_down_press:
									tauon.bottom_playlist2.pulse()

							gui.force_search = False

					if inp.key_up_press is True \
							and not inp.key_shiftr_down \
							and not inp.key_shift_down \
							and not inp.key_ctrl_down \
							and not inp.key_rctrl_down \
							and not inp.key_meta \
							and not inp.key_lalt \
							and not inp.key_ralt:

						gui.pl_update = 1
						oi = gui.search_index

						while gui.search_index > 1:
							gui.search_index -= 1
							gui.search_index = min(gui.search_index, len(pctl.default_playlist) - 1)
							search_terms = search_over.search_text.text.lower().split()
							line = pctl.master_library[pctl.default_playlist[gui.search_index]].title.lower() + \
								pctl.master_library[pctl.default_playlist[gui.search_index]].artist.lower() \
								+ pctl.master_library[pctl.default_playlist[gui.search_index]].album.lower() + \
								pctl.master_library[pctl.default_playlist[gui.search_index]].filename.lower()

							if prefs.diacritic_search and all([ord(c) < 128 for c in search_over.search_text.text]):
								line = str(unidecode(line))

							if all(word in line for word in search_terms):

								pctl.selected_in_playlist = gui.search_index
								if len(pctl.default_playlist) > 10 and gui.search_index > 10:
									pctl.playlist_view_position = gui.search_index - 7
									logging.debug("Position changed by search")
								else:
									pctl.playlist_view_position = 0
								if gui.combo_mode:
									pctl.show_selected()
								break
						else:
							gui.search_index = oi
							tauon.edge_playlist2.pulse()

					if inp.key_return_press is True and gui.search_index > -1:
						gui.pl_update = 1
						pctl.jump(pctl.default_playlist[gui.search_index], gui.search_index)
						if prefs.album_mode:
							tauon.goto_album(pctl.playlist_playing_position)
						gui.quick_search_mode = False
						tauon.search_clear_timer.set()
				elif not tauon.search_over.active:
					if inp.key_up_press and ((
						not inp.key_shiftr_down \
						and not inp.key_shift_down \
						and not inp.key_ctrl_down \
						and not inp.key_rctrl_down \
						and not inp.key_meta \
						and not inp.key_lalt \
						and not inp.key_ralt) or (keymaps.test("shift-up"))):

						pctl.show_selected()
						gui.pl_update = 1

						if not keymaps.test("shift-up"):
							if pctl.selected_in_playlist > 0:
								pctl.selected_in_playlist -= 1
								pctl.r_menu_index = pctl.default_playlist[pctl.selected_in_playlist]
							gui.shift_selection = []

						if pctl.playlist_view_position > 0 and pctl.selected_in_playlist < pctl.playlist_view_position + 2:
							pctl.playlist_view_position -= 1
							logging.debug("Position changed by key up")

							tauon.scroll_hide_timer.set()
							gui.frame_callback_list.append(TestTimer(0.9))

						pctl.selected_in_playlist = min(pctl.selected_in_playlist, len(pctl.default_playlist))

					if pctl.selected_in_playlist < len(pctl.default_playlist) and (
						(inp.key_down_press and \
						not inp.key_shiftr_down \
						and not inp.key_shift_down \
						and not inp.key_ctrl_down \
						and not inp.key_rctrl_down \
						and not inp.key_meta \
						and not inp.key_lalt \
						and not inp.key_ralt) or keymaps.test("shift-down")):

						pctl.show_selected()
						gui.pl_update = 1

						if not keymaps.test("shift-down"):
							if pctl.selected_in_playlist < len(pctl.default_playlist) - 1:
								pctl.selected_in_playlist += 1
								pctl.r_menu_index = pctl.default_playlist[pctl.selected_in_playlist]
							gui.shift_selection = []

						if pctl.playlist_view_position < len(
								pctl.default_playlist) and pctl.selected_in_playlist > pctl.playlist_view_position + gui.playlist_view_length - 3 - gui.row_extra:
							pctl.playlist_view_position += 1
							logging.debug("Position changed by key down")

							tauon.scroll_hide_timer.set()
							gui.frame_callback_list.append(TestTimer(0.9))

						pctl.selected_in_playlist = max(pctl.selected_in_playlist, 0)

					if inp.key_return_press and not pref_box.enabled and not radiobox.active and not tauon.trans_edit_box.active and not gui.timed_lyrics_editing_now \
						and not (gui.showcase_mode and gui.timed_lyrics_edit_view):
						gui.pl_update = 1
						if pctl.selected_in_playlist > len(pctl.default_playlist) - 1:
							pctl.selected_in_playlist = 0
							gui.shift_selection = []
						if pctl.default_playlist:
							pctl.jump(pctl.default_playlist[pctl.selected_in_playlist], pctl.selected_in_playlist)
							if prefs.album_mode:
								tauon.goto_album(pctl.playlist_playing_position)
			elif gui.mode == 3:
				if (inp.key_shift_down and inp.mouse_click) or inp.middle_click:
					if prefs.mini_mode_mode == 4:
						prefs.mini_mode_mode = 1
						window_size[0] = int(330 * gui.scale)
						window_size[1] = int(330 * gui.scale)
						sdl3.SDL_SetWindowMinimumSize(t_window, window_size[0], window_size[1])
						sdl3.SDL_SetWindowSize(t_window, window_size[0], window_size[1])
					else:
						prefs.mini_mode_mode = 4
						window_size[0] = int(320 * gui.scale)
						window_size[1] = int(90 * gui.scale)
						sdl3.SDL_SetWindowMinimumSize(t_window, window_size[0], window_size[1])
						sdl3.SDL_SetWindowSize(t_window, window_size[0], window_size[1])

				if prefs.mini_mode_mode == 5:
					tauon.mini_mode3.render()
				elif prefs.mini_mode_mode == 4:
					tauon.mini_mode2.render()
				else:
					tauon.mini_mode.render()

			t = tauon.toast_love_timer.get()
			if t < 1.8 and gui.toast_love_object is not None:
				track = gui.toast_love_object

				ww = 0
				if gui.lsp:
					ww = gui.lspw

				rect = (ww + 5 * gui.scale, gui.panelY + 5 * gui.scale, 235 * gui.scale, 39 * gui.scale)
				tauon.fields.add(rect)

				if tauon.coll(rect):
					tauon.toast_love_timer.force_set(10)
				else:
					ddt.rect(grow_rect(rect, 2 * gui.scale), colours.box_border)
					ddt.rect(rect, colours.queue_card_background)

					# fqo = copy.copy(pctl.force_queue[-1])

					ddt.text_background_colour = colours.queue_card_background

					if gui.toast_love_added:
						text = _("Loved track")
						gui.heart_notify_icon.render(rect[0] + 9 * gui.scale, rect[1] + 8 * gui.scale, ColourRGBA(250, 100, 100, 255))
					else:
						text = _("Un-Loved track")
						gui.heart_notify_break_icon.render(
							rect[0] + 9 * gui.scale, rect[1] + 7 * gui.scale,
							ColourRGBA(150, 150, 150, 255))

					ddt.text_background_colour = colours.queue_card_background
					ddt.text((rect[0] + 42 * gui.scale, rect[1] + 3 * gui.scale), text, colours.box_text, 313)
					ddt.text(
						(rect[0] + 42 * gui.scale, rect[1] + 20 * gui.scale),
						f"{track.track_number}. {track.artist} - {track.title}".strip(".- "), colours.box_text_label,
						13, max_w=rect[2] - 50 * gui.scale)

			t = tauon.queue_add_timer.get()
			if t < 2.5 and gui.toast_queue_object:
				track = pctl.get_track(gui.toast_queue_object.track_id)

				ww = 0
				if gui.lsp:
					ww = gui.lspw
				if tauon.search_over.active:
					ww = window_size[0] // 2 - (215 * gui.scale // 2)

				rect = (ww + 5 * gui.scale, gui.panelY + 5 * gui.scale, 215 * gui.scale, 39 * gui.scale)
				tauon.fields.add(rect)

				if tauon.coll(rect):
					tauon.queue_add_timer.force_set(10)
				elif len(pctl.force_queue) > 0:

					fqo = copy.copy(pctl.force_queue[-1])

					ddt.rect(grow_rect(rect, 2 * gui.scale), colours.box_border)
					ddt.rect(rect, colours.queue_card_background)

					ddt.text_background_colour = colours.queue_card_background
					top_text = _("Track")
					if gui.queue_toast_plural:
						top_text = "Album"
						fqo.type = 1
					if pctl.force_queue[-1].type == 1:
						top_text = "Album"

					tauon.queue_box.draw_card(
						rect[0] - 8 * gui.scale, 0, 160 * gui.scale, 210 * gui.scale,
						rect[1] + 1 * gui.scale, track, fqo, True, False)

					ddt.text_background_colour = colours.queue_card_background
					ddt.text(
						(rect[0] + rect[2] - 50 * gui.scale, rect[1] + 3 * gui.scale, 2), f"{top_text} added",
						colours.box_text_label, 11)
					ddt.text(
						(rect[0] + rect[2] - 50 * gui.scale, rect[1] + 15 * gui.scale, 2), "to queue",
						colours.box_text_label, 11)

			t = tauon.toast_mode_timer.get()
			if t < gui.toast_length:

				wid = ddt.get_text_w(gui.mode_toast_text, 313)
				wid = max(round(68 * gui.scale), wid)

				ww = round(7 * gui.scale)
				if gui.lsp and not gui.combo_mode:
					ww += gui.lspw

				rect = (ww + 8 * gui.scale, gui.panelY + 15 * gui.scale, wid + 20 * gui.scale, 25 * gui.scale)
				tauon.fields.add(rect)

				if tauon.coll(rect):
					tauon.toast_mode_timer.force_set(10)
				else:
					ddt.rect(grow_rect(rect, round(2 * gui.scale)), colours.grey(60))
					ddt.rect(rect, colours.queue_card_background)

					ddt.text_background_colour = colours.queue_card_background
					ddt.text((rect[0] + (rect[2] // 2), rect[1] + 4 * gui.scale, 2), gui.mode_toast_text, colours.grey(230), 313)

			# Render Menus-------------------------------
			for instance in Menu.instances:
				instance.render()

			if tauon.view_box.active:
				tauon.view_box.render()

			tauon.tool_tip.render()
			tauon.tool_tip2.render()

			if tauon.console.show:
				rect = (20 * gui.scale, 40 * gui.scale, 580 * gui.scale, 200 * gui.scale)
				ddt.rect(rect, ColourRGBA(0, 0, 0, 245))

				yy = rect[3] + 15 * gui.scale
				u = False
				for record in reversed(tauon.log.log_history):

					if yy < rect[1] + 5 * gui.scale:
						break

					text_colour = ColourRGBA(60, 255, 60, 255)
					message = tauon.log.format(record)

					t = record.created
					d = time.time() - t
					dt = time.localtime(t)

					fade = 255
					if d > 2:
						fade = 200

					text_colour = ColourRGBA(120, 120, 120, fade)
					if record.levelno == 10:
						text_colour = ColourRGBA(80, 80, 80, fade)
					if record.levelno == 30:
						text_colour = ColourRGBA(230, 190, 90, fade)
					if record.levelno == 40:
						text_colour = ColourRGBA(255, 120, 90, fade)
					if record.levelno == 50:
						text_colour = ColourRGBA(255, 90, 90, fade)

					time_colour = ColourRGBA(255, 80, 160, fade)

					w = ddt.text(
						(rect[0] + 10 * gui.scale, yy), time.strftime("%H:%M:%S", dt), time_colour, 311,
						rect[2] - 60 * gui.scale, bg=ColourRGBA(5,5,5,255))

					ddt.text((w + rect[0] + 17 * gui.scale, yy), message, text_colour, 311, rect[2] - 60 * gui.scale, bg=ColourRGBA(5,5,5,255))
					yy -= 14 * gui.scale
				if u:
					gui.delay_frame(5)

				if pctl.draw.button("Copy", rect[0] + rect[2] - 55 * gui.scale, rect[1] + rect[3] - 30 * gui.scale):
					text = ""
					for record in tauon.log.log_history[-50:]:
						t = record.created
						dt = time.localtime(t)
						text += time.strftime("%H:%M:%S", dt) + " " + tauon.log.format(record) + "\n"
					copy_to_clipboard(text)
					tauon.show_message(_("Lines copied to clipboard"), mode="done")

			if gui.cursor_is != gui.cursor_want:
				gui.cursor_is = gui.cursor_want

				if gui.cursor_is == 0:
					sdl3.SDL_SetCursor(gui.cursor_standard)
				elif gui.cursor_is == 1:
					sdl3.SDL_SetCursor(gui.cursor_shift)
				elif gui.cursor_is == 2:
					sdl3.SDL_SetCursor(gui.cursor_text)
				elif gui.cursor_is == 3:
					sdl3.SDL_SetCursor(gui.cursor_hand)
				elif gui.cursor_is == 4:
					sdl3.SDL_SetCursor(gui.cursor_br_corner)
				elif gui.cursor_is == 8:
					sdl3.SDL_SetCursor(gui.cursor_right_side)
				elif gui.cursor_is == 9:
					sdl3.SDL_SetCursor(gui.cursor_top_side)
				elif gui.cursor_is == 10:
					sdl3.SDL_SetCursor(gui.cursor_left_side)
				elif gui.cursor_is == 11:
					sdl3.SDL_SetCursor(gui.cursor_bottom_side)

			tauon.input_sdl.test_capture_mouse()
			tauon.input_sdl.mouse_capture_want = False

			# # Quick view
			# quick_view_box.render()

			# Drag icon next to cursor
			if inp.quick_drag and inp.mouse_down and not point_proximity_test(
				gui.drag_source_position, inp.mouse_position, 15 * gui.scale):
				i_x, i_y = tauon.input_sdl.mouse()
				gui.drag_source_position = (0, 0)

				block_size = round(10 * gui.scale)
				x_offset = round(20 * gui.scale)
				y_offset = round(1 * gui.scale)

				if len(gui.shift_selection) == 1:  # Single track
					ddt.rect((i_x + x_offset, i_y + y_offset, block_size, block_size), ColourRGBA(160, 140, 235, 240))
				elif inp.key_ctrl_down:  # Add to queue undrouped
					small_block = round(6 * gui.scale)
					spacing = round(2 * gui.scale)
					ddt.rect((i_x + x_offset, i_y + y_offset, small_block, small_block), ColourRGBA(160, 140, 235, 240))
					ddt.rect(
						(i_x + x_offset + spacing + small_block, i_y + y_offset, small_block, small_block), ColourRGBA(160, 140, 235, 240))
					ddt.rect(
						(i_x + x_offset, i_y + y_offset + spacing + small_block, small_block, small_block), ColourRGBA(160, 140, 235, 240))
					ddt.rect(
						(i_x + x_offset + spacing + small_block, i_y + y_offset + spacing + small_block, small_block, small_block),
						ColourRGBA(160, 140, 235, 240))
					ddt.rect(
						(i_x + x_offset, i_y + y_offset + spacing + small_block + spacing + small_block, small_block, small_block),
						ColourRGBA(160, 140, 235, 240))
					ddt.rect(
						(i_x + x_offset + spacing + small_block,
						i_y + y_offset + spacing + small_block + spacing + small_block,
						small_block, small_block), ColourRGBA(160, 140, 235, 240))

				else:  # Multiple tracks
					long_block = round(25 * gui.scale)
					ddt.rect((i_x + x_offset, i_y + y_offset, block_size, long_block), ColourRGBA(160, 140, 235, 240))

				# gui.update += 1
				gui.update_on_drag = True

			# Drag pl tab next to cursor
			if (tauon.playlist_box.drag) and inp.mouse_down and not point_proximity_test(
				gui.drag_source_position, inp.mouse_position, 10 * gui.scale):
				i_x, i_y = tauon.input_sdl.mouse()
				gui.drag_source_position = (0, 0)
				ddt.rect(
					(i_x + 20 * gui.scale, i_y + 3 * gui.scale, int(50 * gui.scale), int(15 * gui.scale)), ColourRGBA(50, 50, 50, 225))
				# ddt.rect_r((i_x + 20 * gui.scale, i_y + 1 * gui.scale, int(60 * gui.scale), int(15 * gui.scale)), [240, 240, 240, 255], True)
				# ddt.draw_text((i_x + 75 * gui.scale, i_y - 0 * gui.scale, 1), pctl.multi_playlist[tauon.playlist_box.drag_on].title, ColourRGBA(30, 30, 30, 255), 212, bg=[240, 240, 240, 255])
			if tauon.radio_view.drag and not point_proximity_test(tauon.radio_view.click_point, inp.mouse_position, round(4 * gui.scale)):
				ddt.rect((
					inp.mouse_position[0] + round(8 * gui.scale), inp.mouse_position[1] - round(8 * gui.scale), 48 * gui.scale,
					14 * gui.scale), colours.grey(70))
			if (gui.set_label_hold != -1) and inp.mouse_down:

				gui.update_on_drag = True

				if not point_proximity_test(gui.set_label_point, inp.mouse_position, 3):
					i_x, i_y = tauon.input_sdl.mouse()
					gui.set_label_point = (0, 0)

					w = ddt.get_text_w(gui.pl_st[gui.set_label_hold][0], 212)
					w = max(w, 45 * gui.scale)
					ddt.rect(
						(i_x + 25 * gui.scale, i_y + 1 * gui.scale, w + int(20 * gui.scale), int(15 * gui.scale)),
						ColourRGBA(240, 240, 240, 255))
					ddt.text(
						(i_x + 25 * gui.scale + w + int(20 * gui.scale) - 4 * gui.scale, i_y - 0 * gui.scale, 1),
						gui.pl_st[gui.set_label_hold][0], ColourRGBA(30, 30, 30, 255), 212, bg=ColourRGBA(240, 240, 240, 255))

			inp.input_text = ""
			gui.update -= 1

			# logging.info("FRAME " + str(tauon.core_timer.get()))
			gui.update = min(gui.update, 1)
			gui.present = True

			sdl3.SDL_SetRenderTarget(renderer, None)
			sdl3.SDL_RenderTexture(renderer, gui.main_texture, None, gui.tracklist_texture_rect)

			if gui.turbo:
				gui.level_update = True

		# if gui.vis == 1 and pctl.playing_state != PlayingState.PLAYING and gui.level_peak != [0, 0] and gui.turbo:
		# 	# logging.info(gui.level_peak)
		# 	gui.time_passed = gui.level_time.hit()
		# 	if gui.time_passed > 1:
		# 		gui.time_passed = 0
		# 	while gui.time_passed > 0.01:
		# 		gui.level_peak[1] -= 0.5
		# 		if gui.level_peak[1] < 0:
		# 			gui.level_peak[1] = 0
		# 		gui.level_peak[0] -= 0.5
		# 		if gui.level_peak[0] < 0:
		# 			gui.level_peak[0] = 0
		# 		gui.time_passed -= 0.020
		# 	gui.level_update = True

		# gui.turbo = True
		# gui.vis = 5
		# gui.level_update = True

		if gui.level_update is True and not resize_mode and gui.mode != 3:
			gui.level_update = False

			sdl3.SDL_SetRenderTarget(renderer, None)
			if not gui.present:
				sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
				sdl3.SDL_SetRenderDrawColor(
					renderer, 0, 0,
					0, 0)
				sdl3.SDL_RenderClear(renderer)
				sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
				sdl3.SDL_RenderTexture(renderer, gui.main_texture, None, gui.tracklist_texture_rect)
				gui.present = True

			if gui.vis == 5:
				# milky
				pass

			if gui.vis == 3:
				# Scrolling spectrogram

				# if not vis_update:
				#     logging.info("No UPDATE " + str(random.randint(1,50)))
				if len(gui.spec2_buffers) > 0 and gui.spec2_timer.get() > 0.04:
					# gui.spec2_timer.force_set(gui.spec2_timer.get() - 0.04)
					gui.spec2_timer.set()
					vis_update = True

				if len(gui.spec2_buffers) > 0 and vis_update:
					vis_update = False

					sdl3.SDL_SetRenderTarget(renderer, gui.spec2_tex)
					for i, value in enumerate(gui.spec2_buffers[0]):
						ddt.rect(
							[gui.spec2_position, i, 1, 1],
							colours.vis_bg)

					del gui.spec2_buffers[0]

					gui.spec2_position += 1

					if gui.spec2_position > gui.spec2_w - 1:
						gui.spec2_position = 0

					sdl3.SDL_SetRenderTarget(renderer, None)

				#
				# else:
				#     logging.info("animation stall" + str(random.randint(1, 10)))

				if prefs.spec2_scroll:

					gui.spec2_source.x = 0
					gui.spec2_source.y = 0
					gui.spec2_source.w = gui.spec2_position
					gui.spec2_dest.x = gui.spec2_rec.x + gui.spec2_rec.w - gui.spec2_position
					gui.spec2_dest.w = gui.spec2_position
					sdl3.SDL_RenderTexture(renderer, gui.spec2_tex, gui.spec2_source, gui.spec2_dest)

					gui.spec2_source.x = gui.spec2_position
					gui.spec2_source.y = 0
					gui.spec2_source.w = gui.spec2_rec.w - gui.spec2_position
					gui.spec2_dest.x = gui.spec2_rec.x
					gui.spec2_dest.w = gui.spec2_rec.w - gui.spec2_position
					sdl3.SDL_RenderTexture(renderer, gui.spec2_tex, gui.spec2_source, gui.spec2_dest)
				else:
					sdl3.SDL_RenderTexture(renderer, gui.spec2_tex, None, gui.spec2_rec)

				if pref_box.enabled:
					#ddt.rect((gui.spec2_rec.x, gui.spec2_rec.y, gui.spec2_rec.w, gui.spec2_rec.h), ColourRGBA(0, 0, 0, 90))
					logging.info("spectrogram box")
					ddt.rect((gui.spec2_rec.x, gui.spec2_rec.y, gui.spec2_rec.w, gui.spec2_rec.h), colours.vis_bg)

			if gui.vis == 4 and gui.draw_vis4_top:
				showcase.render_vis(True)
				# gui.level_update = False

			if gui.vis == 2 and gui.spec is not None:
				# Standard spectrum visualiser
				if gui.update_spec == 0 and pctl.playing_state != PlayingState.PAUSED:
					if tauon.vis_decay_timer.get() > 0.007:  # Controls speed of decay after stop
						tauon.vis_decay_timer.set()
						for i in range(len(gui.spec)):
							if gui.s_spec[i] > 0:
								if gui.spec[i] > 0:
									gui.spec[i] -= 1
								gui.level_update = True
					else:
						gui.level_update = True

				if tauon.vis_rate_timer.get() > 0.027:  # Limit the change rate #to 60 fps
					tauon.vis_rate_timer.set()

					if spec_smoothing and pctl.playing_state != PlayingState.STOPPED:
						for i in range(len(gui.spec)):
							if gui.spec[i] > gui.s_spec[i]:
								gui.s_spec[i] += 1
								if abs(gui.spec[i] - gui.s_spec[i]) > 4:
									gui.s_spec[i] += 1
								if abs(gui.spec[i] - gui.s_spec[i]) > 6:
									gui.s_spec[i] += 1
								if abs(gui.spec[i] - gui.s_spec[i]) > 8:
									gui.s_spec[i] += 1
							elif gui.spec[i] == gui.s_spec[i]:
								pass
							elif gui.spec[i] < gui.s_spec[i] > 0:
								gui.s_spec[i] -= 1
								if abs(gui.spec[i] - gui.s_spec[i]) > 4:
									gui.s_spec[i] -= 1
								if abs(gui.spec[i] - gui.s_spec[i]) > 6:
									gui.s_spec[i] -= 1
								if abs(gui.spec[i] - gui.s_spec[i]) > 8:
									gui.s_spec[i] -= 1

						if pctl.playing_state == PlayingState.STOPPED and check_equal(gui.s_spec):
							gui.level_update = True
							time.sleep(0.008)
					else:
						gui.s_spec = gui.spec
				else:
					pass

				if not gui.test:
					sdl3.SDL_SetRenderTarget(renderer, gui.spec1_tex)

					# ddt.rect_r(gui.spec_rect, colours.top_panel_background, True)
					ddt.rect((0, 0, gui.spec_w, gui.spec_h), colours.vis_bg)

					# xx = 0
					gui.bar.x = 0
					on = 0

					sdl3.SDL_SetRenderDrawColor(
						renderer, colours.vis_colour.r,
						colours.vis_colour.g, colours.vis_colour.b,
						colours.vis_colour.a)

					for item in gui.s_spec:
						if on > 19:
							break
						on += 1

						item -= 1

						if item < 1:
							gui.bar.x += round(4 * gui.scale)
							continue

						item = min(item, 20)

						if gui.scale >= 2:
							item = round(item * gui.scale)

						gui.bar.y = 0 + gui.spec_h - item
						gui.bar.h = item

						sdl3.SDL_RenderFillRect(renderer, gui.bar)

						gui.bar.x += round(4 * gui.scale)

					if tauon.pref_box.enabled:
						ddt.rect((0, 0, gui.spec_w, gui.spec_h), ColourRGBA(0, 0, 0, 90))

					sdl3.SDL_SetRenderTarget(renderer, None)
					sdl3.SDL_RenderTexture(renderer, gui.spec1_tex, None, gui.spec1_rec)

			if gui.vis == 1:
				if prefs.backend == 2 or True:
					if pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
						# gui.level_update = True
						while tauon.level_train and tauon.level_train[0][0] < time.time():

							l = tauon.level_train[0][1]
							r = tauon.level_train[0][2]

							gui.level_peak[0] = max(r, gui.level_peak[0])
							gui.level_peak[1] = max(l, gui.level_peak[1])

							del tauon.level_train[0]

					else:
						tauon.level_train.clear()

				sdl3.SDL_SetRenderTarget(renderer, gui.spec_level_tex)

				x = window_size[0] - 20 * gui.scale - gui.offset_extra
				y = gui.level_y
				w = gui.level_w
				s = gui.level_s

				y = 0

				gui.spec_level_rec.x = round(x - 70 * gui.scale)
				ddt.rect_a((0, 0), (79 * gui.scale, 18 * gui.scale), colours.grey(10))

				x = round(gui.level_ww - 9 * gui.scale)
				y = 10 * gui.scale

				if prefs.backend == 2 or True:
					if (gui.level_peak[0] > 0 or gui.level_peak[1] > 0):
						# gui.level_update = True
						if pctl.playing_time < 1:
							gui.delay_frame(0.032)

						if pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
							t = gui.level_decay_timer.hit()
							decay = 14 * t
							gui.level_peak[1] -= decay
							gui.level_peak[0] -= decay
						elif pctl.playing_state in (PlayingState.STOPPED, PlayingState.PAUSED):
							gui.level_update = True
							time.sleep(0.016)
							t = gui.level_decay_timer.hit()
							decay = 16 * t
							gui.level_peak[1] -= decay
							gui.level_peak[0] -= decay

				for t in range(12):
					met = False if gui.level_peak[0] < t else True
					if gui.level_peak[0] < 0.2:
						met = False
					if gui.level_meter_colour_mode == 1:
						if not met:
							cc = ColourRGBA(15, 10, 20, 255)
						else:
							cc = colorsys.hls_to_rgb(0.68 + (t * 0.015), 0.4, 0.7)
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)
					elif gui.level_meter_colour_mode == 2:
						if not met:
							cc = ColourRGBA(11, 11, 13, 255)
						else:
							cc = colorsys.hls_to_rgb(0.63 - (t * 0.015), 0.4, 0.7)
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)
					elif gui.level_meter_colour_mode == 3:
						if not met:
							cc = ColourRGBA(12, 6, 0, 255)
						else:
							cc = colorsys.hls_to_rgb(0.11 - (t * 0.010), 0.4, 0.7 + (t * 0.02))
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)
					elif gui.level_meter_colour_mode == 4:
						if not met:
							cc = ColourRGBA(10, 10, 10, 255)
						else:
							cc = colorsys.hls_to_rgb(0.3 - (t * 0.03), 0.4, 0.7 + (t * 0.02))
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)
					elif t < 7:
						cc = colours.level_green
						if met is False:
							cc = colours.level_1_bg
					elif t < 10:
						cc = colours.level_yellow
						if met is False:
							cc = colours.level_2_bg
					else:
						cc = colours.level_red
						if met is False:
							cc = colours.level_3_bg
					if gui.level > 0 and pctl.playing_state != PlayingState.STOPPED:
						pass
					ddt.rect_a(((x - (w * t) - (s * t)), y), (w, w), cc)

				y -= 7 * gui.scale
				for t in range(12):
					met = not gui.level_peak[1] < t
					if gui.level_peak[1] < 0.2:
						met = False

					if gui.level_meter_colour_mode == 1:
						if not met:
							cc = ColourRGBA(15, 10, 20, 255)
						else:
							cc = colorsys.hls_to_rgb(0.68 + (t * 0.015), 0.4, 0.7)
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

					elif gui.level_meter_colour_mode == 2:
						if not met:
							cc = ColourRGBA(11, 11, 13, 255)
						else:
							cc = colorsys.hls_to_rgb(0.63 - (t * 0.015), 0.4, 0.7)
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

					elif gui.level_meter_colour_mode == 3:
						if not met:
							cc = ColourRGBA(12, 6, 0, 255)
						else:
							cc = colorsys.hls_to_rgb(0.11 - (t * 0.010), 0.4, 0.7 + (t * 0.02))
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

					elif gui.level_meter_colour_mode == 4:
						if not met:
							cc = ColourRGBA(10, 10, 10, 255)
						else:
							cc = colorsys.hls_to_rgb(0.3 - (t * 0.03), 0.4, 0.7 + (t * 0.02))
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

					elif t < 7:
						cc = colours.level_green
						if met is False:
							cc = colours.level_1_bg
					elif t < 10:
						cc = colours.level_yellow
						if met is False:
							cc = colours.level_2_bg
					else:
						cc = colours.level_red
						if met is False:
							cc = colours.level_3_bg

					if gui.level > 0 and pctl.playing_state != PlayingState.STOPPED:
						pass
					ddt.rect_a(((x - (w * t) - (s * t)), y), (w, w), cc)

				sdl3.SDL_SetRenderTarget(renderer, None)
				sdl3.SDL_RenderTexture(renderer, gui.spec_level_tex, None, gui.spec_level_rec)

		if gui.present:
			sdl3.SDL_SetRenderTarget(renderer, None)
			sdl3.SDL_RenderPresent(renderer)

			gui.present = False

		# -------------------------------------------------------------------------------------------
		# Misc things to update every tick

		# Update d-bus metadata on Linux
		if (pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM)) and pctl.mpris is not None:
			pctl.mpris.update_progress()

		# GUI time ticker update
		if (pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM)) and gui.lowered is False:
			if int(pctl.playing_time) != int(pctl.last_playing_time):
				pctl.last_playing_time = pctl.playing_time
				tauon.bottom_bar1.seek_time = pctl.playing_time
				if not prefs.power_save or window_is_focused(tauon.t_window):
					gui.update = 1

		# Auto save play times to disk
		if pctl.total_playtime - time_last_save > 600:
			try:
				if bag.should_save_state:
					logging.info("Auto save playtime")
					with (user_directory / "star.p").open("wb") as file:
						pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)
				else:
					logging.info("Dev mode, skip auto saving playtime")
			except PermissionError:
				logging.exception("Permission error encountered while writing database")
				tauon.show_message(_("Permission error encountered while writing database"), "error")
			except Exception:
				logging.exception("Unknown error encountered while writing database")
			time_last_save = pctl.total_playtime

		# Always render at least one frame per minute (to avoid SDL bugs I guess)
		if tauon.min_render_timer.get() > 60:
			tauon.min_render_timer.set()
			gui.pl_update = 1
			gui.update += 1

		# Save power if the window is minimized
		if gui.lowered:
			time.sleep(0.2)

	if tauon.spot_ctl.playing:
		tauon.spot_ctl.control("stop")

	# Send scrobble if pending
	if tauon.lfm_scrobbler.queue and not tauon.lfm_scrobbler.running:
		tauon.lfm_scrobbler.start_queue()
		logging.info("Sending scrobble before close...")

	if gui.mode < 3:
		tauon.old_window_position = get_window_position(t_window)


	sdl3.SDL_DestroyTexture(gui.main_texture)
	sdl3.SDL_DestroyTexture(gui.tracklist_texture)
	sdl3.SDL_DestroyTexture(gui.spec2_tex)
	sdl3.SDL_DestroyTexture(gui.spec1_tex)
	sdl3.SDL_DestroyTexture(gui.spec_level_tex)
	ddt.clear_text_cache()
	tauon.clear_img_cache(False)

	sdl3.SDL_DestroyWindow(t_window)

	pctl.playerCommand = "unload"
	pctl.playerCommandReady = True

	if prefs.reload_play_state and pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED):
		logging.info("Saving play state...")
		prefs.reload_state = (pctl.playing_state, pctl.playing_time)

	if bag.should_save_state:
		with (user_directory / "star.p").open("wb") as file:
			pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)
		with (user_directory / "album-star.p").open("wb") as file:
			pickle.dump(tauon.album_star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)

	gui.gallery_positions[pctl.pl_to_id(pctl.active_playlist_viewing)] = gui.album_scroll_px
	tauon.save_state()

	date = datetime.date.today()
	if bag.should_save_state:
		with (user_directory / "star.p.backup").open("wb") as file:
			pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)
		with (user_directory / f"star.p.backup{date.month!s}").open("wb") as file:
			pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)

	if tauon.stream_proxy and tauon.stream_proxy.download_running:
		logging.info("Stopping stream...")
		tauon.stream_proxy.stop()
		time.sleep(2)

	try:
		if tauon.thread_manager.player_lock.locked():
			tauon.thread_manager.player_lock.release()
	except RuntimeError as e:
		if str(e) == "release unlocked lock":
			logging.error("RuntimeError: Attempted to release already unlocked player_lock")  # noqa: TRY400
		else:
			logging.exception("Unknown RuntimeError trying to release player_lock")
	except Exception:
		logging.exception("Unknown error trying to release player_lock")

	if tauon.radio_server is not None:
		try:
			tauon.radio_server.server_close()
		except Exception:
			logging.exception("Failed to close radio server")

	if sys.platform == "win32":
		tauon.tray.stop()
		if pctl.smtc:
			pctl.sm.unload()
	elif tauon.de_notify_support:
		try:
			tauon.song_notification.close()
			tauon.g_tc_notify.close()
			Notify.uninit()
		except Exception:
			logging.exception("uninit notification error")

	try:
		tauon.instance_lock.close()
	except Exception:
		logging.exception("No lock object to close")


	#sdl3.IMG_Quit()
	#sdl3.SDL_QuitSubSystem(sdl3.SDL_INIT_EVERYTHING)
	sdl3.SDL_Quit()
	#logging.info("SDL unloaded")

	exit_timer = Timer()
	exit_timer.set()

	if not tauon.quick_close:
		while tauon.thread_manager.check_playback_running():
			time.sleep(0.2)
			if exit_timer.get() > 2:
				logging.warning("Phazor unload timeout")
				break

		while tauon.lfm_scrobbler.running:
			time.sleep(0.2)
			tauon.lfm_scrobbler.running = False
			if exit_timer.get() > 15:
				logging.warning("Scrobble wait timeout")
				break

	if tauon.sleep_lock is not None:
		del tauon.sleep_lock
	if tauon.shutdown_lock is not None:
		del tauon.shutdown_lock
	if tauon.play_lock is not None:
		del tauon.play_lock

	if tauon.librespot_p:
		time.sleep(1)
		logging.info("Killing librespot")
		tauon.librespot_p.kill()
		#tauon.librespot_p.communicate()

	cache_dir = tmp_cache_dir()
	if os.path.isdir(cache_dir):
		# This check can be Windows only, lazy deletes are fine on Linux/macOS
		if sys.platform == "win32":
			while tauon.cachement.running:
				logging.warning("Waiting for caching to stop before deleting cache directory…")
				time.sleep(0.2)
		logging.info("Clearing tmp cache")
		shutil.rmtree(cache_dir)

	logging.info("Bye!")
