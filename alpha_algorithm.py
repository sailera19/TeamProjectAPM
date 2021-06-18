import pandas as pd
from collections import defaultdict, namedtuple
from pm4py.objects.petri.obj import PetriNet, Marking
from pm4py.objects.petri import utils
from pm4py.visualization.petri_net import visualizer as pn_visualizer


def run_alpha_algorithm(traces, min_support=None, include_start_end=True, activity_map=None):
    traces = filter_traces(traces, min_support=min_support, include_start_end=include_start_end)
    all_activities, start_activities, end_activities, direct_successions, direct_successions_count \
        = get_activities(traces)

    footprint = FootPrintMatrix(all_activities, direct_successions)
    all_pairs = footprint.find_pairs()
    maximal_pairs = remove_non_maximal_pairs(all_pairs)
    net = AlphaPetriNet(start_activities=start_activities, end_activities=end_activities,
                        all_activities=all_activities, maximal_pairs=maximal_pairs, activity_map=activity_map)

    return net


def run_alpha_algorithm_min_count(traces, min_count):
    all_activities, start_activities, end_activities, direct_successions, direct_successions_count \
        = get_activities(traces)

    footprint = FootPrintMatrixMinCount(all_activities, direct_successions_count, min_count)
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
    #all_activities = set()
    all_activities = set([inner for outer in traces for inner in outer])

    direct_successions = defaultdict(set)

    # initialize with count 0 for all successions
    direct_successions_count = {y: {x: 0 for x in all_activities} for y in all_activities}


    # go through all our traces
    for trace in traces:
        # add start and end activities
        start_activities.add(trace[0])
        end_activities.add(trace[-1])

        # add activities of trace to all activities
        all_activities.update(trace)

        # go through all activities in our trace and
        for predecessor, successor in zip(trace[:-1], trace[1:]):
            direct_successions[predecessor].add(successor)
            direct_successions_count[predecessor][successor] += 1

    direct_successions_count = {key_outer: {
        key_inner: val_inner for key_inner, val_inner in val_outer.items() if val_inner > 0}
        for key_outer, val_outer in direct_successions_count.items()}
    direct_successions_count = {key: val for key, val in direct_successions_count.items() if len(val) > 0}

    Activities = namedtuple("Activities", ["all_activities", "start_activities", "end_activities", "direct_successions",
                                           "direct_successions_count"])

    return Activities(all_activities, start_activities, end_activities, direct_successions, direct_successions_count)


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


class FootPrintMatrixMinCount(FootPrintMatrix):
    def __init__(self, all_activities, direct_successions_count, min_count):
        all_activities = sorted(list(all_activities))
        footprint = []

        for x in all_activities:
            row = []
            for y in all_activities:
                x_follows_y = y in direct_successions_count and x in direct_successions_count[y] and direct_successions_count[y][x] > min_count
                y_follows_x = x in direct_successions_count and y in direct_successions_count[x] and direct_successions_count[x][y] > min_count

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

    def __init__(self, start_activities, end_activities, all_activities, maximal_pairs, activity_map=None):
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
            transition = PetriNet.Transition(activity, activity_map[activity] if activity_map is not None else activity)
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


def filter_traces(traces, min_support=None, include_start_end=True):
    return_traces = traces.copy()
    print("Traces at the start: ", len(traces))
    if min_support:
        n_traces = len(return_traces)
        min_amount = round(min_support*n_traces)
        all_activities = set([inner for outer in traces for inner in outer])

        if include_start_end:
            # add start token
            all_activities.add("^")
            # add end token
            all_activities.add("$")

        possible_successions = [(x, y) for x in all_activities for y in all_activities]
        succession_counter = {x: 0 for x in possible_successions}
        for trace in traces:
            if include_start_end:
                # add start and end token
                trace = ["^", *trace, "$"]

            # create set of successions to avoid double counting
            successions = set(zip(trace[:-1], trace[1:]))
            for succession in successions:
                succession_counter[succession] += 1

        valid_successions = {x: succession_counter[x] for x in succession_counter if succession_counter[x] > min_amount}

        invalid_successions = [x for x in possible_successions if x not in valid_successions]

        drop_traces = []

        for i, trace in enumerate(return_traces):
            if include_start_end:
                # add start and end token
                trace = ["^", *trace, "$"]
            if any(x in zip(trace[:-1], trace[1:]) for x in invalid_successions):
                drop_traces.append(i)

        for drop_index in sorted(drop_traces, reverse=True):
            del return_traces[drop_index]

    print("traces after filtering: ", len(return_traces))
    return return_traces

