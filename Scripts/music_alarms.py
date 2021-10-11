import alarms
import date_and_time
from interactions.base.immediate_interaction import ImmediateSuperInteraction
from music_jobs import MusicJobs
from music_util import ld_notice, error_trap

class MusicAlarmTracker:
    def __init__(self, sim, alarm, *args, **kwargs):
        (super().__init__)(*args, **kwargs)
        self.sim = sim
        self.alarm = alarm

class MusicMoshInteraction(ImmediateSuperInteraction):

    def __init__(self, *args, **kwargs):
        (super().__init__)(*args, **kwargs)
        self.music_alarm = MusicAlarms(*args, **kwargs)

    def _run_interaction_gen(self, timeline):
        self.music_alarm.push_sim_function(self.sim, self.sim, 240309)


class MusicDanceInteraction(ImmediateSuperInteraction):

    def __init__(self, *args, **kwargs):
        (super().__init__)(*args, **kwargs)
        self.music_alarm = MusicAlarms(*args, **kwargs)

    def _run_interaction_gen(self, timeline):
        return


class MusicListenInteraction(ImmediateSuperInteraction):

    def __init__(self, *args, **kwargs):
        (super().__init__)(*args, **kwargs)
        self.music_alarm = MusicAlarms(*args, **kwargs)

    def _run_interaction_gen(self, timeline):
        try:
            self.music_alarm.picked_sims = []
            self.music_alarm.picked_sims.append(self.sim)
            if self.music_alarm.LISTEN_ALARM is None:
                self.music_alarm.add_listen_alarm()
        except BaseException as e:
            error_trap(e)

class MusicAlarms(MusicJobs):
    alarm_tracker = []

    def __init__(self, *args, **kwargs):
        (super().__init__)(*args, **kwargs)
        self.LISTEN_ALARM = None

    def _run_interaction_gen(self, timeline):
        return

    def listen_alarm_callback(self, _):
        if self.LISTEN_ALARM is None:
            return
        self.picked_sims_listen()

    def remove_listen_alarm(self):
        if self.LISTEN_ALARM is None:
            return
        for sim in self.picked_sims:
            self.clear_sim_instance(sim, "listen", False)
        alarms.cancel_alarm(self.LISTEN_ALARM)
        self.LISTEN_ALARM = None

    def add_listen_alarm(self):
        if self.LISTEN_ALARM is not None:
            self.remove_listen_alarm()
        self.LISTEN_ALARM = alarms.add_alarm(self, (date_and_time.TimeSpan(4000)),
            self.listen_alarm_callback, repeating=True, cross_zone=False)
        MusicJobs.remove_sim = None
        MusicAlarms.alarm_tracker.append(MusicAlarmTracker(self.sim, self.LISTEN_ALARM))

    def kill_all_alarms(self):
        for alarm in list(MusicAlarms.alarm_tracker):
            if alarm.alarm is not None:
                self.clear_sim_instance(alarm.sim, "listen", False)
                alarms.cancel_alarm(alarm.alarm)
                MusicAlarms.alarm_tracker.remove(alarm)

    def kill_sim_alarm(self, sim):
        for alarm in list(MusicAlarms.alarm_tracker):
            if alarm.alarm is not None and alarm.sim == sim:
                self.clear_sim_instance(alarm.sim, "listen", False)
                alarms.cancel_alarm(alarm.alarm)
                MusicAlarms.alarm_tracker.remove(alarm)


