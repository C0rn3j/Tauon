from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from tauon.t_modules.t_extra import shooter

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon, TrackClass, LoadClass, Prefs, Timer
	from pathlib import Path

class PlayerCtl:
	"""Main class that controls playback (play, pause, stepping, playlists, queue etc). Sends commands to backend."""

	# C-PC
	def __init__(self, prefs: Prefs, master_count, master_library, gen_codes) -> None:

		self.running:           bool = True
		self.prefs:             Prefs = prefs

		# Database

		self.master_count = master_count
		self.total_playtime: float = 0
		self.master_library = master_library
		self.db_inc = random.randint(0, 10000)
		# self.star_library = star_library
		self.LoadClass = LoadClass

		self.gen_codes = gen_codes

		self.shuffle_pools = {}
		self.after_import_flag = False
		self.quick_add_target = None

		self.album_mbid_release_cache = {}
		self.album_mbid_release_group_cache = {}
		self.mbid_image_url_cache = {}

		# Misc player control

		self.url: str = ""
		# self.save_urls = url_saves
		self.tag_meta: str = ""
		self.found_tags = {}
		self.encoder_pause = 0

		# Playback

		self.track_queue = QUE
		self.queue_step = playing_in_queue
		self.playing_time = 0
		self.playlist_playing_position = playlist_playing  # track in playlist that is playing
		if self.playlist_playing_position == None:
			self.playlist_playing_position = -1
		self.playlist_view_position = playlist_view_position
		self.selected_in_playlist = selected_in_playlist
		self.target_open = ""
		self.target_object = None
		self.start_time = 0
		self.b_start_time = 0
		self.playerCommand = ""
		self.playerSubCommand = ""
		self.playerCommandReady = False
		self.playing_state:    int = 0
		self.playing_length: float = 0
		self.jump_time = 0
		self.random_mode = prefs.random_mode
		self.repeat_mode = prefs.repeat_mode
		self.album_repeat_mode = prefs.album_repeat_mode
		self.album_shuffle_mode = prefs.album_shuffle_mode
		# self.album_shuffle_pool = []
		# self.album_shuffle_id = ""
		self.last_playing_time = 0
		self.multi_playlist = multi_playlist
		self.active_playlist_viewing = playlist_active  # the playlist index that is being viewed
		self.active_playlist_playing = playlist_active  # the playlist index that is playing from
		self.force_queue = p_force_queue  # []
		self.pause_queue = False
		self.left_time = 0
		self.left_index = 0
		self.player_volume = volume
		self.new_time = 0
		self.time_to_get = []
		self.a_time = 0
		self.b_time = 0
		# self.playlist_backup = []
		self.active_replaygain = 0
		self.auto_stop = False

		self.record_stream = False
		self.record_title = ""

		# Bass

		self.bass_devices = []
		self.set_device = 0

		self.gst_devices = []  # Display names
		self.gst_outputs = {}  # Display name : (sink, device)

		self.mpris = None
		self.tray_update = None
		self.eq = [0] * 2  # not used
		self.enable_eq = True  # not used

		self.playing_time_int = 0  # playing time but with no decimel

		self.windows_progress = None

		self.finish_transition = False
		# self.queue_target = 0
		self.start_time_target = 0

		self.decode_time = 0
		self.download_time = 0

		self.radio_meta_on = ""

		self.radio_scrobble_trip = True
		self.radio_scrobble_timer = Timer()

		self.radio_image_bin = None
		self.radio_rate_timer = Timer(2)
		self.radio_poll_timer = Timer(2)

		self.volume_update_timer = Timer()
		self.wake_past_time = 0

		self.regen_in_progress = False
		self.notify_in_progress = False

		self.radio_playlists = radio_playlists
		self.radio_playlist_viewing = radio_playlist_viewing
		self.tag_history = {}

		self.commit = None
		self.spot_playing = False

		self.buffering_percent = 0

	def notify_change(self):
		self.db_inc += 1
		tauon.bg_save()

	def update_tag_history(self):
		if prefs.auto_rec:
			self.tag_history[radiobox.song_key] = {
				"title": radiobox.dummy_track.title,
				"artist": radiobox.dummy_track.artist,
				"album": radiobox.dummy_track.album,
				# "image": pctl.radio_image_bin
			}

	def radio_progress(self):
		if radiobox.loaded_url and "radio.plaza.one" in radiobox.loaded_url and self.radio_poll_timer.get() > 0:
			self.radio_poll_timer.force_set(-10)
			response = requests.get("https://api.plaza.one/status")

			if response.status_code == 200:
				d = json.loads(response.text)
				if "song" in d:
					if "artist" in d["song"] and "title" in d["song"]:
						self.tag_meta = d["song"]["artist"] + " - " + d["song"]["title"]

		if self.tag_meta:
			if self.radio_rate_timer.get() > 7 and self.radio_meta_on != self.tag_meta:
				self.radio_rate_timer.set()
				self.radio_scrobble_trip = False
				self.radio_meta_on = self.tag_meta

				radiobox.dummy_track.art_url_key = ""
				radiobox.dummy_track.title = ""
				radiobox.dummy_track.date = ""
				radiobox.dummy_track.artist = ""
				radiobox.dummy_track.album = ""
				radiobox.dummy_track.lyrics = ""
				radiobox.dummy_track.date = ""

				tags = pctl.found_tags
				if "title" in tags:
					radiobox.dummy_track.title = tags["title"]
					if "artist" in tags:
						radiobox.dummy_track.artist = tags["artist"]
					if "year" in tags:
						radiobox.dummy_track.date = tags["year"]
					if "album" in tags:
						radiobox.dummy_track.album = tags["album"]

				elif self.tag_meta.count(
						"-") == 1 and not ":" in self.tag_meta and not "advert" in self.tag_meta.lower():
					artist, title = self.tag_meta.split("-")
					radiobox.dummy_track.title = title.strip()
					radiobox.dummy_track.artist = artist.strip()

				if self.tag_meta:
					radiobox.song_key = self.tag_meta
				else:
					radiobox.song_key = radiobox.dummy_track.artist + " - " + radiobox.dummy_track.title

				self.update_tag_history()
				if radiobox.loaded_url not in radiobox.websocket_source_urls:
					pctl.radio_image_bin = None
				logging.info("NEXT RADIO TRACK")

				try:
					get_radio_art()
				except Exception:
					logging.exception("Get art error")

				pctl.notify_update(mpris=False)
				if pctl.mpris:
					pctl.mpris.update(force=True)

				lfm_scrobbler.listen_track(radiobox.dummy_track)
				lfm_scrobbler.start_queue()

			if self.radio_scrobble_trip is False and self.radio_scrobble_timer.get() > 45:
				self.radio_scrobble_trip = True
				lfm_scrobbler.scrob_full_track(copy.deepcopy(radiobox.dummy_track))

	def update_shuffle_pool(self, pl_id):

		new_pool = copy.deepcopy(self.multi_playlist[id_to_pl(pl_id)][2])
		random.shuffle(new_pool)
		self.shuffle_pools[pl_id] = new_pool
		console.print("Refill shuffle pool")

	def notify_update_fire(self):
		if self.mpris is not None:
			self.mpris.update()
		if tauon.update_play_lock is not None:
			tauon.update_play_lock()
		# if self.tray_update is not None:
		#	 self.tray_update()
		self.notify_in_progress = False

	def notify_update(self, mpris=True):
		tauon.tray_releases += 1
		try:
			tauon.tray_lock.release()
		except Exception:
			logging.exception("Failed to release tray_lock")

		if mpris and smtc:
			tr = pctl.playing_object()
			if tr:
				state = 0
				if pctl.playing_state == 1:
					state = 1
				if pctl.playing_state == 2:
					state = 2
				image_path = ""
				try:
					image_path = tauon.thumb_tracks.path(tr)
				except Exception:
					logging.exception("Failed to set image_path from thumb_tracks.path")

				if image_path is None:
					image_path = ""

				image_path = image_path.replace("/", "\\")
				#logging.info(image_path)

				sm.update(
					state, tr.title.encode("utf-16"), len(tr.title), tr.artist.encode("utf-16"), len(tr.artist),
					image_path.encode("utf-16"), len(image_path))


		if self.mpris is not None and mpris is True:
			while self.notify_in_progress:
				time.sleep(0.01)
			self.notify_in_progress = True
			shoot = threading.Thread(target=self.notify_update_fire)
			shoot.daemon = True
			shoot.start()
		if prefs.art_bg or (gui.mode == 3 and prefs.mini_mode_mode == 5):
			tm.ready("style")

	def get_url(self, track_object):

		if track_object.file_ext == "TIDAL":
			return tidal.resolve_stream(track_object), None
		if track_object.file_ext == "PLEX":
			return plex.resolve_stream(track_object.url_key), None

		if track_object.file_ext == "JELY":
			return jellyfin.resolve_stream(track_object.url_key)

		if track_object.file_ext == "KOEL":
			return koel.resolve_stream(track_object.url_key)

		if track_object.file_ext == "SUB":
			return subsonic.resolve_stream(track_object.url_key)

		if track_object.file_ext == "TAU":
			return tau.resolve_stream(track_object.url_key), None

		return None, None

	def playing_playlist(self):
		return self.multi_playlist[self.active_playlist_playing][2]

	def playing_ready(self):
		return len(self.track_queue) > 0

	def selected_ready(self):
		return default_playlist and pctl.selected_in_playlist < len(default_playlist)

	def render_playlist(self):

		if taskbar_progress and msys and self.windows_progress:
			self.windows_progress.update(True)
		gui.pl_update = 1

	def show_selected(self):

		if gui.playlist_view_length < 1:
			return 0

		global shift_selection

		for i in range(len(self.multi_playlist[self.active_playlist_viewing][2])):

			if i == pctl.selected_in_playlist:

				if i < pctl.playlist_view_position:
					pctl.playlist_view_position = i - random.randint(2, int((gui.playlist_view_length / 3) * 2) + int(
						gui.playlist_view_length / 6))
					console.print("DEBUG: Position changed show selected (a)")
				elif abs(pctl.playlist_view_position - i) > gui.playlist_view_length:
					pctl.playlist_view_position = i
					console.print("DEBUG: Position changed show selected (b)")
					if i > 6:
						pctl.playlist_view_position -= 5
						console.print("DEBUG: Position changed show selected (c)")
					if i > gui.playlist_view_length * 1 and i + (gui.playlist_view_length * 2) < len(
							self.multi_playlist[self.active_playlist_viewing][2]) and i > 10:
						pctl.playlist_view_position = i - random.randint(2, int(gui.playlist_view_length / 3) * 2)
						console.print("DEBUG: Position changed show selected (d)")
					break

		self.render_playlist()

		return 0

	def g(self, id):
		"""Get track object by id"""
		return self.master_library[id]

	def sg(self, i, pl):
		"""Get track object by playlist and index"""
		if pl == -1:
			pl = self.active_playlist_viewing
		try:
			playlist = self.multi_playlist[pl][2]
			return self.g(playlist[i])
		except IndexError:
			logging.exception("Failed getting track object by playlist and index!")
		except Exception:
			logging.exception("Unknown error getting track object by playlist and index!")
		return None

	def show_object(self):
		"""The track to show in the metadata side panel"""

		target_track = None

		if self.playing_state == 3:
			return radiobox.dummy_track

		if 3 > self.playing_state > 0:
			target_track = self.playing_object()

		elif self.playing_state == 0 and prefs.meta_shows_selected:
			if -1 < pctl.selected_in_playlist < len(self.multi_playlist[self.active_playlist_viewing][2]):
				target_track = self.g(self.multi_playlist[self.active_playlist_viewing][2][pctl.selected_in_playlist])

		elif self.playing_state == 0 and prefs.meta_persists_stop:
			target_track = self.master_library[self.track_queue[self.queue_step]]

		if prefs.meta_shows_selected_always:
			if -1 < pctl.selected_in_playlist < len(self.multi_playlist[self.active_playlist_viewing][2]):
				target_track = self.g(self.multi_playlist[self.active_playlist_viewing][2][pctl.selected_in_playlist])

		return target_track

	def playing_object(self) -> TrackClass | None:

		if self.playing_state == 3:
			return radiobox.dummy_track

		if len(self.track_queue) > 0:
			return self.master_library[self.track_queue[self.queue_step]]
		else:
			return None

	def title_text(self):

		line = ""
		track = pctl.playing_object()
		if track:
			title = track.title
			artist = track.artist

			if not title:
				line = clean_string(track.filename)
			else:
				if artist != "":
					line += artist
				if title != "":
					if line != "":
						line += "  -  "
					line += title

			if pctl.playing_state == 3 and not title and not artist:
				return pctl.tag_meta

		return line

	def show(self):

		global shift_selection

		if not self.track_queue:
			return 0

	def show_current(
		self, select=True, playing=True, quiet=False, this_only=False, highlight=False, index=None,
		no_switch=False, folder_list=True):

		# logging.info("show------")
		# logging.info(select)
		# logging.info(playing)
		# logging.info(quiet)
		# logging.info(this_only)
		# logging.info(highlight)
		# logging.info("--------")
		console.print("DEBUG: Position set by show playing")

		global shift_selection

		if spot_ctl.coasting:
			sptr = tauon.dummy_track.misc.get("spotify-track-url")
			if sptr:

				for p in default_playlist:
					tr = pctl.g(p)
					if tr.misc.get("spotify-track-url") == sptr:
						index = tr.index
						break
				else:
					for i, pl in enumerate(pctl.multi_playlist):
						for p in pl[2]:
							tr = pctl.g(p)
							if tr.misc.get("spotify-track-url") == sptr:
								index = tr.index
								switch_playlist(i)
								break
						else:
							continue
						break
					else:
						return

		if not self.track_queue:
			return 0

		track_index = self.track_queue[self.queue_step]
		if index is not None:
			track_index = index

		# Switch to source playlist
		if not no_switch:
			if self.active_playlist_viewing != self.active_playlist_playing and (
					track_index not in self.multi_playlist[self.active_playlist_viewing][2]):
				switch_playlist(self.active_playlist_playing)

		if gui.playlist_view_length < 1:
			return 0

		for i in range(len(self.multi_playlist[self.active_playlist_viewing][2])):
			if self.multi_playlist[self.active_playlist_viewing][2][i] == track_index:

				if self.playlist_playing_position < len(self.multi_playlist[self.active_playlist_viewing][2]) and \
						self.active_playlist_viewing == self.active_playlist_playing and track_index == \
						self.multi_playlist[self.active_playlist_viewing][2][self.playlist_playing_position] and \
						i != self.playlist_playing_position:
					# continue
					i = self.playlist_playing_position

				if select:
					pctl.selected_in_playlist = i

				if playing:
					# Make the found track the playing track
					self.playlist_playing_position = i
					self.active_playlist_playing = self.active_playlist_viewing

				vl = gui.playlist_view_length
				if pctl.multi_playlist[pctl.active_playlist_viewing][6] == gui.playlist_current_visible_tracks_id:
					vl = gui.playlist_current_visible_tracks

				if not (
						quiet and self.playing_object().length < 15):  # or (abs(pctl.playlist_view_position - i) < vl - 1)):

					# Align to album if in view range (and folder titles are active)
					ap = get_album_info(i)[1][0]

					if not (quiet and pctl.playlist_view_position <= i <= pctl.playlist_view_position + vl) and (
					not abs(i - ap) > vl - 2) and not pctl.multi_playlist[pctl.active_playlist_viewing][4]:
						pctl.playlist_view_position = ap

					else:
						# Move to a random offset ---

						if i == pctl.playlist_view_position - 1 and pctl.playlist_view_position > 1:
							pctl.playlist_view_position -= 1

						# Move a bit if its just out of range
						elif pctl.playlist_view_position + vl - 2 == i and i < len(
								self.multi_playlist[self.active_playlist_viewing][2]) - 5:
							pctl.playlist_view_position += 3

						# We know its out of range if above view postion
						elif i < pctl.playlist_view_position:
							pctl.playlist_view_position = i - random.randint(2, int((
								gui.playlist_view_length / 3) * 2) + int(gui.playlist_view_length / 6))

						# If its below we need to test if its in view. If playing track in view, don't jump.
						elif abs(pctl.playlist_view_position - i) >= vl:
							pctl.playlist_view_position = i
							if i > 6:
								pctl.playlist_view_position -= 5
							if i > gui.playlist_view_length and i + (gui.playlist_view_length * 2) < len(
									self.multi_playlist[self.active_playlist_viewing][2]) and i > 10:
								pctl.playlist_view_position = i - random.randint(2,
									int(gui.playlist_view_length / 3) * 2)

				break

		else:  # Search other all other playlists
			if not this_only:
				for i, playlist in enumerate(self.multi_playlist):
					if track_index in playlist[2]:
						switch_playlist(i, quiet=True)
						self.show_current(select, playing, quiet, this_only=True, index=track_index)
						break

		if pctl.playlist_view_position < 0:
			pctl.playlist_view_position = 0

		# if pctl.playlist_view_position > len(self.multi_playlist[self.active_playlist_viewing][2]) - 1:
		#	 logging.info("Run Over")

		if select:
			shift_selection = []

		self.render_playlist()

		if album_mode and not quiet:
			if highlight:
				gui.gallery_animate_highlight_on = goto_album(pctl.selected_in_playlist)
				gallery_select_animate_timer.set()
			else:
				goto_album(pctl.selected_in_playlist)

		if prefs.left_panel_mode == "artist list" and gui.lsp and not quiet:
			artist_list_box.locate_artist(pctl.playing_object())

		if folder_list and prefs.left_panel_mode == "folder view" and gui.lsp and not quiet and not tree_view_box.lock_pl:
			tree_view_box.show_track(pctl.playing_object())

		return 0

	def toggle_mute(self):
		global volume_store
		if pctl.player_volume > 0:
			volume_store = pctl.player_volume
			pctl.player_volume = 0
		else:
			pctl.player_volume = volume_store

		pctl.set_volume()

	def set_volume(self, notify=True):

		if (spot_ctl.coasting or spot_ctl.playing) and not spot_ctl.local and mouse_down:
			# Rate limit network volume change
			t = self.volume_update_timer.get()
			if t < 0.3:
				return

		self.volume_update_timer.set()
		self.playerCommand = "volume"
		self.playerCommandReady = True
		if notify:
			self.notify_update()

	def revert(self):

		if self.queue_step == 0:
			return

		prev = 0
		while len(self.track_queue) > prev + 1 and prev < 5:
			if self.track_queue[len(self.track_queue) - 1 - prev] == self.left_index:
				self.queue_step = len(self.track_queue) - 1 - prev
				self.jump_time = self.left_time
				self.playing_time = self.left_time
				self.decode_time = self.left_time
				break
			prev += 1
		else:
			self.queue_step -= 1
			self.jump_time = 0
			self.playing_time = 0
			self.decode_time = 0

		if not len(self.track_queue) > self.queue_step >= 0:
			logging.error("There is no previous track?")
			return

		self.target_open = pctl.master_library[self.track_queue[self.queue_step]].fullpath
		self.target_object = pctl.master_library[self.track_queue[self.queue_step]]
		self.start_time = pctl.master_library[self.track_queue[self.queue_step]].start_time
		self.start_time_target = self.start_time
		self.playing_length = pctl.master_library[self.track_queue[self.queue_step]].length
		self.playerCommand = "open"
		self.playerCommandReady = True
		self.playing_state = 1

		if tauon.stream_proxy.download_running:
			tauon.stream_proxy.stop()

		self.show_current()
		self.render_playlist()

	def deduct_shuffle(self, track_id):
		if pctl.multi_playlist and self.random_mode:
			pl = pctl.multi_playlist[pctl.active_playlist_playing]
			id = pl[6]

			if id not in pctl.shuffle_pools:
				self.update_shuffle_pool(pl[6])

			pool = pctl.shuffle_pools[id]
			if not pool:
				del pctl.shuffle_pools[id]
				self.update_shuffle_pool(pl[6])
			pool = pctl.shuffle_pools[id]

			if track_id in pool:
				pool.remove(track_id)


	def play_target_rr(self):
		tm.ready_playback()
		self.playing_length = pctl.master_library[self.track_queue[self.queue_step]].length

		if self.playing_length > 2:
			random_start = random.randrange(1, int(self.playing_length) - 45 if self.playing_length > 50 else int(
				self.playing_length))
		else:
			random_start = 0

		self.playing_time = random_start
		self.target_open = pctl.master_library[self.track_queue[self.queue_step]].fullpath
		self.target_object = pctl.master_library[self.track_queue[self.queue_step]]
		self.start_time = pctl.master_library[self.track_queue[self.queue_step]].start_time
		self.start_time_target = self.start_time
		self.jump_time = random_start
		self.playerCommand = "open"
		if not prefs.use_jump_crossfade:
			self.playerSubCommand = "now"
		self.playerCommandReady = True
		self.playing_state = 1
		radiobox.loaded_station = None

		if tauon.stream_proxy.download_running:
			tauon.stream_proxy.stop()

		if update_title:
			update_title_do()

		self.deduct_shuffle(self.target_object.index)

	def play_target(self, gapless=False, jump=False):

		tm.ready_playback()

		#logging.info(self.track_queue)
		self.playing_time = 0
		self.decode_time = 0
		target = pctl.master_library[self.track_queue[self.queue_step]]
		self.target_open = target.fullpath
		self.target_object = target
		self.start_time = target.start_time
		self.start_time_target = self.start_time
		self.playing_length = target.length
		self.last_playing_time = 0
		self.commit = None
		radiobox.loaded_station = None

		if tauon.stream_proxy and tauon.stream_proxy.download_running:
			tauon.stream_proxy.stop()

		if pctl.multi_playlist[pctl.active_playlist_playing][11]:
			t = target.misc.get("position", 0)
			if t:
				self.playing_time = 0
				self.decode_time = 0
				self.jump_time = t

		self.playerCommand = "open"
		if jump:  # and not prefs.use_jump_crossfade:
			self.playerSubCommand = "now"

		self.playerCommandReady = True

		self.playing_state = 1
		self.update_change()
		self.deduct_shuffle(target.index)

	def update_change(self):
		if update_title:
			update_title_do()
		self.notify_update()
		hit_discord()
		self.render_playlist()

		if lfm_scrobbler.a_sc:
			lfm_scrobbler.a_sc = False
			self.a_time = 0

		lfm_scrobbler.start_queue()

		if (album_mode or not gui.rsp) and (gui.theme_name == "Carbon" or prefs.colour_from_image):
			target = self.playing_object()
			if target and prefs.colour_from_image and target.parent_folder_path == colours.last_album:
				return

			album_art_gen.display(target, (0, 0), (50, 50), theme_only=True)

	def jump(self, index, pl_position=None, jump=True):

		lfm_scrobbler.start_queue()
		pctl.auto_stop = False

		if self.force_queue and not pctl.pause_queue:
			if self.force_queue[0][4] == 1:
				if pctl.g(self.force_queue[0][0]).parent_folder_path != pctl.g(index).parent_folder_path:
					del self.force_queue[0]

		if len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]

			if self.playing_state == 1 and self.left_time > 5 and self.playing_length - self.left_time > 15:
				pctl.master_library[self.left_index].skips += 1

		global playlist_hold
		gui.update_spec = 0
		self.active_playlist_playing = self.active_playlist_viewing
		self.track_queue.append(index)
		self.queue_step = len(self.track_queue) - 1
		playlist_hold = False
		self.play_target(jump=jump)

		if pl_position is not None:
			self.playlist_playing_position = pl_position

		gui.pl_update = 1

	def back(self):

		if self.playing_state < 3 and prefs.back_restarts and pctl.playing_time > 6:
			self.seek_time(0)
			self.render_playlist()
			return

		if spot_ctl.coasting:
			spot_ctl.control("previous")
			spot_ctl.update_timer.set()
			self.playing_time = -2
			self.decode_time = -2
			return

		if len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]

		gui.update_spec = 0
		# Move up
		if self.random_mode is False and len(self.playing_playlist()) > self.playlist_playing_position > 0:

			if len(self.track_queue) > 0 and self.playing_playlist()[self.playlist_playing_position] != \
					self.track_queue[
						self.queue_step]:

				try:
					p = self.playing_playlist().index(self.track_queue[self.queue_step])
				except Exception:
					logging.exception("Failed to change playing_playlist")
					p = random.randrange(len(self.playing_playlist()))
				if p is not None:
					self.playlist_playing_position = p

			self.playlist_playing_position -= 1
			self.track_queue.append(self.playing_playlist()[self.playlist_playing_position])
			self.queue_step = len(self.track_queue) - 1
			self.play_target(jump=True)

		elif self.random_mode is True and self.queue_step > 0:
			self.queue_step -= 1
			self.play_target(jump=True)
		else:
			logging.info("BACK: NO CASE!")
			self.show_current()

		if self.active_playlist_viewing == self.active_playlist_playing:
			self.show_current(False, True)

		if album_mode:
			goto_album(self.playlist_playing_position)
		if gui.combo_mode and self.active_playlist_viewing == self.active_playlist_playing:
			self.show_current()

		self.render_playlist()
		self.notify_update()
		notify_song()
		lfm_scrobbler.start_queue()
		gui.pl_update += 1

	def stop(self, block=False, run=False):

		self.playerCommand = "stop"
		if run:
			self.playerCommand = "runstop"
		if block:
			self.playerSubCommand = "return"

		self.playerCommandReady = True

		try:
			tm.player_lock.release()
		except Exception:
			logging.exception("Failed to release player_lock")

		self.record_stream = False
		if len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]
		previous_state = self.playing_state
		self.playing_time = 0
		self.decode_time = 0
		self.playing_state = 0
		self.render_playlist()

		gui.update_spec = 0
		# gui.update_level = True  # Allows visualiser to enter decay sequence
		gui.update = True
		if update_title:
			update_title_do()  # Update title bar text

		if tauon.stream_proxy and tauon.stream_proxy.download_running:
			tauon.stream_proxy.stop()

		if block:
			loop = 0
			sleep_timeout(lambda: self.playerSubCommand != "stopped", 2)
			if tauon.stream_proxy.download_running:
				sleep_timeout(lambda: tauon.stream_proxy.download_running, 2)

		if spot_ctl.playing or spot_ctl.coasting:
			logging.info("Spotify stop")
			spot_ctl.control("stop")

		self.notify_update()
		lfm_scrobbler.start_queue()
		return previous_state

	def pause(self):

		if tauon.spotc and tauon.spotc.running and spot_ctl.playing:
			if self.playing_state == 1:
				self.playerCommand = "pauseon"
				self.playerCommandReady = True
			elif self.playing_state == 2:
				self.playerCommand = "pauseoff"
				self.playerCommandReady = True

		if self.playing_state == 3:
			if spot_ctl.coasting:
				if spot_ctl.paused:
					spot_ctl.control("resume")
				else:
					spot_ctl.control("pause")
			return

		if spot_ctl.playing:
			if self.playing_state == 2:
				spot_ctl.control("resume")
				self.playing_state = 1
			elif self.playing_state == 1:
				spot_ctl.control("pause")
				self.playing_state = 2
			self.render_playlist()
			return

		if self.playing_state == 1:
			self.playerCommand = "pauseon"
			self.playing_state = 2
		elif self.playing_state == 2:
			self.playerCommand = "pauseoff"
			self.playing_state = 1
			notify_song()

		self.playerCommandReady = True

		self.render_playlist()
		self.notify_update()

	def pause_only(self):
		if self.playing_state == 1:
			self.playerCommand = "pauseon"
			self.playing_state = 2

			self.playerCommandReady = True
			self.render_playlist()
			self.notify_update()

	def play_pause(self):
		if self.playing_state == 3:
			self.stop()
		elif self.playing_state > 0:
			self.pause()
		else:
			self.play()

	def seek_decimal(self, decimal):
		# if self.commit:
		#	 return
		if self.playing_state == 1 or self.playing_state == 2 or (self.playing_state == 3 and spot_ctl.coasting):
			if decimal > 1:
				decimal = 1
			elif decimal < 0:
				decimal = 0
			self.new_time = pctl.playing_length * decimal
			#logging.info('seek to:' + str(pctl.new_time))
			self.playerCommand = "seek"
			self.playerCommandReady = True
			self.playing_time = self.new_time

			if msys and taskbar_progress and self.windows_progress:
				self.windows_progress.update(True)

			if self.mpris is not None:
				self.mpris.seek_do(self.playing_time)

	def seek_time(self, new):
		# if self.commit:
		#	 return
		if self.playing_state == 1 or self.playing_state == 2 or (self.playing_state == 3 and spot_ctl.coasting):

			if new > self.playing_length - 0.5:
				self.advance()
				return

			if new < 0.4:
				new = 0

			self.new_time = new
			self.playing_time = new

			self.playerCommand = "seek"
			self.playerCommandReady = True

			if self.mpris is not None:
				self.mpris.seek_do(self.playing_time)

	def play(self):

		if spot_ctl.playing:
			if self.playing_state == 2:
				self.play_pause()
			return

		# Unpause if paused
		if self.playing_state == 2:
			self.playerCommand = "pauseoff"
			self.playerCommandReady = True
			self.playing_state = 1
			self.notify_update()

		# If stopped...
		elif pctl.playing_state == 0:

			if radiobox.loaded_station:
				radiobox.start(radiobox.loaded_station)
				return

			# If the queue is empty
			if self.track_queue == [] and len(self.multi_playlist[self.active_playlist_playing][2]) > 0:
				self.track_queue.append(self.multi_playlist[self.active_playlist_playing][2][0])
				self.queue_step = 0
				self.playlist_playing_position = 0
				self.active_playlist_playing = 0

				self.play_target()

			# If the queue is not empty, play?
			elif len(self.track_queue) > 0:
				self.play_target()

		self.render_playlist()

	def spot_test_progress(self):

		if (self.playing_state == 1 or self.playing_state == 2) and spot_ctl.playing:
			th = 5  # the rate to poll the spotify API
			if self.playing_time > self.playing_length:
				th = 1
			if not spot_ctl.paused:
				if spot_ctl.start_timer.get() < 0.5:
					spot_ctl.progress_timer.set()
					return
				add_time = spot_ctl.progress_timer.get()
				if add_time > 5:
					add_time = 0
				self.playing_time += add_time
				self.decode_time = self.playing_time
				# self.test_progress()
				spot_ctl.progress_timer.set()
				if len(self.track_queue) > 0 and 2 > add_time > 0:
					star_store.add(self.track_queue[self.queue_step], add_time)
			if spot_ctl.update_timer.get() > th:
				spot_ctl.update_timer.set()
				shooter(spot_ctl.monitor)
			else:
				self.test_progress()

		elif self.playing_state == 3 and spot_ctl.coasting:
			th = 7
			if self.playing_time > self.playing_length or self.playing_time < 2.5:
				th = 1
			if spot_ctl.update_timer.get() < th:
				if not spot_ctl.paused:
					self.playing_time += spot_ctl.progress_timer.get()
					self.decode_time = self.playing_time
				spot_ctl.progress_timer.set()

			else:
				tauon.spot_ctl.update_timer.set()
				tauon.spot_ctl.update()

	def purge_track(self, track_id, fast=False):  # Remove a track from the database
		# Remove from all playlists
		if not fast:
			for playlist in self.multi_playlist:
				while track_id in playlist[2]:
					album_dex.clear()
					playlist[2].remove(track_id)
		# Stop if track is playing track
		if self.track_queue and self.track_queue[self.queue_step] == track_id and self.playing_state != 0:
			self.stop(block=True)
		# Remove from playback history
		while track_id in self.track_queue:
			self.track_queue.remove(track_id)
			self.queue_step -= 1
		# Remove track from force queue
		for i in reversed(range(len(self.force_queue))):
			if self.force_queue[i][0] == track_id:
				del self.force_queue[i]
		del self.master_library[track_id]

	def test_progress(self):

		# Fuzzy reload lastfm for rescrobble
		if lfm_scrobbler.a_sc and self.playing_time < 1:
			lfm_scrobbler.a_sc = False
			self.a_time = 0

		# Update the UI if playing time changes a whole number
		# next_round = int(pctl.playing_time)
		# if self.playing_time_int != next_round:
		#	 #if not prefs.power_save:
		#	 #gui.update += 1
		#	 self.playing_time_int = next_round

		gap_extra = 2  # 2

		if spot_ctl.playing or tauon.chrome_mode:
			gap_extra = 3

		if msys and taskbar_progress and self.windows_progress:
			self.windows_progress.update(True)

		if self.commit is not None:
			return

		if self.playing_state == 1 and pctl.multi_playlist[pctl.active_playlist_playing][11]:
			tr = pctl.playing_object()
			if tr:
				tr.misc["position"] = pctl.decode_time

		if self.playing_state == 1 and self.decode_time + gap_extra >= self.playing_length and self.decode_time > 0.2:

			# Allow some time for spotify playing time to update?
			if spot_ctl.playing and spot_ctl.start_timer.get() < 3:
				return

			# Allow some time for backend to provide a length
			if self.playing_time < 6 and self.playing_length == 0:
				return
			if not spot_ctl.playing and pctl.a_time < 2:
				return

			self.decode_time = 0

			pp = self.playing_playlist()

			if pctl.auto_stop:  # and not pctl.force_queue and not (pctl.force_queue and pctl.pause_queue):
				self.stop(run=True)
				if pctl.force_queue or (not pctl.force_queue and not pctl.random_mode and not pctl.repeat_mode):
					self.advance(play=False)
				gui.update += 2
				pctl.auto_stop = False

			elif self.force_queue and not self.pause_queue:
				id = self.advance(end=True, quiet=True, dry=True)
				if id is not None:
					self.start_commit(id)
					return
				else:
					self.advance(end=True, quiet=True)



			elif self.repeat_mode is True:

				if self.album_repeat_mode:

					if self.playlist_playing_position > len(pp) - 1:
						self.playlist_playing_position = 0  # Hack fix, race condition bug?

					ti = self.g(pp[self.playlist_playing_position])

					i = self.playlist_playing_position

					# Test if next track is in same folder
					if i + 1 < len(pp):
						nt = self.g(pp[i + 1])
						if ti.parent_folder_path == nt.parent_folder_path:
							# The next track is in the same folder
							# so advance normally
							self.advance(quiet=True, end=True)
							return

					# We need to backtrack to see where the folder begins
					i -= 1
					while i >= 0:
						nt = self.g(pp[i])
						if ti.parent_folder_path != nt.parent_folder_path:
							i += 1
							break
						i -= 1
					if i < 0:
						i = 0

					pctl.selected_in_playlist = i
					shift_selection = [i]

					self.jump(pp[i], i, jump=False)

				elif prefs.playback_follow_cursor and self.playing_ready() \
						and self.multi_playlist[pctl.active_playlist_viewing][2][
					pctl.selected_in_playlist] != self.playing_object().index \
						and -1 < pctl.selected_in_playlist < len(default_playlist):

					logging.info("Repeat follow cursor")

					self.playing_time = 0
					self.decode_time = 0
					self.active_playlist_playing = self.active_playlist_viewing
					self.playlist_playing_position = pctl.selected_in_playlist

					self.track_queue.append(default_playlist[pctl.selected_in_playlist])
					self.queue_step = len(self.track_queue) - 1
					self.play_target(jump=False)
					self.render_playlist()
					lfm_scrobbler.start_queue()

				else:
					id = self.track_queue[self.queue_step]
					self.commit = id
					target = self.g(id)
					self.target_open = target.fullpath
					self.target_object = target
					self.start_time = target.start_time
					self.start_time_target = self.start_time
					self.playerCommand = "open"
					self.playerSubCommand = "repeat"
					self.playerCommandReady = True

					#self.render_playlist()
					lfm_scrobbler.start_queue()

					# Reload lastfm for rescrobble
					if lfm_scrobbler.a_sc:
						lfm_scrobbler.a_sc = False
						self.a_time = 0

			elif self.random_mode is False and len(pp) > self.playlist_playing_position + 1 and \
					self.master_library[pp[self.playlist_playing_position]].is_cue is True \
					and self.master_library[pp[self.playlist_playing_position + 1]].filename == \
					self.master_library[pp[self.playlist_playing_position]].filename and int(
				self.master_library[pp[self.playlist_playing_position]].track_number) == int(
				self.master_library[pp[self.playlist_playing_position + 1]].track_number) - 1:

				#  not (self.force_queue and not self.pause_queue) and \

				# We can shave it closer
				if not self.playing_time + 0.1 >= self.playing_length:
					return

				logging.info("Do transition CUE")
				self.playlist_playing_position += 1
				self.queue_step += 1
				self.track_queue.append(pp[self.playlist_playing_position])
				self.playing_state = 1
				self.playing_time = 0
				self.decode_time = 0
				self.playing_length = self.master_library[self.track_queue[self.queue_step]].length
				self.start_time = self.master_library[self.track_queue[self.queue_step]].start_time
				self.start_time_target = self.start_time
				lfm_scrobbler.start_queue()

				gui.update += 1
				gui.pl_update = 1

				if update_title:
					update_title_do()
				self.notify_update()
			else:
				# self.advance(quiet=True, end=True)

				id = self.advance(quiet=True, end=True, dry=True)
				if id is not None and not spot_ctl.playing:
					#logging.info("Commit")
					self.start_commit(id)
					return

				self.advance(quiet=True, end=True)
				self.playing_time = 0
				self.decode_time = 0

	def start_commit(self, id, repeat=False):
		self.commit = id
		target = self.g(id)
		self.target_open = target.fullpath
		self.target_object = target
		self.start_time = target.start_time
		self.start_time_target = self.start_time
		self.playerCommand = "open"
		if repeat:
			self.playerSubCommand = "repeat"
		self.playerCommandReady = True

	def advance(self, rr=False, quiet=False, inplace=False, end=False, force=False, play=True, dry=False):

		# Spotify remote control mode
		if not dry:
			if spot_ctl.coasting:
				spot_ctl.control("next")
				spot_ctl.update_timer.set()
				self.playing_time = -2
				self.decode_time = -2
				return

		# Temporary Workaround for UI block causing unwanted dragging
		if not dry:
			quick_d_timer.set()

		if prefs.show_current_on_transition:
			quiet = False

		# Trim the history if it gets too long
		while len(self.track_queue) > 250:
			self.queue_step -= 1
			del self.track_queue[0]

		# Save info about the track we are leaving
		if not dry:
			if len(self.track_queue) > 0:
				self.left_time = self.playing_time
				self.left_index = self.track_queue[self.queue_step]

		# Test to register skip (not currently used for anything)
		if not dry:
			if self.playing_state == 1 and 1 < self.left_time < 45:
				pctl.master_library[self.left_index].skips += 1
				#logging.info('skip registered')

		if not dry:
			pctl.playing_time = 0
			pctl.decode_time = 0
			pctl.playing_length = 100
			gui.update_spec = 0

		old = self.queue_step
		end_of_playlist = False

		# Force queue (middle click on track)
		if len(self.force_queue) > 0 and not self.pause_queue:

			q = self.force_queue[0]
			target_index = q[0]

			if q[3] == 1:
				# This is an album type

				if q[4] == 0:
					# We have not started playing the album yet
					# So we go to that track
					# (This is a copy of the track code, but we don't delete the item)

					if not dry:

						pl = id_to_pl(q[2])
						if pl is not None:
							self.active_playlist_playing = pl

						if target_index not in self.playing_playlist():
							del self.force_queue[0]
							self.advance()
							return

					if dry:
						return target_index

					self.playlist_playing_position = q[1]
					self.track_queue.append(target_index)
					self.queue_step = len(self.track_queue) - 1
					# self.queue_target = len(self.track_queue) - 1
					if play:
						self.play_target(jump=not end)

					#  Set the flag that we have entered the album
					self.force_queue[0][4] = 1

					# This code is mirrored below -------
					ok_continue = True

					# Check if we are at end of playlist
					pl = pctl.multi_playlist[pctl.active_playlist_playing][2]
					if self.playlist_playing_position > len(pl) - 3:
						ok_continue = False

					# Check next song is in album
					if ok_continue:
						if self.g(pl[self.playlist_playing_position + 1]).parent_folder_path != pctl.g(
								target_index).parent_folder_path:
							ok_continue = False

					# -----------


				elif q[4] == 1:
					# We have previously started playing this album

					# Check to see if we still are:
					ok_continue = True

					if pctl.g(target_index).parent_folder_path != pctl.playing_object().parent_folder_path:
						# Remember to set jumper check this too (leave album if we jump to some other track, i.e. double click))
						ok_continue = False

					pl = pctl.multi_playlist[pctl.active_playlist_playing][2]

					# Check next song is in album
					if ok_continue:

						# Check if we are at end of playlist, or already at end of album
						if self.playlist_playing_position >= len(pl) - 1 or self.playlist_playing_position < len(
								pl) - 1 and \
								self.g(pl[self.playlist_playing_position + 1]).parent_folder_path != pctl.g(
							target_index).parent_folder_path:

							if dry:
								return None

							del self.force_queue[0]
							self.advance()
							return


						# Check if 2 songs down is in album, remove entry in queue if not
						elif self.playlist_playing_position < len(pl) - 2 and \
								self.g(pl[self.playlist_playing_position + 2]).parent_folder_path != pctl.g(
							target_index).parent_folder_path:
							ok_continue = False

					# if ok_continue:
					# We seem to be still in the album. Step down one and play
					if not dry:
						self.playlist_playing_position += 1

					if len(pl) <= self.playlist_playing_position:
						if dry:
							return None
						logging.info("END OF PLAYLIST!")
						del self.force_queue[0]
						self.advance()
						return

					if dry:
						return pl[self.playlist_playing_position + 1]
					self.track_queue.append(pl[self.playlist_playing_position])
					self.queue_step = len(self.track_queue) - 1
					# self.queue_target = len(self.track_queue) - 1
					if play:
						self.play_target(jump=not end)

				if not ok_continue:
					# It seems this item has expired, remove it and call advance again

					if dry:
						return None

					logging.info("Remove expired album from queue")
					del self.force_queue[0]

					if q[6]:
						pctl.auto_stop = True
					if prefs.stop_end_queue and not self.force_queue:
						pctl.auto_stop = True

					if queue_box.scroll_position > 0:
						queue_box.scroll_position -= 1

						# self.advance()
						# return

			else:
				# This is track type
				pl = id_to_pl(q[2])
				if not dry:
					if pl is not None:
						self.active_playlist_playing = pl

				if target_index not in self.playing_playlist():
					if dry:
						return None
					del self.force_queue[0]
					self.advance()
					return

				if dry:
					return target_index

				self.playlist_playing_position = q[1]
				self.track_queue.append(target_index)
				self.queue_step = len(self.track_queue) - 1
				# self.queue_target = len(self.track_queue) - 1
				if play:
					self.play_target(jump=not end)
				del self.force_queue[0]
				if q[6]:
					pctl.auto_stop = True
				if prefs.stop_end_queue and not self.force_queue:
					pctl.auto_stop = True
				if queue_box.scroll_position > 0:
					queue_box.scroll_position -= 1

		# Stop if playlist is empty
		elif len(self.playing_playlist()) == 0:
			if dry:
				return None
			self.stop()
			return 0

		# Playback follow cursor
		elif prefs.playback_follow_cursor and self.playing_ready() \
				and self.multi_playlist[pctl.active_playlist_viewing][2][
			pctl.selected_in_playlist] != self.playing_object().index \
				and -1 < pctl.selected_in_playlist < len(default_playlist):

			if dry:
				return default_playlist[pctl.selected_in_playlist]

			self.active_playlist_playing = self.active_playlist_viewing
			self.playlist_playing_position = pctl.selected_in_playlist

			self.track_queue.append(default_playlist[pctl.selected_in_playlist])
			self.queue_step = len(self.track_queue) - 1
			if play:
				self.play_target(jump=not end)

		# If random, jump to random track
		elif (self.random_mode or rr) and len(self.playing_playlist()) > 0 and not (
				self.album_shuffle_mode or prefs.album_shuffle_lock_mode):
			# self.queue_step += 1
			new_step = self.queue_step + 1

			if new_step == len(self.track_queue):

				if self.album_repeat_mode and self.repeat_mode:
					# Album shuffle mode
					pp = self.playing_playlist()
					k = self.playlist_playing_position
					# ti = self.g(pp[k])
					ti = self.master_library[self.track_queue[self.queue_step]]

					if ti.index not in pp:
						if dry:
							return None
						logging.info("No tracks to repeat!")
						return 0

					matches = []
					for i, p in enumerate(pp):

						if self.g(p).parent_folder_path == ti.parent_folder_path:
							matches.append((i, p))

					if matches:
						# Avoid a repeat of same track
						if len(matches) > 1 and (k, ti.index) in matches:
							matches.remove((k, ti.index))

						i, p = random.choice(matches)  # not used

						if prefs.true_shuffle:

							id = ti.parent_folder_path

							while True:
								if id in pctl.shuffle_pools:

									pool = pctl.shuffle_pools[id]

									if not pool:
										del pctl.shuffle_pools[id]  # Trigger a refill
										continue

									ref = pool.pop()
									if dry:
										pool.append(ref)
										return ref[1]
									# ref = random.choice(pool)
									# pool.remove(ref)

									if ref[1] not in pp:  # Check track still in the live playlist
										logging.info("Track not in pool")
										continue

									i, p = ref  # Find position of reference in playlist
									break

								else:
									# Refill the pool
									random.shuffle(matches)
									pctl.shuffle_pools[id] = matches

									logging.info("Refill folder shuffle pool")

						self.playlist_playing_position = i
						self.track_queue.append(p)

				else:
					# Normal select from playlist

					if prefs.true_shuffle:
						# True shuffle avoids repeats by using a pool

						pl = pctl.multi_playlist[pctl.active_playlist_playing]
						id = pl[6]

						while True:

							if id in pctl.shuffle_pools:

								pool = pctl.shuffle_pools[id]

								if not pool:
									del pctl.shuffle_pools[id]  # Trigger a refill
									continue

								ref = pool.pop()
								if dry:
									pool.append(ref)
									return ref
								# ref = random.choice(pool)
								# pool.remove(ref)

								if ref not in pl[2]:  # Check track still in the live playlist
									continue

								random_jump = pl[2].index(ref)  # Find position of reference in playlist
								break

							else:
								# Refill the pool
								self.update_shuffle_pool(pl[6])

					else:
						random_jump = random.randrange(len(self.playing_playlist()))  # not used

					self.playlist_playing_position = random_jump
					self.track_queue.append(self.playing_playlist()[random_jump])

			if inplace and self.queue_step > 1:
				del self.track_queue[self.queue_step]
			else:
				if dry:
					return self.track_queue[new_step]
				self.queue_step = new_step

			if rr:
				if dry:
					return None
				self.play_target_rr()
			else:
				if play:
					self.play_target(jump=not end)


		# If not random mode, Step down 1 on the playlist
		elif self.random_mode is False and len(self.playing_playlist()) > 0:

			# Stop at end of playlist
			if self.playlist_playing_position == len(self.playing_playlist()) - 1:
				if dry:
					return None
				if prefs.end_setting == "stop":
					self.playing_state = 0
					self.playerCommand = "runstop"
					self.playerCommandReady = True
					end_of_playlist = True

				elif prefs.end_setting == "advance" or prefs.end_setting == "cycle":

					# If at end playlist and not cycle mode, stop playback
					if pctl.active_playlist_playing == len(
							pctl.multi_playlist) - 1 and not prefs.end_setting == "cycle":
						self.playing_state = 0
						self.playerCommand = "runstop"
						self.playerCommandReady = True
						end_of_playlist = True

					else:

						p = pctl.active_playlist_playing
						for i in range(len(pctl.multi_playlist)):

							k = (p + i + 1) % len(pctl.multi_playlist)

							# Skip a playlist if empty
							if not (pctl.multi_playlist[k][2]):
								continue

							# Skip a playlist if hidden
							if pctl.multi_playlist[k][8] and prefs.tabs_on_top:
								continue

							# Set found playlist as playing the first track
							pctl.active_playlist_playing = k
							pctl.playlist_playing_position = -1
							pctl.advance(end=end, force=True, play=play)
							break

						else:
							# Restart current if no other eligible playlist found
							pctl.playlist_playing_position = -1
							pctl.advance(end=end, force=True, play=play)

						return

				elif prefs.end_setting == "repeat":
					pctl.playlist_playing_position = -1
					pctl.advance(end=end, force=True, play=play)
					return

				gui.update += 3

			else:
				if self.playlist_playing_position > len(self.playing_playlist()) - 1:
					if dry:
						return None
					self.playlist_playing_position = 0

				elif not force and len(self.track_queue) > 0 and self.playing_playlist()[
					self.playlist_playing_position] != self.track_queue[
					self.queue_step]:
					try:
						if dry:
							return None
						self.playlist_playing_position = self.playing_playlist().index(
							self.track_queue[self.queue_step])
					except Exception:
						logging.exception("Failed to set playlist_playing_position")

				if len(self.playing_playlist()) == self.playlist_playing_position + 1:
					return

				if dry:
					return self.playing_playlist()[self.playlist_playing_position + 1]
				self.playlist_playing_position += 1
				self.track_queue.append(self.playing_playlist()[self.playlist_playing_position])

				# logging.info("standand advance")
				# self.queue_target = len(self.track_queue) - 1
				# if end:
				#	 self.play_target_gapless(jump= not end)
				# else:
				self.queue_step = len(self.track_queue) - 1
				if play:
					self.play_target(jump=not end)

		else:

			if self.random_mode and (self.album_shuffle_mode or prefs.album_shuffle_lock_mode):

				# Album shuffle mode
				logging.info("Album shuffle mode")

				po = self.playing_object()

				redraw = False

				# Checks
				if po is not None and len(self.playing_playlist()) > 0:

					# If we at end of playlist, we'll go to a new album
					if len(self.playing_playlist()) == self.playlist_playing_position + 1:
						redraw = True
					# If the next track is a new album, go to a new album
					elif po.parent_folder_path != pctl.g(
							self.playing_playlist()[self.playlist_playing_position + 1]).parent_folder_path:
						redraw = True
					# Always redraw on press in album shuffle lockdown
					if prefs.album_shuffle_lock_mode and not end:
						redraw = True

					if not redraw:
						if dry:
							return self.playing_playlist()[self.playlist_playing_position + 1]
						self.playlist_playing_position += 1
						self.track_queue.append(self.playing_playlist()[self.playlist_playing_position])
						self.queue_step = len(self.track_queue) - 1
						# self.queue_target = len(self.track_queue) - 1
						if play:
							self.play_target(jump=not end)

					else:

						if dry:
							return None
						albums = []
						current_folder = ""
						for i in range(len(self.playing_playlist())):
							if i == 0:
								albums.append(i)
								current_folder = self.master_library[self.playing_playlist()[i]].parent_folder_path
							else:
								if pctl.master_library[self.playing_playlist()[i]].parent_folder_path != current_folder:
									current_folder = self.master_library[self.playing_playlist()[i]].parent_folder_path
									albums.append(i)

						random.shuffle(albums)

						for a in albums:

							if self.g(self.playing_playlist()[a]).parent_folder_path != self.playing_object().parent_folder_path:
								self.playlist_playing_position = a
								self.track_queue.append(self.playing_playlist()[a])
								self.queue_step = len(self.track_queue) - 1
								# self.queue_target = len(self.track_queue) - 1
								if play:
									self.play_target(jump=not end)
								break
							a = 0
							self.playlist_playing_position = a
							self.track_queue.append(self.playing_playlist()[a])
							self.queue_step = len(self.track_queue) - 1
							if play:
								self.play_target(jump=not end)
							# logging.info("THERE IS ONLY ONE ALBUM IN THE PLAYLIST")
							# self.stop()

			else:
				logging.error("ADVANCE ERROR - NO CASE!")

		if dry:
			return None

		if self.active_playlist_viewing == self.active_playlist_playing:
			self.show_current(quiet=quiet)
		elif prefs.auto_goto_playing:
			self.show_current(quiet=quiet, this_only=True, playing=False, highlight=True, no_switch=True)

		# if album_mode:
		#	 goto_album(self.playlist_playing)

		self.render_playlist()

		if spot_ctl.playing and end_of_playlist:
			spot_ctl.control("stop")

		self.notify_update()
		lfm_scrobbler.start_queue()
		if play:
			notify_song(end_of_playlist, delay=1.3)

	def reset_missing_flags(self):
		for value in self.master_library.values():
			value.found = True
		gui.pl_update += 1
