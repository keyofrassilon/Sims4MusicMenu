import os

import build_buy
import enum
import services
from interactions.base.immediate_interaction import ImmediateSuperInteraction
from interactions.context import InteractionContext, QueueInsertStrategy
from interactions.interaction_finisher import FinishingType
from interactions.priority import Priority
from music_util import error_trap, ld_notice


class ListenMusicBehavior(enum.Int):
    LISTEN = 0
    SITTING_DOWN = 1
    SEATED = 2
    SOCIAL = 3
    GOHERE = 4
    HEADBANG = 5


class MusicJobs(ImmediateSuperInteraction):
    countdown = 20
    remove_sim = None

    def __init__(self, *args, **kwargs):
        (super().__init__)(*args, **kwargs)
        self.picked_sims = []

    def _run_interaction_gen(self, timeline):
        return

    def add_picked_sims(self, sims):
        self.picked_sims = sims

    def remove_picked_sim(self, sim):
        MusicJobs.remove_sim = sim

    def clear_sim_instance(self, sim, filter=None, all_but_filter=True):
        try:
            if filter is None:
                filter = ""
            filter = filter.lower()
            value = filter.split("|")
            if len(value) == 0:
                value = [filter, ""]
            for interaction in sim.get_all_running_and_queued_interactions():
                if interaction is not None:
                    title = interaction.__class__.__name__
                    title = title.lower()
                    if all_but_filter is False and filter != "":
                        cancel = False
                        for v in value:
                            if v in title and v != "":
                                cancel = True
                        if cancel is True:
                            interaction.cancel(FinishingType.KILLED, 'Stop')

                    elif filter != "":
                        cancel = True
                        for v in value:
                            if v in title and v != "":
                                cancel = False
                        if cancel is True:
                            interaction.cancel(FinishingType.KILLED, 'Stop')
                    else:
                        interaction.cancel(FinishingType.KILLED, 'Stop')
        except BaseException as e:
            error_trap(e)

    def push_sim_function(self, sim, target, dc_interaction: int):
        affordance_manager = services.affordance_manager()
        context = InteractionContext(sim, (InteractionContext.SOURCE_SCRIPT_WITH_USER_INTENT),
                                     (Priority.High), insert_strategy=(QueueInsertStrategy.FIRST))
        sim.push_super_affordance(affordance_manager.get(dc_interaction),
                                  target, context)

    def get_social_filters(self, filename):
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
            values = line.split("|")
            filters.extend(values)
        file.close()
        if len(filters) == 0:
            return None
        return filters

    def distance_to(self, target, dest):
        return (target.position - dest.position).magnitude_2d()

    def picked_sims_listen(self):
        try:
            action_target = None
            for sim in list(self.picked_sims):
                if MusicJobs.remove_sim is not None:
                    if [sim for sim in self.picked_sims if sim == MusicJobs.remove_sim]:
                        self.picked_sims.remove(MusicJobs.remove_sim)
                        MusicJobs.remove_sim = None
                        continue
                    else:
                        MusicJobs.remove_sim = None

                behavior = ListenMusicBehavior.LISTEN
                if "earbuds" in str(self.target).lower():
                    dist = 0
                else:
                    dist = self.distance_to(sim, self.target)
                obj_room_id = build_buy.get_room_id(self.target.zone_id, self.target.position, self.target.level)
                sim_room_id = build_buy.get_room_id(sim.zone_id, sim.position, sim.level)
                interactions = sim.get_all_running_and_queued_interactions()

                # check if custom radio sound is active
                if self.target is not None:
                    if hasattr(self.target, "primitives"):
                        if hasattr(sim, "primitives"):
                            if "sound" not in str(self.target.primitives).lower() and "sound" not in str(sim.primitives).lower():
                                self.remove_listen_alarm()
                                return

                for action in interactions:
                    action_title = action.__class__.__name__.lower()
                    if action.target is not None:
                        action_dist = self.distance_to(sim, action.target)
                    else:
                        action_dist = 0

                    if "gohere" in action_title:
                        behavior = ListenMusicBehavior.GOHERE
                    if behavior != ListenMusicBehavior.GOHERE:
                        filters = self.get_social_filters("filters")
                        if filters is not None:
                            if [f for f in filters if f in action_title and f is not "" and f is not None]:
                                if action.is_user_directed:
                                    MusicJobs.countdown = 999
                                behavior = ListenMusicBehavior.SOCIAL
                                action_target = action.target
                        if behavior != ListenMusicBehavior.SOCIAL:
                            MusicJobs.countdown = 20
                            if "headbang" in action_title:
                                behavior = ListenMusicBehavior.HEADBANG
                            if "sit_passive" in action_title:
                                behavior = ListenMusicBehavior.SEATED
                            if "seating_sit" in action_title and action_dist > 0.1:
                                if behavior != ListenMusicBehavior.SEATED:
                                    behavior = ListenMusicBehavior.SITTING_DOWN


                if behavior == ListenMusicBehavior.GOHERE:
                    self.clear_sim_instance(sim, "listen", False)
                    continue
                if MusicJobs.countdown < 1:
                    MusicJobs.countdown = 20
                    if action_target is not None:
                        if action_target.is_sim:
                            self.clear_sim_instance(action_target, "sit")
                            self.push_sim_function(action_target, action_target, 18240980946975959663)
                            action_target = None
                    self.clear_sim_instance(sim, "sit")
                    self.push_sim_function(sim, sim, 18240980946975959663)
                    continue
                if behavior == ListenMusicBehavior.SOCIAL:
                    self.clear_sim_instance(sim, "listen", False)
                    if action_target is not None:
                        if action_target.is_sim:
                            self.clear_sim_instance(action_target, "listen", False)
                    MusicJobs.countdown = MusicJobs.countdown - 1
                    continue
                if action_target is not None:
                    if action_target.is_sim:
                        self.clear_sim_instance(action_target, "listen", False)
                        if action_target == sim:
                            continue
                if behavior == ListenMusicBehavior.SITTING_DOWN:
                    self.clear_sim_instance(sim, "listen", False)
                    continue
                if behavior == ListenMusicBehavior.HEADBANG:
                    self.clear_sim_instance(sim, "listen", False)
                    continue
                if obj_room_id != sim_room_id or dist > 8:
                    self.clear_sim_instance(sim)
                    self.push_sim_function(sim, self.target, 12677454845923784945)
                    continue
                self.clear_sim_instance(sim, "sit")
                self.push_sim_function(sim, sim, 18240980946975959663)

        except BaseException as e:
            error_trap(e)

