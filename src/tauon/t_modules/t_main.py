from __future__ import annotations


class Tauon:
	"""Root class for everything Tauon"""

	def __init__(self) -> None:
		pass

def main() -> None:
	logging.info(f"Window size: {window_size}; Logical size: {logical_size}")

	tls_context = setup_tls(holder)
	last_fm_enable = is_module_loaded("pylast")
	if last_fm_enable:
		importlib.reload(pylast)

	discord_allow = is_module_loaded("lynxpresence", "ActivityType")

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


	detect_macstyle = False
	gtk_settings: Gtk.Settings | None = None
	mac_close = ColourRGBA(253, 70, 70, 255)
	mac_maximize = ColourRGBA(254, 176, 36, 255)
	mac_minimize = ColourRGBA(42, 189, 49, 255)
	try:
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
		for k, v in mac_styles.items():
			if k in gtk_theme:
				detect_macstyle = True
				if v is not None:
					mac_close = v[0]
					mac_maximize = v[1]
					mac_minimize = v[2]

	except Exception:
		logging.exception("Error accessing GTK settings")


	install_mode = False
	flatpak_mode = False
	snap_mode = False
	if str(install_directory).startswith(("/opt/", "/usr/", "/app/", "/snap/", "/nix/store/")):
		install_mode = True
		if str(install_directory)[:6] == "/snap/":
			snap_mode = True
		if str(install_directory)[:5] == "/app/":
			logging.info("Detected running as Flatpak")

			if os.path.exists(os.path.join(home_directory, ".var/app/com.github.taiko2k.tauonmb/config")):
				host_fcfg = os.path.join(home_directory, ".config/fontconfig/")
				flatpak_fcfg = os.path.join(home_directory, ".var/app/com.github.taiko2k.tauonmb/config/fontconfig")

				if os.path.exists(host_fcfg):

					if os.path.islink(flatpak_fcfg):
						logging.info("-- Symlink to fonconfig exists, removing")
						os.unlink(flatpak_fcfg)

			flatpak_mode = True

	logging.info(f"Platform: {sys.platform}")

	if pyinstaller_mode:
		logging.info("Pyinstaller mode")

	if (install_mode and system == "Linux") or macos or msys:
		cache_directory  = Path(GLib.get_user_cache_dir()) / "TauonMusicBox"
		config_directory = user_directory

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

	sdl3.SDL_SetRenderTarget(renderer, main_texture)
	sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)

	sdl3.SDL_SetRenderTarget(renderer, main_texture_overlay_temp)
	sdl3.SDL_SetTextureBlendMode(main_texture_overlay_temp, sdl3.SDL_BLENDMODE_BLEND)
	sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
	sdl3.SDL_RenderClear(renderer)

	loaded_asset_dc: dict[str, WhiteModImageAsset | LoadImageAsset] = {}

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

	if install_directory != config_directory and not (config_directory / "input.txt").is_file():
		logging.warning("Input config file is missing, first run? Copying input.txt template from templates directory")
		shutil.copy(install_directory / "templates" / "input.txt", config_directory)

	if snap_mode:
		discord_allow = False

	musicbrainzngs.set_useragent("TauonMusicBox", n_version, "https://github.com/Taiko2k/Tauon")

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


	Archive_Formats = {"zip"}

	if whicher("unrar", flatpak_mode):
		Archive_Formats.add("rar")

	if whicher("7z", flatpak_mode):
		Archive_Formats.add("7z")

	MOD_Formats = {"xm", "mod", "s3m", "it", "mptm", "umx", "okt", "mtm", "669", "far", "wow", "dmf", "med", "mt2", "ult"}
	GME_Formats = {"ay", "gbs", "gym", "hes", "kss", "nsf", "nsfe", "sap", "spc", "vgm", "vgz"}
	draw_sep_hl = False
	default_playlist: list[int] = []
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
		system=system,
		pump=True,
		wayland=wayland,
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
	b_info_y = int(window_size[1] * 0.7)

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

			db_version = save[17]
			if db_version != latest_db_version:
				if db_version > latest_db_version:
					logging.critical(f"Loaded DB version: '{db_version}' is newer than latest known DB version '{latest_db_version}', refusing to load!\nAre you running an out of date Tauon version using Configuration directory from a newer one?")
					sys.exit(42)
				logging.warning(f"Loaded older DB version: {db_version}")
			if len(save) > 63 and save[63] is not None:
				prefs.ui_scale = save[63]

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
			prefs.theme = save[13]
			bag.folder_image_offsets = save[14]
			prefs.view_prefs = save[18]
			gui.save_size = copy.copy(save[19])
			gui.rspw = save[20]
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
			if len(save) > 32 and save[32] is not None:
				gui.maximized = save[32]
			if len(save) > 33 and save[33] is not None:
				prefs.prefer_bottom_title = save[33]
			if len(save) > 34 and save[34] is not None:
				gui.display_time_mode = save[34]
			if len(save) > 36 and save[36] is not None:
				prefs.transcode_codec = save[36]
			if len(save) > 37 and save[37] is not None:
				prefs.transcode_bitrate = save[37]
			if len(save) > 40 and save[40] is not None:
				prefs.playlist_font_size = save[40]
			if len(save) > 41 and save[41] is not None:
				prefs.use_title = save[41]
			if len(save) > 42 and save[42] is not None:
				gui.pl_st = save[42]
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
			if len(save) > 53 and save[53] is not None:
				prefs.auto_lfm = save[53]
			if len(save) > 54 and save[54] is not None:
				prefs.scrobble_mark = save[54]
			if len(save) > 55 and save[55] is not None:
				prefs.replay_gain = save[55]
			if len(save) > 57 and save[57] is not None:
				prefs.show_gimage = save[57]
			if len(save) > 58 and save[58] is not None:
				prefs.end_setting = save[58]
			if len(save) > 59 and save[59] is not None:
				prefs.show_gen = save[59]
			if len(save) > 61 and save[61] is not None:
				prefs.auto_del_zip = save[61]
			if len(save) > 62 and save[62] is not None:
				gui.level_meter_colour_mode = save[62]
			if len(save) > 64 and save[64] is not None:
				prefs.show_lyrics_side = save[64]
			if len(save) > 66 and save[66] is not None:
				gui.restart_album_mode = save[66]
			if len(save) > 67 and save[67] is not None:
				gui.album_playlist_width = save[67]
			if len(save) > 68 and save[68] is not None:
				prefs.transcode_opus_as = True
			if len(save) > 69 and save[69] is not None:
				pass
			del save
			break

		except IndexError:
			logging.exception("Index error")
			break
		except Exception:
			logging.exception("Failed to load save file")

	tauon = Tauon()

	tauon.after_scan              = after_scan
