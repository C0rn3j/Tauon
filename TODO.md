# Martin
## Get rid of globals

<details><summary>List</summary>

```yaml
src/tauon/t_modules/t_tagscan.py: global s_name
src/tauon/t_modules/player_ctl.py: global playlist_hold
src/tauon/t_modules/player_ctl.py: global shift_selection
src/tauon/t_modules/player_ctl.py: global volume_store
src/tauon/t_modules/t_main.py: global added
src/tauon/t_modules/t_main.py: global album_art_gen
src/tauon/t_modules/t_main.py: global album_dex
src/tauon/t_modules/t_main.py: global album_h_gap
src/tauon/t_modules/t_main.py: global album_info_cache_key
src/tauon/t_modules/t_main.py: global album_mode
src/tauon/t_modules/t_main.py: global album_mode_art_size
src/tauon/t_modules/t_main.py: global album_playlist_width
src/tauon/t_modules/t_main.py: global albums
src/tauon/t_modules/t_main.py: global album_v_gap
src/tauon/t_modules/t_main.py: global album_v_slide_value
src/tauon/t_modules/t_main.py: global break_enable
src/tauon/t_modules/t_main.py: global cargo
src/tauon/t_modules/t_main.py: global clicked
src/tauon/t_modules/t_main.py: global click_location
src/tauon/t_modules/t_main.py: global click_time
src/tauon/t_modules/t_main.py: global cm_clean_db
src/tauon/t_modules/t_main.py: global colours
src/tauon/t_modules/t_main.py: global core_use
src/tauon/t_modules/t_main.py: global cue_list
src/tauon/t_modules/t_main.py: global DA_Formats
src/tauon/t_modules/t_main.py: global default_playlist
src/tauon/t_modules/t_main.py: global dl_use
src/tauon/t_modules/t_main.py: global drag_mode
src/tauon/t_modules/t_main.py: global draw_border
src/tauon/t_modules/t_main.py: global draw_max_button
src/tauon/t_modules/t_main.py: global enc_field
src/tauon/t_modules/t_main.py: global highlight_left
src/tauon/t_modules/t_main.py: global highlight_right
src/tauon/t_modules/t_main.py: global home
src/tauon/t_modules/t_main.py: global input_text
src/tauon/t_modules/t_main.py: global last_row
src/tauon/t_modules/t_main.py: global loaderCommand
src/tauon/t_modules/t_main.py: global loaderCommandReady
src/tauon/t_modules/t_main.py: global loading_in_progress
src/tauon/t_modules/t_main.py: global mouse_down
src/tauon/t_modules/t_main.py: global mouse_up
src/tauon/t_modules/t_main.py: global move_in_progress
src/tauon/t_modules/t_main.py: global move_on_title
src/tauon/t_modules/t_main.py: global new_playlist_cooldown
src/tauon/t_modules/t_main.py: global old_album_pos
src/tauon/t_modules/t_main.py: global old_window_position
src/tauon/t_modules/t_main.py: global playlist_hold
src/tauon/t_modules/t_main.py: global playlist_hold_position
src/tauon/t_modules/t_main.py: global quick_drag
src/tauon/t_modules/t_main.py: global rename_index
src/tauon/t_modules/t_main.py: global renderer
src/tauon/t_modules/t_main.py: global right_click
src/tauon/t_modules/t_main.py: global r_menu_index
src/tauon/t_modules/t_main.py: global r_menu_position
src/tauon/t_modules/t_main.py: global scaled_asset_directory
src/tauon/t_modules/t_main.py: global scroll_enable
src/tauon/t_modules/t_main.py: global search_index
src/tauon/t_modules/t_main.py: global selection_stage
src/tauon/t_modules/t_main.py: global shift_selection
src/tauon/t_modules/t_main.py: global should_save_state
src/tauon/t_modules/t_main.py: global theme
src/tauon/t_modules/t_main.py: global todo
src/tauon/t_modules/t_main.py: global to_get
src/tauon/t_modules/t_main.py: global to_got
src/tauon/t_modules/t_main.py: global track_box
src/tauon/t_modules/t_main.py: global transcode_list
src/tauon/t_modules/t_main.py: global transcode_state
src/tauon/t_modules/t_main.py: global update_layout
src/tauon/t_modules/t_main.py: global update_title
src/tauon/t_modules/t_main.py: global volume_store
src/tauon/t_modules/t_main.py: global window_size
```
</details>

## Add requirements_devel.txt
This will allow to type GTK stuff

## Better system detection - https://docs.python.org/3/library/sys.html#sys.platform
Currently there's multiple ways to detect platforms, type of terminal etc, unify it

## Migrate deps to pyproject.toml - https://setuptools.pypa.io/en/latest/userguide/dependency_management.html
This should allow us to get rid of all the req .txt files

## Unify scripts
We don't need 2 shell scripts to compile phazor and 2 python scripts to do translations, merge them ideally into one Python script with flags
