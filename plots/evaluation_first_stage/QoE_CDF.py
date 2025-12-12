import json
import numpy as np
import matplotlib.pyplot as plt

marker_size = 5
line_width = 2
font_size = 14

n_CNs = 10
n_gNBs = 10
n_users = 1200

x = [i for i in range(0, 100)]

y_optimal = []
y_traditional = []
y_QoE_aware = []
y_single_association = []
y_dual_connectivity = []

for timestamp in x:
    # json_optimal = json.load(open("../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    # json_optimal = json_optimal["solution"]
    # y_optimal.append(json_optimal["Total_QoE"])
    
    # json_traditional = json.load(open("../solutions/first_stage/traditional_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    # json_traditional = json_traditional["solution"]
    # y_traditional.append(json_traditional["Total_QoE"])
    
    json_QoE_aware = json.load(open("../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    json_QoE_aware = json_QoE_aware["solution"]
    y_QoE_aware.append(json_QoE_aware["Total_QoE"])

    json_single_association = json.load(open("../solutions/first_stage/single_association_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    json_single_association = json_single_association["solution"]
    y_single_association.append(json_single_association["Total_QoE"])

    json_dual_connectivity = json.load(open("../solutions/first_stage/dual_connectivity_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    json_dual_connectivity = json_dual_connectivity["solution"]
    y_dual_connectivity.append(json_dual_connectivity["Total_QoE"])

plt.figure(figsize=(5, 3))

def plot_cdf(data, label, color):
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data)+1) / len(sorted_data)
    plt.plot(sorted_data, cdf, marker=None, linestyle='-', markersize=marker_size, linewidth=line_width, color=color, label=label)

plot_cdf(y_single_association[10:], 'SA', 'royalblue')
plot_cdf(y_dual_connectivity[10:], 'DC', 'darkorange')
plot_cdf(y_QoE_aware[10:], 'VEXA', 'forestgreen')

plt.legend(loc='upper center', bbox_to_anchor=(0.53, 1.3), fontsize=font_size, ncol=3)

plt.xlabel('Total QoE (#)', fontsize=font_size)
plt.ylabel('CDF', fontsize=font_size)
plt.xticks(fontsize=font_size)
plt.yticks(fontsize=font_size)
plt.xlim(0, 1000)
plt.ylim(0, 1.1)
plt.grid(True, linestyle='--')
plt.tight_layout()
plt.savefig('CDF_QoE_compare_heuristics.pdf')