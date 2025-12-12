import json
import matplotlib.pyplot as plt
import numpy as np

fontsize = 13

n_CNs = 10
n_gNBs = 10
n_users = 250

y_GEPAR = []
y_optimal = []
y_unconstrained = []
y_single_path = []
y_agent = []

for timestamp in range(100):
    json_obj = json.load(open("../../solutions/second_stage/unconstrained_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    y_unconstrained.append(json_obj["solution"]["migration_cost"])

    json_obj = json.load(open("../../solutions/second_stage/single_path_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    y_single_path.append(json_obj["solution"]["migration_cost"])

    # if timestamp in [0, 1]:
    #     y_GEPAR.append(0)
    #     y_optimal.append(0)
    # else:
    json_obj = json.load(open("../../solutions/second_stage/heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    y_GEPAR.append(json_obj["solution"]["migration_cost"])

    json_obj = json.load(open("../../solutions/second_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    y_optimal.append(json_obj["solution"]["migration_cost"])

plt.figure(figsize=(7, 3))
plt.plot(y_unconstrained, label='Unconstrained', linestyle='-', color="tab:orange", linewidth=2)
plt.plot(y_single_path, label='Single Path', linestyle='-', color="royalblue", linewidth=2)
plt.plot(y_GEPAR, label='GEPAR', color="forestgreen", linestyle='-', linewidth=2)

plt.yscale("log")

# plt.plot(y_GEPAR_total, label='GEPAR Total Cost', linestyle='--')
# plt.plot(y_optimal_total, label='Optimal Total Cost', linestyle='--')

plt.xlabel('Timestamp (#)', fontsize=fontsize)
plt.ylabel('Migration Cost (#)', fontsize=fontsize)
plt.legend(fontsize=fontsize, loc="upper left", bbox_to_anchor=(0.058, 1.26), ncol=3)
plt.grid(linestyle='--', linewidth=1)
plt.xlim(0, 101)
plt.ylim(0, 10**3)
plt.yticks(fontsize=fontsize)
plt.xticks(fontsize=fontsize)
# plt.yticks([0, 10, 20, 30, 40, 50], fontsize=fontsize)
plt.tight_layout()
plt.savefig('migration_cost_plot.pdf')
# plt.show()