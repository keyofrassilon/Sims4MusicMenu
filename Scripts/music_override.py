import os

from interactions.utils.audio import TunablePlayStoredAudioFromSource, ApplyAudioEffect
from music_util import ld_notice, error_trap, clean_string
from objects.components.types import STORED_AUDIO_COMPONENT
from snippets import MUSIC_TRACK_DATA

setattr(ApplyAudioEffect, "DEBUG", False)

class MusicOverride(ApplyAudioEffect):
    def __init__(self, *args, **kwargs):
        (super().__init__)(*args, **kwargs)

    def start(self):
        try:
            if self.DEBUG:
                datapath = os.path.abspath(os.path.dirname(__file__))
                filename = datapath + r"\{}.log".format("music")
                if os.path.exists(filename):
                    append_write = 'a'  # append if already exists
                else:
                    append_write = 'w'  # make a new file if not
                file = open(filename, append_write)
                output = ""

            if not self.running:
                if self.target is not None:
                    if self.DEBUG:
                        result = self._audio_effect_data
                        for att in dir(result):
                            if hasattr(result, att):
                                output = output + "\n(" + str(att) + "): " + clean_string(
                                    str(getattr(result, att)))

                    self.target.append_audio_effect(self.tag_name, self._audio_effect_data)
                    self._running = True

            if self.DEBUG:
                file.write("\nAUDIO: {}\n".format(output))
                file.close()
        except BaseException as e:
            error_trap(e)


ApplyAudioEffect.start = MusicOverride.start
