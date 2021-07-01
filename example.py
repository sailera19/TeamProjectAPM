from alpha_extended_algorithm import run_alpha_extended_algorithm
from data_loader import load_from_traces, load_from_log
import os

os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

# aalst traces
traces_aalst = [
    ["a", "b", "c", "d"],
    ["a", "c", "b", "d"],
    ["a", "e", "d"]
]
net_aalst = run_alpha_extended_algorithm(traces_aalst)
net_aalst.save('nets/aalst.png')

# rehse traces
traces_rehse = [
    ["a", "c", "d", "e"],
    ["b", "c", "d", "e"],
    ["a", "c", "e", "d"],
    ["b", "c", "e", "d"],
    ["a", "c", "d", "a", "d"]
]
net_rehse = run_alpha_extended_algorithm(traces_rehse)
net_rehse.save('nets/rehse.png')

# manually created toy data set
traces_toyset = load_from_traces("data/Traces_Example.xlsx")
net_toyset = run_alpha_extended_algorithm(traces_toyset, min_support=0.5, include_start_end=True, per_node=True, filter_full_trace=False)
net_toyset.save('nets/toyset.png')

# real life event log from travel data
traces_filtered_dataset, activity_map_filtered_dataset = load_from_log("data/Travel_Data_final.csv")

# Infrequent per node (Happy Path), filter nodes only
net_n_n = run_alpha_extended_algorithm(traces_filtered_dataset, min_support=0.9, include_start_end=True, per_node=True,
                                       filter_full_trace=False, activity_map=activity_map_filtered_dataset, detect_loops=True)
net_n_n.save('nets/happypath_infrequent_per_node__filter_nodes_only.png')
                               
# Infrequent per node (Happy Path), filter full traces
net_n_t = run_alpha_extended_algorithm(traces_filtered_dataset, min_support=0.9, include_start_end=True, per_node=True,
                                       filter_full_trace=True, activity_map=activity_map_filtered_dataset, detect_loops=True)
net_n_t.save('nets/happypath_infrequent_per_node__filter_full_traces.png')
                               
# Infrequent global (Happy Path), filter nodes only
net_g_n = run_alpha_extended_algorithm(traces_filtered_dataset, min_support=0.45, include_start_end=True, per_node=False,
                                       filter_full_trace=False, activity_map=activity_map_filtered_dataset, detect_loops=True)
net_g_n.save('nets/happypath_infrequent_global__filter_nodes_only.png')
                               
# Infrequent global (Happy Path), filter full traces
net_g_t = run_alpha_extended_algorithm(traces_filtered_dataset, min_support=0.45, include_start_end=True, per_node=False,
                                       filter_full_trace=True, activity_map=activity_map_filtered_dataset, detect_loops=True)
net_g_t.save('nets/happypath_infrequent_global__filter_full_traces.png')

# Infrequent per node (most_common), filter nodes only
net_n_n_t2 = run_alpha_extended_algorithm(traces_filtered_dataset, min_support=0.2, include_start_end=True, per_node=True,
                                          filter_full_trace=False, activity_map=activity_map_filtered_dataset, detect_loops=True)
net_n_n_t2.save('nets/threshold_0.2_infrequent_per_node__filter_nodes_only.png')

# Infrequent per node (most_common), filter full trace
net_n_t_t2 = run_alpha_extended_algorithm(traces_filtered_dataset, min_support=0.2, include_start_end=True, per_node=True,
                                          filter_full_trace=True, activity_map=activity_map_filtered_dataset, detect_loops=True)
net_n_t_t2.save('nets/threshold_0.2_infrequent_per_node__filter_full_trace.png')

# Infrequent global (most_common), filter nodes only
net_g_n_t1 = run_alpha_extended_algorithm(traces_filtered_dataset, min_support=0.1, include_start_end=True, per_node=False,
                                          filter_full_trace=False, activity_map=activity_map_filtered_dataset, detect_loops=True)
net_g_n_t1.save('nets/threshold_0.1_infrequent_global__filter_nodes_only.png')

# Infrequent global (most_common), filter full trace
net_g_t_t1 = run_alpha_extended_algorithm(traces_filtered_dataset, min_support=0.1, include_start_end=True, per_node=False,
                                          filter_full_trace=True, activity_map=activity_map_filtered_dataset, detect_loops=True)
net_g_t_t1.save('nets/threshold_0.1_infrequent_global__filter_full_trace.png')

# No filtering
net_all = run_alpha_extended_algorithm(traces_filtered_dataset, min_support=None, activity_map=activity_map_filtered_dataset, detect_loops=True)
net_all.save('nets/no_filtering.png')
