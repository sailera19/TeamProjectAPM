import pandas as pd
from collections import defaultdict, namedtuple
from pm4py.objects.petri.obj import PetriNet, Marking
from pm4py.objects.petri import utils
from pm4py.visualization.petri_net import visualizer as pn_visualizer


def run_alpha_algorithm(traces):
    all_activities, start_activities, end_activities, direct_successions = get_activities(traces)

    footprint = FootPrintMatrix(all_activities, direct_successions)
    all_pairs = footprint.find_pairs()
    maximal_pairs = remove_non_maximal_pairs(all_pairs)
    net = AlphaPetriNet(start_activities=start_activities, end_activities=end_activities,
                        all_activities=all_activities, maximal_pairs=maximal_pairs)

    return net


def get_activities(traces):
    """
    Get activity informations from traces.
    Returns set for all_activities, start_activities, end_activities and dict for direct_successions
    """
    start_activities = set()
    end_activities = set()
    all_activities = set()

    direct_successions = defaultdict(set)

    # go through all our traces
    for trace in traces:
        # add start and end activities
        start_activities.add(trace[0])
        end_activities.add(trace[-1])

        # add activities of trace to all activities
        all_activities.update(trace)

        # go through all activities in our trace and
        for idx, activity in enumerate(trace[1:], start=1):
            direct_successions[trace[idx - 1]].add(activity)

    Activities = namedtuple("Activities", ["all_activities", "start_activities", "end_activities", "direct_successions"])

    return Activities(all_activities, start_activities, end_activities, direct_successions)


class FootPrintMatrix:
    footprint_df: pd.DataFrame = None

    def __init__(self, all_activities, direct_successions):
        all_activities = sorted(list(all_activities))
        footprint = []

        for x in all_activities:
            row = []
            for y in all_activities:
                x_follows_y = x in direct_successions[y]
                y_follows_x = y in direct_successions[x]

                if y_follows_x and not x_follows_y:
                    row.append("→")
                elif x_follows_y and not y_follows_x:
                    row.append("←")
                elif x_follows_y and y_follows_x:
                    row.append("||")
                else:
                    row.append("#")
            footprint.append(row)

        self.footprint_df = pd.DataFrame(footprint, columns=all_activities, index=all_activities)

    def is_mergeable(self, p, q):
        """Check if two pairs are mergeable"""

        for pa in p[0]:
            # every activity in a must be #-(choice)-relation with every other element in a
            for qa in q[0]:
                if self.footprint_df[qa][pa] != "#":
                    return False

            # every activity in a must be in →-(causality)-relation with every activity in b
            for qb in q[1]:
                if self.footprint_df[qb][pa] != "→":
                    return False

        for pb in p[1]:
            # every activity in b must be #-(choice)-relation with every other element in b
            for qb in q[1]:
                if self.footprint_df[pb][qb] != "#":
                    return False

            # every activity in a must be in →-(causality)-relation with every activity in b
            for qa in q[0]:
                if self.footprint_df[pb][qa] != "→":
                    return False

        return True

    @staticmethod
    def merge_pairs(p, q):
        a = set(p[0])
        a.update(q[0])

        b = set(p[1])
        b.update(q[1])

        return (a, b)

    def find_pairs(self):
        # get all →-(causality)-relations
        pairs = [({self.footprint_df[col][self.footprint_df[col] == "→"].index[i]}, {col})
                 for col in self.footprint_df.columns for i in range(len(self.footprint_df[col][self.footprint_df[col] == '→'].index))]
        idx = 0
        while idx < len(pairs):
            p = pairs[idx]
            for q in pairs[idx + 1:]:
                # check if the pairs can be merged
                if self.is_mergeable(p, q):
                    # create and add the merged pair to pairs
                    merged_pair = self.merge_pairs(p, q)
                    if merged_pair not in pairs:
                        pairs.append(merged_pair)
            idx += 1
        return pairs


def remove_non_maximal_pairs(pairs):
    pairs = pairs.copy()
    idx = 0
    while idx < len(pairs) - 1:
        p = pairs[idx]
        non_max = False
        for q in pairs[idx+1:]:
            # check if current pair is a subset of another pair, if yes, remove pair
            if p[0].issubset(q[0]) and p[1].issubset(q[1]):
                pairs.pop(idx)
                non_max = True
                break
        if not non_max:
            idx += 1
    return pairs


class AlphaPetriNet:
    net: PetriNet = None
    initial_marking: Marking = None
    final_marking: Marking = None

    def __init__(self, start_activities, end_activities, all_activities, maximal_pairs):
        self.net = PetriNet("Example: Rehse")

        # create and add places
        source = PetriNet.Place("start")
        self.net.places.add(source)
        sink = PetriNet.Place("end")
        self.net.places.add(sink)

        # add tokens
        self.initial_marking = Marking()
        self.initial_marking[source] = 1
        self.final_marking = Marking()
        self.final_marking[sink] = 1

        # Add Transitions for all Activities
        transition_map = {}
        for activity in all_activities:
            transition = PetriNet.Transition(activity, activity)
            self.net.transitions.add(transition)
            transition_map[activity] = transition

        # Add Input Arc from Start Place (Source) to Start Activities/Transitions
        for activity in start_activities:
            utils.add_arc_from_to(source, transition_map[activity], self.net)

        # Add Output Arc from End Activities/Transitions to End Place (Sink)
        for activity in end_activities:
            utils.add_arc_from_to(transition_map[activity], sink, self.net)

        # Add Input and Output Arcs for all our Pairs
        for idx, pair in enumerate(maximal_pairs, start=1):
            place = PetriNet.Place("p%d" % idx)
            self.net.places.add(place)

            for a in pair[0]:
                utils.add_arc_from_to(transition_map[a], place, self.net)

            for b in pair[1]:
                utils.add_arc_from_to(place, transition_map[b], self.net)

    def show(self):
        gviz = pn_visualizer.apply(self.net, self.initial_marking, self.final_marking)
        pn_visualizer.view(gviz)