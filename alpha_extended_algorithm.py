import pandas as pd
from collections import defaultdict, namedtuple, Counter
from pm4py.objects.petri.obj import PetriNet, Marking
from pm4py.objects.petri import utils
from pm4py.visualization.petri_net import visualizer as pn_visualizer
import copy


def run_alpha_plus_algorithm(traces, min_support=None, include_start_end=True, per_node=False,
                             filter_full_trace=True, detect_loops=False, activity_map=None):
    traces = filter_traces(traces, min_support=min_support, per_node=per_node,
                           include_start_end=include_start_end, filter_full_trace=filter_full_trace)

    if detect_loops:
        # Preprocessing phase, extracting the length 1 loops
        preprocess = True
        all_activities, start_activities, end_activities, direct_successions, length_two_loop, activities_with_loops = get_activities(traces, preprocess)
        footprint = FootPrintMatrix(activities_with_loops, direct_successions, length_two_loop)
        all_pairs = footprint.find_pairs()
        maximal_pairs = remove_non_maximal_pairs(all_pairs)
        loop_one_start, loop_one_end = filter_loop_one(maximal_pairs)
        remove_one_loops(traces)

        # Run Alpha Algorithm without length 1 loops
        preprocess = False
        tmp, tmp1, tmp2, direct_successions, length_two_loop, tmp3 = get_activities(traces, preprocess)
        footprint = FootPrintMatrix(tmp, direct_successions, length_two_loop)
        all_pairs = footprint.find_pairs()
        maximal_pairs = remove_non_maximal_pairs(all_pairs)

        # Add back length 1 loops
        net = AlphaPetriNet(start_activities=start_activities, end_activities=end_activities,
                            all_activities=all_activities, maximal_pairs=maximal_pairs, loop_one_start=loop_one_start,
                            loop_one_end=loop_one_end, activity_map=activity_map)
    else:
        all_activities, start_activities, end_activities, direct_successions, _, _ = get_activities(traces)

        footprint = FootPrintMatrix(all_activities, direct_successions)
        all_pairs = footprint.find_pairs()
        maximal_pairs = remove_non_maximal_pairs(all_pairs)
        net = AlphaPetriNet(start_activities=start_activities, end_activities=end_activities,
                            all_activities=all_activities, maximal_pairs=maximal_pairs, activity_map=activity_map)
    return net


def get_activities(traces, preprocess=False):
    """
    Get activity informations from traces.
    Returns set for all_activities, start_activities, end_activities and dict for direct_successions
    """
    start_activities = set()
    activities_with_loops = set()
    end_activities = set()
    all_activities = set()

    direct_successions = defaultdict(set)
    length_two_loop = defaultdict(set)

    # go through all our traces
    for trace in traces:
        # add start and end activities
        start_activities.add(trace[0])
        end_activities.add(trace[-1])

        # add activities of trace to all activities
        all_activities.update(trace)
        if preprocess:
            # remove duplicates at beginning and end
            remove_duplicates_beginning_and_end(trace)
            # remove triples
            remove_triples(trace)
            # detect length 1 loops
            tmp = trace.copy()
            pop = []
            for idx, activity in enumerate(tmp[1:], start=1):
                if activity == '*':
                    continue
                if tmp[idx-1] == tmp[idx] and tmp[idx] not in start_activities and tmp[idx] not in end_activities:
                    trace[idx] = "#" + trace[idx]
                    pop.append(idx-1)
            for j in pop[::-1]:
                del trace[j]

        # go through all activities in our trace and add succession
        for predecessor, successor in zip(trace[:-1], trace[1:]):
            if not (successor == '*' or predecessor == '*'):
                direct_successions[predecessor].add(successor)

        # detect length 2 loops
        for idx, activity in enumerate(trace[2:], start=2):
            if activity == '*' or trace[idx - 1] == '*':
                continue
            if trace[idx - 2] == activity and trace[idx - 1] != activity:
                length_two_loop[trace[idx - 2]].add(trace[idx - 1])
                #TODO check if right
                length_two_loop[trace[idx - 1]].add(trace[idx - 2])

        # add loops to activities
        activities_with_loops.update(trace)
    Activities = namedtuple("Activities", ["all_activities", "start_activities", "end_activities", "direct_successions",
                                           "length_two_loop", "activities_with_loops"])

    # remove the placeholder char from activities if they are present
    start_activities.discard('*')
    end_activities.discard('*')
    all_activities.discard('*')
    activities_with_loops.discard('*')

    # an activity might no longer be reachable, if other nodes got removed
    # check if succession is reachable
    reachable_activities = []
    reachable_activities.extend(start_activities)
    idx = 0
    while idx < len(reachable_activities):
        activity = reachable_activities[idx]
        successions = direct_successions[activity]
        for succession in successions:
            if succession not in reachable_activities:
                reachable_activities.append(succession)
        idx += 1
    # some activities might no longer reach an end activity
    # check for the reachable activities if they do lead to an end activity
    valid_activities = []
    for activity in reachable_activities:
        if activity in end_activities:
            valid_activities.append(activity)
            continue
        successions = list(direct_successions[activity])
        idx = 0

        # find all the following activities
        while idx < len(successions):
            for succession in direct_successions[successions[idx]]:
                if succession not in successions:
                    successions.append(succession)
            idx += 1

        # check if one of the following is an end activity -> valid
        for successor in successions:
            if successor in end_activities:
                valid_activities.append(activity)
                continue

    invalid_activities = all_activities - set(valid_activities)
    start_activities = start_activities - invalid_activities
    end_activities = end_activities - invalid_activities
    all_activities = all_activities - invalid_activities
    activities_with_loops = activities_with_loops - invalid_activities
    for k in list(direct_successions.keys()):
        if k in invalid_activities:
            direct_successions.pop(k)

    return Activities(all_activities, start_activities, end_activities, direct_successions, length_two_loop,
                      activities_with_loops)


