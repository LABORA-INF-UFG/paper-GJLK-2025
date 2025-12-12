import matplotlib.pyplot as plt
import sys
import json
import numpy as np

fontsize = 12
linewidth = 1.5

n_CNs = 10
n_gNBs = 10

x = [400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]

y_optimal_cost = []
y_unconstrained_cost = []
y_single_path_cost = []
y_GEPAR_cost = []
y_agent_cost = []

y_optimal_time = []
y_unconstrained_time = []
y_single_path_time = []
y_GEPAR_time = []
y_agent_time = []

for n_users in x:
    for timestamp in range(0, 1):
        tmp_time = []
        tmp_cost = []
        json_optimal = json.load(open("../../solutions/second_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
        tmp_time.append(json_optimal["solution"]["time"] * 1000)
        tmp_cost.append(json_optimal["solution"]["Total_Cost"])
    y_optimal_time.append(np.mean(tmp_time))
    y_optimal_cost.append(np.mean(tmp_cost))

    for timestamp in range(0, 1):
        tmp_time = []
        tmp_cost = []
        json_unconstrained = json.load(open("../../solutions/second_stage/unconstrained_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
        tmp_time.append(json_unconstrained["solution"]["time"] * 1000)
        tmp_cost.append(json_unconstrained["solution"]["Total_Cost"])
    y_unconstrained_time.append(np.mean(tmp_time))
    y_unconstrained_cost.append(np.mean(tmp_cost))

    for timestamp in range(0, 1):
        tmp_time = []
        tmp_cost = []
        json_single_path = json.load(open("../../solutions/second_stage/single_path_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
        tmp_time.append(json_single_path["solution"]["time"] * 1000)
        tmp_cost.append(json_single_path["solution"]["Total_Cost"])
    y_single_path_time.append(np.mean(tmp_time))
    y_single_path_cost.append(np.mean(tmp_cost))

    for timestamp in range(0, 1):
        tmp_time = []
        tmp_cost = []
        json_GEPAR = json.load(open("../../solutions/second_stage/heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
        tmp_time.append(json_GEPAR["solution"]["time"] * 1000)
        tmp_cost.append(json_GEPAR["solution"]["Total_Cost"])
    y_GEPAR_time.append(np.mean(tmp_time))
    y_GEPAR_cost.append(np.mean(tmp_cost))

    for timestamp in range(0, 30):
        tmp_time = []
        tmp_cost = []
        json_agent = json.load(open("../../solutions/second_stage/agent/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
        tmp_time.append(json_agent["solution"]["time"] * 1000)
        tmp_cost.append(json_agent["solution"]["Total_Cost"])
    y_agent_time.append(np.mean(tmp_time))
    y_agent_cost.append(np.mean(tmp_cost))
    
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(7, 5))

# Plot cost on the first axis

ax1.plot(x, y_unconstrained_cost, label='Unconstrained', linewidth=linewidth, color="tab:orange", marker="v", linestyle="--")
ax1.plot(x, y_single_path_cost, label='Single Path', linewidth=linewidth, color="royalblue", marker="s", linestyle="--")
ax1.plot(x, y_GEPAR_cost, label='GEPAR', linewidth=linewidth, color="forestgreen", marker="o", linestyle="--")
ax1.plot(x, y_optimal_cost, label='Optimal', linewidth=linewidth, color="red", marker="^", linestyle="--")
ax1.plot(x, y_agent_cost, label='Agent', linewidth=linewidth, color="purple", marker="*", linestyle="--")
ax1.set_ylabel('Cost ($/sec)', fontsize=fontsize)
ax1.legend(fontsize=fontsize-1, ncol=4, loc='upper center', bbox_to_anchor=(0.5, 1.25))
ax1.grid(True, linestyle='--')
ax1.set_yticks([0, 1, 2, 3, 4, 5, 6, 7, 8])
ax1.tick_params(axis='y', labelsize=fontsize)
# ax1.set_yscale('log')

# Plot time on the second axis
ax2.plot(x, y_unconstrained_time, label='Unconstrained', linewidth=linewidth, color="tab:orange", marker="v", linestyle="--")
ax2.plot(x, y_single_path_time, label='Single Path', linewidth=linewidth, color="royalblue", marker="s", linestyle="--")
ax2.plot(x, y_GEPAR_time, label='GEPAR', linewidth=linewidth, color="forestgreen", marker="o", linestyle="--")
ax2.plot(x, y_optimal_time, label='Optimal', linewidth=linewidth, color="red", marker="^", linestyle="--")
ax2.plot(x, y_agent_time, label='Agent', linewidth=linewidth, color="purple", marker="*", linestyle="--")
ax2.set_xlabel('Users (#)', fontsize=fontsize-1)
ax2.set_ylabel('Time (ms)', fontsize=fontsize)
# ax2.legend(fontsize=fontsize, ncol=2)
ax2.set_yscale('log')
ax2.tick_params(axis='y', labelsize=fontsize)
ax2.tick_params(axis='x', labelsize=fontsize - 3)
ax2.set_yticks([1, 10, 100, 1000, 10000, 100000, 1000000, 10000000])
ax2.set_xticks([400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000])
ax2.grid(True, linestyle='--')

plt.tight_layout()
plt.savefig("Comparing_total_cost_and_time.pdf")
# plt.show()