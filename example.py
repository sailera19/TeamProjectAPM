import pandas as pd
from collections import defaultdict
from alpha_algorithm import run_alpha_algorithm

# aalst traces
#traces = [
#    ["a", "b", "c", "d"],
#    ["a", "c", "b", "d"],
#    ["a", "e", "d"]
#]

# rehse traces
traces = [
    ["a", "c", "d", "e"],
    ["b", "c", "d", "e"],
    ["a", "c", "e", "d"],
    ["b", "c", "e", "d"],
    ["a", "c", "d", "a", "d"]
]

net = run_alpha_algorithm(traces)

net.show()