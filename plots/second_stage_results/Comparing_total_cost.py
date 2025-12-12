import matplotlib.pyplot as plt
import sys
import json
import numpy as np

fontsize = 16
linewidth = 2

n_CNs = 10
n_gNBs = 10

x = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400]

y_optimal = []
y_unconstrained = []
y_single_path = []
y_GEPAR = []

for n_users in x:
    json_optimal = json.load(open("../../solutions/second_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_0.json".format(n_CNs, n_gNBs, n_users)))
    y_optimal.append(json_optimal["solution"]["Total_Cost"])

    json_unconstrained = json.load(open("../../solutions/second_stage/unconstrained_model/{}_CNs_{}_gNBs_{}_users_timestamp_0.json".format(n_CNs, n_gNBs, n_users)))
    y_unconstrained.append(json_unconstrained["solution"]["Total_Cost"])

    json_single_path = json.load(open("../../solutions/second_stage/single_path_model/{}_CNs_{}_gNBs_{}_users_timestamp_0.json".format(n_CNs, n_gNBs, n_users)))
    y_single_path.append(json_single_path["solution"]["Total_Cost"])

    json_GEPAR = json.load(open("../../solutions/second_stage/heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_0.json".format(n_CNs, n_gNBs, n_users)))
    y_GEPAR.append(json_GEPAR["solution"]["Total_Cost"])
    
plt.figure(figsize=(7, 3))
bar_width = 2.5  # width of each bar
x_indices = np.arange(len(x))

plt.plot(x_indices, y_optimal, marker='o', label="Optimal", color="blue", linewidth=linewidth)
plt.plot(x_indices, y_single_path, marker='s', label="Single Path", color="orange", linewidth=linewidth)
plt.plot(x_indices, y_unconstrained, marker='^', label="Unconstrained", color="firebrick", linewidth=linewidth)
plt.plot(x_indices, y_GEPAR, marker='d', label="GEPAR", color="green", linewidth=linewidth)

plt.xticks(x_indices, x, fontsize=fontsize-2)
plt.yscale("log")

plt.legend(fontsize=fontsize-3, ncol=2)

#plt.yscale("log")
plt.xlabel("Users (#)", fontsize=fontsize)
plt.ylabel("Total cost (#)", fontsize=fontsize)
# plt.xlim(0, 100)
# plt.ylim(0, 1600)
# plt.legend()
# plt.yticks([0, 1, 2, 3], fontsize=fontsize)
# plt.xticks([10, 100, 200, 300, 400], fontsize=fontsize-2)
plt.grid(True, linestyle='--', linewidth=1)

# plt.legend(loc='upper center', bbox_to_anchor=(0.617, 1.2), fontsize=fontsize, ncols=3)

plt.tight_layout()
plt.savefig("Comparing_total_cost.pdf")
# plt.show()