def remove_triples(trace):
    tmp = trace.copy()
    pop = []
    for i, act in enumerate(tmp[2:], start=2):
        if len(tmp)>2 and (tmp[i]==tmp[i-1]==tmp[i-2]):
            pop.append(i-2)
    pop = pop[::-1]
    for j in pop:
        del trace[j]


def remove_duplicates_beginning_and_end(trace):
    if len(trace) == 1:
        return trace
    elif trace[0] == trace[1]:
        trace.pop(0)
        remove_duplicates_beginning_and_end(trace)
    elif trace[len(trace)-1] == trace[len(trace)-2]:
        trace.pop()
        remove_duplicates_beginning_and_end(trace)
    else:
        return trace


def filter_loop_one(max_pairs):
    loop_one_start = defaultdict(set)
    loop_one_end = defaultdict(set)
    # Add Input and Output Arcs for all our Pairs
    for idx, pair in enumerate(max_pairs, start=1):
        for a in pair[0]:
            if a.startswith("#"):
                for b in pair[1]:
                    loop_one_end[b].add(a[1:])
        for b in pair[1]:
            if b.startswith("#"):
                for a in pair[0]:
                    loop_one_start[a].add(b[1:])
    return loop_one_start, loop_one_end


def remove_one_loops(traces):
    for trace in traces:
        # go through all activities in our trace and
        for idx, activity in enumerate(trace[1:], start=1):
            if activity.startswith("#"):
                trace.remove(activity)


class FootPrintMatrix:
    footprint_df: pd.DataFrame = None

    def __init__(self, all_activities, direct_successions, length_two_loop=defaultdict(set)):
        all_activities = sorted(list(all_activities))
        footprint = []
        for x in all_activities:
            row = []
            for y in all_activities:
                x_follows_y = x in direct_successions[y]
                y_follows_x = y in direct_successions[x]
                x_loop_y = y in length_two_loop[x]

                if y_follows_x and (not x_follows_y or x_loop_y):
                    row.append("→")
                elif x_follows_y and not y_follows_x:
                    row.append("←")
                elif x_follows_y and y_follows_x and not x_loop_y:
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

    def __init__(self, start_activities, end_activities, all_activities, maximal_pairs, loop_one_start=defaultdict(set),
                 loop_one_end=defaultdict(set), activity_map=None):
        self.net = PetriNet("Petri Net")

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

        # Re-add the loop activities to all activities
        for activities in loop_one_start.values():
            all_activities.update(activities)
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
                if a in loop_one_start:
                    for idx in loop_one_start[a]:
                        utils.add_arc_from_to(transition_map[idx], place, self.net)
            for b in pair[1]:
                utils.add_arc_from_to(place, transition_map[b], self.net)
                if b in loop_one_end:
                    for idx in loop_one_end[b]:
                        utils.add_arc_from_to(place, transition_map[idx], self.net)

    def show(self):
        gviz = pn_visualizer.apply(self.net, self.initial_marking, self.final_marking, {'format': 'png'})
        pn_visualizer.view(gviz)

    def save(self, filename):
        gviz = pn_visualizer.apply(self.net, self.initial_marking, self.final_marking, {'format': 'png'})
        pn_visualizer.save(gviz, filename)


def filter_traces(traces, min_support=None, include_start_end=True, per_node=False, filter_full_trace=True):
    print("Traces at the start: ", len(traces))

    if not min_support:
        return traces

    return_traces = copy.deepcopy(traces)
    n_traces = len(return_traces)
    all_activities = set([activity for trace in traces for activity in trace])

    if include_start_end:
        # add start token
        all_activities.add("^")
        # add end token
        all_activities.add("$")

    invalid_successions = []
    if per_node:
        # per_node is similar to the inductive miner infrequent approach
        # we remove the trace if a succession appears
        # less than min_support of all possible successions for an activity/node
        successions_per_node = defaultdict(Counter)
        for trace in traces:
            if include_start_end:
                # add start and end token
                trace = ["^", *trace, "$"]

            # create set of successions to avoid double counting
            successions = set(zip(trace[:-1], trace[1:]))
            for node, successor in successions:
                successions_per_node[node][successor] += 1

        for node, successors in successions_per_node.items():
            max_successions = max(successors.values())
            min_amount = round(min_support * max_successions)
            for successor, count in successors.items():
                if count < min_amount:
                    invalid_successions.append((node, successor))
    else:
        min_amount = round(min_support * n_traces)
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

        valid_successions = {x: succession_counter[x] for x in succession_counter if succession_counter[x] >= min_amount}

        invalid_successions = [x for x in possible_successions if x not in valid_successions]

    if filter_full_trace:
        # drop the traces that contain infrequent successions
        drop_traces = []

        for i, trace in enumerate(return_traces):
            if include_start_end:
                # add start and end token
                trace = ["^", *trace, "$"]
            if any(x in zip(trace[:-1], trace[1:]) for x in invalid_successions):
                drop_traces.append(i)

        for drop_index in sorted(drop_traces, reverse=True):
            del return_traces[drop_index]
        print("Traces after filtering: ", len(return_traces))
    else:
        # replace infrequent successors with placeholders
        # placeholder successions will be ignored by the alpha algorithm later on
        for i, trace in enumerate(return_traces):
            trace = ["^", *trace, "$"]
            for j, [activity, successor] in enumerate(zip(trace[:-1], trace[1:])):
                if (activity, successor) in invalid_successions:
                    if successor == '$':
                        return_traces[i].append('*')
                    else:
                        return_traces[i][j] = '*'  # placeholder char
    return return_traces
