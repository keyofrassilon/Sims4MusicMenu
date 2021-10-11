import os
import random
import re
from os.path import isfile, join

import services
from distributor.shared_messages import IconInfoData
from interactions.base.immediate_interaction import ImmediateSuperInteraction
from interactions.interaction_finisher import FinishingType
from music_alarms import MusicAlarms
from music_input import dialogtest_input
from music_menu_class import MainMenu
from music_util import error_trap, ld_notice, ld_file_loader
from objects.object_enums import ResetReason
from sims4.localization import LocalizationHelperTuning
from ui.ui_dialog_notification import UiDialogNotification
from ui.ui_dialog_picker import UiSimPicker, SimPickerRow


class MusicMenu(ImmediateSuperInteraction):
    filename = None
    volume = None
    datapath = os.path.join(os.environ['USERPROFILE'], "Music")
    playlist = []
    append = False
    index = 0
    MAX_PLAYLIST = 25
    def __init__(self, *args, **kwargs):
        (super().__init__)(*args, **kwargs)
        self.music_menu_choices = ("Heavy Metal",
                                   "Classic Rock",
                                   "Grindcore",
                                   "Death Metal",
                                   "Black Metal",
                                   "Rap",
                                   "Ambient",
                                   "Dance",
                                   "Tape Deck")

        self.music_options_choices = ("Change Music Directory",
                                        "Playlist Options",
                                        "Audio States",
                                        "Skip Track",
                                        "Headbang",
                                        "Pick Sims Listen To Music",
                                        "Stop Listening To Music",
                                        "Help",
                                        "Reload Scripts")

        self.music_volume_choices = ("Volume Low",
                                     "Volume Med",
                                     "Volume High",
                                     "Volume Highest",
                                     "Headphones",
                                     "High Quality")

        self.playlist_choices = ("Default Music Directory",
                                 "Custom Music Directory",
                                 "Load Playlist",
                                 "Search Playlist",
                                 "Random Playlist",
                                 "Clear Playlist",
                                 "Save New Playlist",
                                 "Build New Playlist",
                                 "Playlist Max Size")

        self.genre = MainMenu(*args, **kwargs)
        self.music_choice = MainMenu(*args, **kwargs)
        self.music_options = MainMenu(*args, **kwargs)
        self.playlist_menu = MainMenu(*args, **kwargs)
        self.music_volume = MainMenu(*args, **kwargs)
        self.script_choice = MainMenu(*args, **kwargs)
        self.music_alarm = MusicAlarms(*args, **kwargs)

    def _run_interaction_gen(self, timeline):
        self.music_options.show(timeline, self, 0, self.music_options_choices, "Music Menu", "Make a selection.")

    def audio_states(self, timeline):
        self.music_volume.show(timeline, self, 0, self.music_volume_choices, "Volume", "Make a selection.")

    def playlist_options(self, timeline):
        self.playlist_menu.show(timeline, self, 0, self.playlist_choices, "Playlist\n{}\nPlaylist has {} entries."
                                .format(MusicMenu.datapath, len(MusicMenu.playlist)), "Make a selection.")

    def headbang(self, timeline):
        self.music_alarm.push_sim_function(self.sim, self.sim, 240309)

    def skip_track(self, timeline):
        self.target.reset(ResetReason.NONE, None, 'Command')

    def picker(self, title: str, text: str, max: int = 50, callback=None):
        try:
            localized_title = lambda **_: LocalizationHelperTuning.get_raw_text(title)
            localized_text = lambda **_: LocalizationHelperTuning.get_raw_text(text)
            dialog = UiSimPicker.TunableFactory().default(self.sim,
                                                          text=localized_text,
                                                          title=localized_title,
                                                          max_selectable=max,
                                                          min_selectable=1,
                                                          should_show_names=True,
                                                          hide_row_description=False)

            sims = services.sim_info_manager().instanced_sims_gen()
            for sim in sims:
                dialog.add_row(SimPickerRow(sim.id, False, tag=sim))

            dialog.add_listener(callback)
            dialog.show_dialog()
        except BaseException as e:
            error_trap(e)

    def pick_sims_listen_to_music(self, timeline):
        try:
            def get_simpicker_results_callback(dialog):
                if not dialog.accepted:
                    return
                self.music_alarm.add_picked_sims(dialog.get_result_tags())
                self.music_alarm.add_listen_alarm()

            self.picker("Select Sims", "Pick up to 50 Sims", 50, get_simpicker_results_callback)
        except BaseException as e:
            error_trap(e)

    def stop_listening_to_music(self, timeline):
        try:
            if self.target.is_sim:
                self.music_alarm.kill_sim_alarm(self.target)
                self.music_alarm.remove_picked_sim(self.target)
                return
            self.music_alarm.kill_all_alarms()
        except BaseException as e:
            error_trap(e)

    def message_box(self, icon_top, icon_bottom, title, text, show_icon=True, color="DEFAULT"):
        try:
            if show_icon:
                icon = lambda _: IconInfoData(obj_instance=icon_top)
                secondary_icon = lambda _: IconInfoData(obj_instance=icon_bottom)
            else:
                icon = None
                secondary_icon = None
            if color is "PURPLE":
                urgency = UiDialogNotification.UiDialogNotificationUrgency.DEFAULT
                information_level = UiDialogNotification.UiDialogNotificationLevel.SIM
                visual_type = UiDialogNotification.UiDialogNotificationVisualType.SPECIAL_MOMENT
            elif color is "ORANGE":
                urgency = UiDialogNotification.UiDialogNotificationUrgency.URGENT
                information_level = UiDialogNotification.UiDialogNotificationLevel.PLAYER
                visual_type = UiDialogNotification.UiDialogNotificationVisualType.INFORMATION
            elif color is "GREEN":
                urgency = UiDialogNotification.UiDialogNotificationUrgency.DEFAULT
                information_level = UiDialogNotification.UiDialogNotificationLevel.PLAYER
                visual_type = UiDialogNotification.UiDialogNotificationVisualType.INFORMATION
            else:
                urgency = UiDialogNotification.UiDialogNotificationUrgency.DEFAULT
                information_level = UiDialogNotification.UiDialogNotificationLevel.SIM
                visual_type = UiDialogNotification.UiDialogNotificationVisualType.INFORMATION

            notification = UiDialogNotification.TunableFactory().default(icon_top,
                                                                         text=lambda
                                                                             **_: LocalizationHelperTuning.get_raw_text(
                                                                             text),
                                                                         title=lambda
                                                                             **_: LocalizationHelperTuning.get_raw_text(
                                                                             '<font size="20" color="#ffffff"><b>' + title + '</b></font>'),
                                                                         icon=icon,
                                                                         secondary_icon=secondary_icon,
                                                                         urgency=urgency,
                                                                         information_level=information_level,
                                                                         visual_type=visual_type,
                                                                         expand_behavior=1, dialog_options=0)
            notification.show_dialog()
        except BaseException as e:
            error_trap(e)

    def get_music_folder(self, filename):
        filters = []
        datapath = os.path.abspath(os.path.dirname(__file__))
        filename = datapath + r"\Data\{}.dat".format(filename)
        try:
            file = open(filename, "r")
        except:
            return None
        lines = file.readlines()
        for line in lines:
            line = line.strip('\n')
            if len(line) > 0:
                folder = line
        file.close()
        if len(folder) == 0:
            return None
        return folder

    def get_help(self):
        datapath = os.path.abspath(os.path.dirname(__file__))
        filename = datapath + r"\Data\help.dat"
        try:
            file = open(filename, "r")
        except:
            return None
        output = ""
        lines = file.readlines()
        for line in lines:
            if len(line) > 0:
                output += line
        file.close()
        return output

    def _playlist(self, filename, append=False, load=False):
        datapath = os.path.abspath(os.path.dirname(__file__))
        if append:
            filename = datapath + r"\Playlists\{}.m3u".format(filename)
            file = open(filename, "a")
            for playlist in MusicMenu.playlist:
                file.write(playlist + "\n")
        elif load:
            filename = datapath + r"\Playlists\{}".format(filename)
            file = open(filename, 'r', errors='ignore')
            lines = file.readlines()
            for line in lines:
                line = line.strip('\n')
                if len(line) > 0:
                    MusicMenu.playlist.append(line)
        else:
            filename = datapath + r"\Playlists\{}.m3u".format(filename)
            file = open(filename, "w")
            for playlist in MusicMenu.playlist:
                file.write(playlist + "\n")
        file.close()

    def load_playlist(self, timeline):
        try:
            datapath = os.path.abspath(os.path.dirname(__file__)) + r"\Playlists"
            files = [f for f in os.listdir(datapath) if ".m3u" in f or ".m3u8" in f]

            self.music_choice.MAX_MENU_ITEMS_TO_LIST = 10
            self.music_choice.commands = []
            self.music_choice.commands.append("<font color='#990000'>[Menu]</font>")

            if len(files) > 0:
                self.music_choice.show(timeline, self, 0, files, "Load Menu\n{}".format(MusicMenu.datapath),
                                       "Choose a playlist to associate with a genre", "load_music_playlist", True, True)
            else:
                ld_notice(None, "Music Menu",
                          "No playlists found!", False,
                          "GREEN")
        except BaseException as e:
            error_trap(e)

    def save_new_playlist(self, timeline):
        self.music_playlist("[Save Playlist]")

    def help(self, timeline):
        self.music_playlist("[Help]")

    def build_new_playlist(self, timeline):
        self.music_playlist("[Build New Playlist]")

    def save_playlist(self, filename):
        self._playlist(filename)
        self.music_playlist()

    def make_playlist(self, timeline):
        self.music_playlist()

    def load_music_playlist(self, filename=""):
        try:
            if "[Menu]" in filename:
                self.playlist_options(None)
                return

            self._playlist(filename, False, True)

            results = []
            for playlist in MusicMenu.playlist:
                results.append(os.path.basename(playlist))

            self.music_choice.MAX_MENU_ITEMS_TO_LIST = 8
            self.music_choice.commands = []
            self.music_choice.commands.append("<font color='#990000'>[Menu]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Save Playlist]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Clear Playlist]</font>")

            self.music_choice.show(None, self, 0, results, "Search Menu\n{}\nPlaylist has {} entries.".format(MusicMenu.datapath, len(MusicMenu.playlist)),
                                   "", "music_playlist", True, True)

        except BaseException as e:
            error_trap(e)

    def playlist_max_size(self, timeline):
        dialogtest_input("Set Max Size", "Max size for playlists.", self.set_max_size, self.music_playlist)

    def set_max_size(self, size):
        MusicMenu.MAX_PLAYLIST = int(size)
        self.music_playlist()

    def search_playlist(self, timeline):
        self.music_playlist("[Search]")

    def random_playlist(self, timeline):
        self.music_playlist("[Random Playlist]")

    def random_music(self):
        try:
            results = []
            menu_list = []
            if len(MusicMenu.playlist):
                results = MusicMenu.playlist
                MusicMenu.playlist = []
            else:
                for root, dirs, files in os.walk(MusicMenu.datapath):
                    for file in files:
                        f = os.path.join(root, file)
                        if ".mp3" in f.lower():
                            results.append(f)
            random.shuffle(results)
            for i, file in enumerate(results):
                if i < MusicMenu.MAX_PLAYLIST:
                    MusicMenu.playlist.append(file)
                    menu_list.append(os.path.basename(file))

            self.music_choice.MAX_MENU_ITEMS_TO_LIST = 8
            self.music_choice.commands = []
            self.music_choice.commands.append("<font color='#990000'>[Menu]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Save Playlist]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Clear Playlist]</font>")
            self.music_choice.show(None, self, 0, menu_list, "Music Menu\n{}\nPlaylist has {} entries.".format(MusicMenu.datapath, len(MusicMenu.playlist)),
                                       "", "music_playlist", True, True)
        except BaseException as e:
            error_trap(e)

    def clear_playlist(self, timeline):
        self.music_playlist("[Clear Playlist]")

    def search_music(self, search):
        try:
            results = []
            playlist = []
            if "[Back]" in search:
                self.music_playlist()
                return

            for root, dirs, files in os.walk(MusicMenu.datapath):
                for file in files:
                    f = os.path.join(root, file)
                    if ".mp3" in f.lower() and search.lower() in f.lower():
                        playlist.append(f)
            random.shuffle(playlist)
            for i, file in enumerate(playlist):
                if i < MusicMenu.MAX_PLAYLIST:
                    MusicMenu.playlist.append(file)
                    results.append(os.path.basename(file))


            self.music_choice.MAX_MENU_ITEMS_TO_LIST = 8
            self.music_choice.commands = []
            self.music_choice.commands.append("<font color='#990000'>[Menu]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Save Playlist]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Clear Playlist]</font>")

            self.music_choice.show(None, self, 0, results, "Search Menu\n{}\nPlaylist has {} entries.".format(MusicMenu.datapath, len(MusicMenu.playlist)),
                                   "", "music_playlist", True, True)
        except BaseException as e:
            error_trap(e)

    def default_music_directory(self, timeline):
        self.music_playlist("[Default Music Directory]")

    def custom_music_directory(self, timeline):
        self.music_playlist("[Custom Music Directory]")

    def music_playlist(self, filename=""):
        try:

            filename = filename.replace("<font color='#990000'>", "")
            filename = filename.replace("</font>", "")

            if "[Menu]" in filename:
                self.playlist_options(None)
                return
            elif "[Search]" in filename:
                dialogtest_input("Search\n{}".format(MusicMenu.datapath),
                             "Type in search term", self.search_music, self.music_playlist)
                return
            elif "[Help]" in filename:
                help_text = self.get_help()
                ld_notice(None, "Help", help_text, False, "GREEN")
                files = [f for f in os.listdir(MusicMenu.datapath) if
                         os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif "[Bookmark Index]" in filename:
                MusicMenu.index = self.music_choice.main_index
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif "[Load Bookmark]" in filename:
                self.music_choice.main_index = MusicMenu.index
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif "[Default Music Directory]" in filename:
                MusicMenu.datapath = os.path.join(os.environ['USERPROFILE'], "Music")
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif "[Custom Music Directory]" in filename:
                MusicMenu.datapath = r"{}".format(self.get_music_folder("music"))
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif "[Add All To Playlist]" in filename:
                files = [f for f in os.listdir(MusicMenu.datapath) if ".mp3" in f.lower()]
                for filename in files:
                    MusicMenu.playlist.append(join(MusicMenu.datapath, filename))
                files = [f for f in os.listdir(MusicMenu.datapath) if
                     os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif "[Random Playlist]" in filename:
                self.random_music()
                return
            elif "[Clear Playlist]" in filename:
                MusicMenu.playlist = []
                files = [f for f in os.listdir(MusicMenu.datapath) if
                     os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif "[Save Playlist]" in filename:
                dialogtest_input("Save Playlist",
                             "Type in name of playlist", self.save_playlist, self.music_playlist)
                return
            elif "[Build New Playlist]" in filename:
                MusicMenu.filename = None
                MusicMenu.append = False
                self.genre.show(None, self, 0, self.music_menu_choices, "{}".format(MusicMenu.datapath),
                                "Switch that selected folder to what genre")
                return
            elif "[Append To Playlist]" in filename:
                MusicMenu.filename = None
                MusicMenu.append = True
                self.genre.show(None, self, 0, self.music_menu_choices, "{}".format(MusicMenu.filename),
                                "Switch that selected folder to what genre")
                return
            elif "[Up One Directory]" in filename and len(MusicMenu.datapath) == 3 and ":" in MusicMenu.datapath:
                files = re.findall(r"[A-Z]+:.*$", os.popen("mountvol /").read(), re.MULTILINE)
                MusicMenu.datapath = ""
            elif "[Up One Directory]" in filename or "[Back]" in filename:
                parent = os.path.dirname(MusicMenu.datapath)
                MusicMenu.datapath = parent
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif len(filename) == 3 and ":" in filename:
                MusicMenu.datapath = filename
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif os.path.isdir(join(MusicMenu.datapath, filename)):
                child = os.path.abspath(os.path.join(MusicMenu.datapath, filename))
                MusicMenu.datapath = child
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            else:
                MusicMenu.playlist.append(join(MusicMenu.datapath, filename))
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]

            self.music_choice.MAX_MENU_ITEMS_TO_LIST = 8
            self.music_choice.commands = []
            self.music_choice.commands.append("<font color='#990000'>[Menu]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Up One Directory]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Append To Playlist]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Add All To Playlist]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Save Playlist]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Clear Playlist]</font>")

            self.music_choice.show(None, self, self.music_choice.main_index, files, "Music Menu\n{}\nPlaylist has {} entries.".format(MusicMenu.datapath, len(MusicMenu.playlist)),
                                   "", "music_playlist", True, True)

        except BaseException as e:
            error_trap(e)

    def change_music_directory(self, timeline):
        try:
            files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]

            self.music_choice.MAX_MENU_ITEMS_TO_LIST = 8
            self.music_choice.commands = []
            self.music_choice.commands.append("<font color='#990000'>[Menu]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Default Music Directory]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Custom Music Directory]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Up One Directory]</font>")

            if len(files) > 0:
                self.music_choice.show(timeline, self, 0, files, "Music Menu\n{}".format(MusicMenu.datapath),
                                       "Choose a folder to associate with a genre", "music_directory", True)
            else:
                ld_notice(None, "Music Menu",
                          "No music found! You need to fill your music folder under your user profile with folders "
                          "containing mp3 files only. eg: name a folder by artist name and fill that folder with that "
                          "artists songs!", False,
                          "GREEN")
        except BaseException as e:
            error_trap(e)

    def music_directory(self, filename=""):
        try:
            filename = filename.replace("<font color='#990000'>", "")
            filename = filename.replace("</font>", "")

            if "[Menu]" in filename:
                self._run_interaction_gen(None)
                return
            elif "[Use This Directory]" in filename:
                MusicMenu.filename = MusicMenu.datapath
                self.genre.show(None, self, 0, self.music_menu_choices, "{}".format(MusicMenu.filename),
                                "Switch that selected folder to what genre")
                return
            elif "[Up One Directory]" in filename and len(MusicMenu.datapath) == 3 and ":" in MusicMenu.datapath:
                files = re.findall(r"[A-Z]+:.*$", os.popen("mountvol /").read(), re.MULTILINE)
                MusicMenu.datapath = ""
            elif "[Up One Directory]" in filename:
                parent = os.path.dirname(MusicMenu.datapath)
                MusicMenu.datapath = parent
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif len(filename) == 3 and ":" in filename:
                MusicMenu.datapath = filename
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif "[Default Music Directory]" in filename:
                MusicMenu.datapath = os.path.join(os.environ['USERPROFILE'], "Music")
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            elif "[Custom Music Directory]" in filename:
                MusicMenu.datapath = r"{}".format(self.get_music_folder("music"))
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]
            else:
                child = os.path.abspath(os.path.join(MusicMenu.datapath, filename))
                MusicMenu.datapath = child
                files = [f for f in os.listdir(MusicMenu.datapath) if os.path.isdir(join(MusicMenu.datapath, f)) or ".mp3" in f.lower()]

            self.music_choice.MAX_MENU_ITEMS_TO_LIST = 8
            self.music_choice.commands = []
            self.music_choice.commands.append("<font color='#990000'>[Menu]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Default Music Directory]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Custom Music Directory]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Up One Directory]</font>")
            self.music_choice.commands.append("<font color='#990000'>[Use This Directory]</font>")

            if len(files) > 0:
                self.music_choice.show(None, self, 0, files, "Music Menu\n{}".format(MusicMenu.datapath),
                                       "Choose a folder to associate with a genre", "music_directory", True)
        except BaseException as e:
            error_trap(e)

    def volume_low(self, timeline):
        name = self.target.__class__.__name__.lower()
        if "earbud" in name:
            self.music_alarm.push_sim_function(self.sim, self.target, 164800)
        else:
            self.music_alarm.push_sim_function(self.sim, self.target, 14313)

    def volume_med(self, timeline):
        name = self.target.__class__.__name__.lower()
        if "earbud" in name:
            self.music_alarm.push_sim_function(self.sim, self.target, 164801)
        else:
            self.music_alarm.push_sim_function(self.sim, self.target, 14314)

    def volume_high(self, timeline):
        name = self.target.__class__.__name__.lower()
        if "earbud" in name:
            self.music_alarm.push_sim_function(self.sim, self.target, 164799)
        else:
            self.music_alarm.push_sim_function(self.sim, self.target, 14312)

    def volume_highest(self, timeline):
        name = self.target.__class__.__name__.lower()
        if "earbud" in name:
            self.music_alarm.push_sim_function(self.sim, self.target, 5022125439428740580)
        else:
            self.music_alarm.push_sim_function(self.sim, self.target, 5022125439428740507)

    def headphones(self, timeline):
        self.music_alarm.push_sim_function(self.sim, self.target, 5022125439428740508)

    def high_quality(self, timeline):
        self.music_alarm.push_sim_function(self.sim, self.target, 5022125439428740509)

    def _list_genres(self, filename: str):
        MusicMenu.filename = filename
        self.genre.show(None, self, 0, self.music_menu_choices, "Music Menu",
                        "Switch that selected folder to what genre")

    def heavy_metal(self, timeline):
        try:
            if MusicMenu.filename is None and len(MusicMenu.playlist) > 0:
                if not MusicMenu.append:
                    self._playlist("Heavy Metal")
                    os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\METAL"')
                    os.system(r'mkdir "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\METAL"')
                else:
                    self._playlist("Heavy Metal", True)
                for playlist in MusicMenu.playlist:
                    os.system(
                        r'mklink "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\METAL\{}" "{}"'.format(
                            os.path.basename(playlist), playlist))
            else:
                os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\METAL"')
                os.system(
                    r'mklink /D "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\METAL" "{}"'.format(
                        MusicMenu.filename))
            self.music_playlist()
        except BaseException as e:
            error_trap(e)

    def classic_rock(self, timeline):
        try:
            if MusicMenu.filename is None and len(MusicMenu.playlist) > 0:
                if not MusicMenu.append:
                    self._playlist("Classic Rock")
                    os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Classical"')
                    os.system(r'mkdir "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Classical"')
                else:
                    self._playlist("Classic Rock", True)
                for playlist in MusicMenu.playlist:
                    os.system(
                        r'mklink "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Classical\{}" "{}"'.format(
                            os.path.basename(playlist), playlist))
            else:
                os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Classical"')
                os.system(
                    r'mklink /D "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Classical" "{}"'.format(
                        MusicMenu.filename))
            self.music_playlist()
        except BaseException as e:
            error_trap(e)

    def grindcore(self, timeline):
        try:
            if MusicMenu.filename is None and len(MusicMenu.playlist) > 0:
                if not MusicMenu.append:
                    self._playlist("Grindcore")
                    os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Grindcore"')
                    os.system(r'mkdir "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Grindcore"')
                else:
                    self._playlist("Grindcore", True)
                for playlist in MusicMenu.playlist:
                    os.system(
                        r'mklink "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Grindcore\{}" "{}"'.format(
                            os.path.basename(playlist), playlist))
            else:
                os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Grindcore"')
                os.system(
                    r'mklink /D "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Grindcore" "{}"'.format(
                        MusicMenu.filename))
            self.music_playlist()
        except BaseException as e:
            error_trap(e)

    def death_metal(self, timeline):
        try:
            if MusicMenu.filename is None and len(MusicMenu.playlist) > 0:
                if not MusicMenu.append:
                    self._playlist("Death Metal")
                    os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Death Metal"')
                    os.system(r'mkdir "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Death Metal"')
                else:
                    self._playlist("Death Metal", True)
                for playlist in MusicMenu.playlist:
                    os.system(
                        r'mklink "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Death Metal\{}" "{}"'.format(
                            os.path.basename(playlist), playlist))
            else:
                os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Death Metal"')
                os.system(
                    r'mklink /D "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Death Metal" "{}"'.format(
                        MusicMenu.filename))
            self.music_playlist()
        except BaseException as e:
            error_trap(e)

    def black_metal(self, timeline):
        try:
            if MusicMenu.filename is None and len(MusicMenu.playlist) > 0:
                if not MusicMenu.append:
                    self._playlist("Black Metal")
                    os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Black Metal"')
                    os.system(r'mkdir "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Black Metal"')
                else:
                    self._playlist("Black Metal", True)
                for playlist in MusicMenu.playlist:
                    os.system(
                        r'mklink "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Black Metal\{}" "{}"'.format(
                            os.path.basename(playlist), playlist))
            else:
                os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Black Metal"')
                os.system(
                    r'mklink /D "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Black Metal" "{}"'.format(
                        MusicMenu.filename))
            self.music_playlist()
        except BaseException as e:
            error_trap(e)

    def rap(self, timeline):
        try:
            if MusicMenu.filename is None and len(MusicMenu.playlist) > 0:
                if not MusicMenu.append:
                    self._playlist("Rap")
                    os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Hip Hop"')
                    os.system(r'mkdir "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Hip Hop"')
                else:
                    self._playlist("Rap", True)
                for playlist in MusicMenu.playlist:
                    os.system(
                        r'mklink "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Hip Hop\{}" "{}"'.format(
                            os.path.basename(playlist), playlist))
            else:
                os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Hip Hop"')
                os.system(
                    r'mklink /D "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Hip Hop" "{}"'.format(
                        MusicMenu.filename))
            self.music_playlist()
        except BaseException as e:
            error_trap(e)

    def ambient(self, timeline):
        try:
            if MusicMenu.filename is None and len(MusicMenu.playlist) > 0:
                if not MusicMenu.append:
                    self._playlist("Ambient")
                    os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Strange Tunes"')
                    os.system(r'mkdir "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Strange Tunes"')
                else:
                    self._playlist("Ambient", True)
                for playlist in MusicMenu.playlist:
                    os.system(
                        r'mklink "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Strange Tunes\{}" "{}"'.format(
                            os.path.basename(playlist), playlist))
            else:
                os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Strange Tunes"')
                os.system(
                    r'mklink /D "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Strange Tunes" "{}"'.format(
                        MusicMenu.filename))
            self.music_playlist()
        except BaseException as e:
            error_trap(e)

    def dance(self, timeline):
        try:
            if MusicMenu.filename is None and len(MusicMenu.playlist) > 0:
                if not MusicMenu.append:
                    self._playlist("Dance")
                    os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Alternative"')
                    os.system(r'mkdir "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Alternative"')
                else:
                    self._playlist("Dance", True)
                for playlist in MusicMenu.playlist:
                    os.system(
                        r'mklink "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Alternative\{}" "{}"'.format(
                            os.path.basename(playlist), playlist))
            else:
                os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Alternative"')
                os.system(
                    r'mklink /D "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Alternative" "{}"'.format(
                        MusicMenu.filename))
            self.music_playlist()
        except BaseException as e:
            error_trap(e)

    def tape_deck(self, timeline):
        try:
            if MusicMenu.filename is None and len(MusicMenu.playlist) > 0:
                if not MusicMenu.append:
                    self._playlist("Tape Deck")
                    os.system(r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Tape Deck"')
                    os.system(r'mkdir "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Tape Deck"')
                else:
                    self._playlist("Tape Deck", True)
                for playlist in MusicMenu.playlist:
                    os.system(
                        r'mklink "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Tape Deck\{}" "{}"'.format(
                            os.path.basename(playlist), playlist))
            else:
                os.system(
                    r'rmdir /s /q "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Tape Deck"')
                os.system(
                    r'mklink /D "%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Custom Music\Tape Deck" "{}"'.format(
                        MusicMenu.filename))
            self.music_playlist()
        except BaseException as e:
            error_trap(e)

    def reload_scripts(self, timeline):
        dialogtest_input("Reload Script",
                         "Type in name of script or leave blank to list all", self._reload_script_callback)

    def _reload_script_callback(self, script_file: str):
        try:
            datapath = os.path.abspath(os.path.dirname(__file__))
            if script_file == "":
                files = [f for f in os.listdir(datapath) if isfile(join(datapath, f))]
                files.insert(0, "all")
                self.script_choice.show(None, self, 0, files, "Reload Script",
                                        "Choose a script to reload", "_reload_script_final", True)
            else:
                ld_file_loader(script_file)
        except BaseException as e:
            error_trap(e)

    def _reload_script_final(self, filename: str):
        try:
            ld_file_loader(filename)
        except BaseException as e:
            error_trap(e)
