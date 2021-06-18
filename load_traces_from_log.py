import pandas as pd
from collections import defaultdict


def load_file(filepath):
    event_log = pd.read_csv(filepath, sep=";")
    event_log = event_log.sort_values(by=["start"])
    return get_traces(event_log)


def get_traces(event_log, replace_activities=True):
    traces = defaultdict(list)
    activity_map = {}
    idx = 0
    for (_, activity, case, _, _, _, _) in event_log.itertuples():
        if replace_activities:
            activity_symbol = activity_map.get(activity)
            if not activity_symbol:
                idx += 1
                activity_symbol = chr(64 + idx)
                activity_map[activity] = activity_symbol
            activity = activity_symbol
        traces[case].append(activity)
    inverted_activity_map = {value: key for key, value in activity_map.items()}
    return list(traces.values()), inverted_activity_map
