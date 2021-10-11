import sims4.commands
import services
from music_util import ld_notice
from sims4.localization import LocalizationHelperTuning
from ui.ui_dialog import UiDialog, UiDialogOk, UiDialogOkCancel

##
## Custom classes to hack a text input
##
class DialogTestUiDialogTextInput(UiDialog):
    __qualname__ = 'DialogTestUiDialogTextInput'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_input_responses = {}

    def on_text_input(self, text_input_name='', text_input=''):
        self.text_input_responses[text_input_name] = text_input
        return False

    def build_msg(self, text_input_overrides=None, additional_tokens=(), **kwargs):
        msg = super().build_msg(additional_tokens=additional_tokens, **kwargs)
        text_input_msg1 = msg.text_input.add()
        text_input_msg1.text_input_name = "userinput"
        #text_input_msg1.max_length = nn
        #text_input_msg1.min_length = nn
        return msg

class DialogTestUiDialogTextInputOkCancel(UiDialogOkCancel, DialogTestUiDialogTextInput):
    __qualname__ = 'DialogTestUiDialogTextInputOkCancel'

##
## Get input from user dialog test
##
def dialogtest_input(title: str, text: str, callback, return_callback=None):
    input_text = ""
    def dialogtest_input_callback(dialog):
        if dialog.accepted:
            input_text = dialog.text_input_responses.get("userinput")
            callback(input_text)
        else:
            if return_callback:
                return_callback()
            return
    client = services.client_manager().get_first_client()
    dialog = DialogTestUiDialogTextInputOkCancel.TunableFactory().default(client.active_sim,
        text=lambda **_: LocalizationHelperTuning.get_raw_text(text),
        title=lambda **_: LocalizationHelperTuning.get_raw_text(title))
    dialog.add_listener(dialogtest_input_callback)
    dialog.show_dialog()

def get_input_callback(input_str):
    client = services.client_manager().get_first_client()
    sim_info = client.active_sim.sim_info
    ld_notice(sim_info,"get_input_callback", input_str)
##
## Ok/Cancel dialog test
##
@sims4.commands.Command('dialogtest.okcancel',  command_type=sims4.commands.CommandType.Live)
def dialogtest_okcancel(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    def dialogtest_okcancel_callback(dialog):
        if dialog.accepted:
            output("User pressed OK")
        else:
            output("User pressed CANCEL")
    title = "Dialog Test 1"
    text = "Please press OK to continue, or Cancel."
    client = services.client_manager().get_first_client()
    dialog = UiDialogOkCancel.TunableFactory().default(client.active_sim, text=lambda **_: LocalizationHelperTuning.get_raw_text(text), title=lambda **_: LocalizationHelperTuning.get_raw_text(title))
    dialog.add_listener(dialogtest_okcancel_callback)
    dialog.show_dialog()