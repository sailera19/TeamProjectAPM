import pandas as pd
from collections import defaultdict
from alpha_algorithm import run_alpha_algorithm
from alpha_plus_algorithm import run_alpha_plus_algorithm
from load_traces_from_log import load_file
import os
os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

# aalst traces
traces = [
    ["a", "b", "c", "d"],
    ["a", "c", "b", "d"],
    ["a", "e", "d"]
]

# rehse traces
traces1 = [
    ["a", "c", "d", "e"],
    ["b", "c", "d", "e"],
    ["a", "c", "e", "d"],
    ["b", "c", "e", "d"],
    ["a", "c", "d", "a", "d"]
]

traces2 = [
    ["a", "a","a", "c", "a", "a", "c", "d", "e", "e", "e"],
    ["b", "c", "e", "d"],
    ["a", "c", "e", "e", "e", "d"],
    ["b", "c", "c", "e", "d"],
    ["a", "c", "a", "d"],
    ["a", "j", "j", "d"]
]

traces3 = [
    ["a", "b", "a", "e", "e", "c"]
]

traces4 = load_file("data/Data_Set.csv")

net = run_alpha_algorithm(traces4)

net.show()
