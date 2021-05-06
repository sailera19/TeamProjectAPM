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
    ["a", "a", "a", "c", "a", "a", "c", "d", "e", "e", "e", "e", "d"],
    ["b", "c", "e", "d"],
    ["a", "c", "e", "e", "e", "d"],
    ["b", "c", "c", "e", "d"],
    ["a", "c", "a", "d"],
    ["a", "j", "j", "d"]
]

traces3 = [
    ["a", "b", "a", "e", "e", "c"]
]

traces5 = [["a", "c", "i", "i", "i", "i", "i", "f", "h", "b", "g"]]



traces4 = load_file("data/Data_Set.csv")

data = pd.read_excel("Traces_Example.xlsx")


def dataprep(data):
    traces_all = []
    for index, Traces in data.iterrows():
        a = []
        sp = []
        a.append(data["Traces"].values[index])
        sp = a[0].split(',')
        traces_all.append(sp)
    return (traces_all)


traces_all = dataprep(data)

net = run_alpha_plus_algorithm(traces_all)

net.show()
