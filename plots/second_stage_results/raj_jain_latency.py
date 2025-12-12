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

y_GEPAR_latency = []
y_optimal_latency = []
y_unconstrained_latency = []
y_single_path_latency = []

y_agent_latency = []

for timestamp in range(100):
    json_obj = json.load(open("../../solutions/second_stage/unconstrained_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    y_unconstrained.append(json_obj["solution"]["migration_cost"])

    json_obj = json.load(open("../../solutions/second_stage/single_path_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    y_single_path.append(json_obj["solution"]["migration_cost"])

    json_obj = json.load(open("../../solutions/second_stage/heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    y_GEPAR.append(json_obj["solution"]["migration_cost"])

    json_obj = json.load(open("../../solutions/second_stage/agent/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    y_agent.append(json_obj["solution"]["migration_cost"])

    json_obj = json.load(open("../../solutions/second_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    y_optimal.append(json_obj["solution"]["migration_cost"])
    
    json_obj = json.load(open("../../solutions/second_stage/unconstrained_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(json_obj["solution"]["users"][user]["max_latency"] * 1000)
    y_unconstrained_latency.append(sum(values)/len(values))

    json_obj = json.load(open("../../solutions/second_stage/single_path_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(json_obj["solution"]["users"][user]["max_latency"] * 1000)
    y_single_path_latency.append(sum(values)/len(values))

    json_obj = json.load(open("../../solutions/second_stage/heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(json_obj["solution"]["users"][user]["max_latency"] * 1000)
    y_GEPAR_latency.append(sum(values)/len(values))

    json_obj = json.load(open("../../solutions/second_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(json_obj["solution"]["users"][user]["max_latency"] * 1000)
    y_optimal_latency.append(sum(values)/len(values))

    json_obj = json.load(open("../../solutions/second_stage/agent/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(json_obj["solution"]["users"][user]["max_latency"] * 1000)
    y_agent_latency.append(sum(values)/len(values))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 5), sharex=True, gridspec_kw={'height_ratios': [1, 1]})

# Top plot: Migration cost
ax1.plot(y_unconstrained, label='Unconstrained', linestyle='-', color="tab:orange", linewidth=1.5)
ax1.plot(y_single_path, label='Single Path', linestyle='-', color="royalblue", linewidth=1.5)
ax1.plot(y_GEPAR, label='GEPAR', color="forestgreen", linestyle='-', linewidth=1.5)
ax1.plot(y_agent, label='MARL Agent', color="purple", linestyle='-', linewidth=1.5)

ax1.set_ylabel('Migration Cost (log)', fontsize=fontsize)
ax1.grid(linestyle='--', linewidth=1)
ax1.set_xlim(0, 100)
ax1.set_yscale('log')
# ax1.set_yticks([0, 20, 40, 60, 80, 100, 120, 140])
ax1.tick_params(axis='y', labelsize=fontsize)
ax1.legend(fontsize=fontsize-2.8, loc="upper left", bbox_to_anchor=(-0.01, 1.2), ncol=4)

# Bottom plot: Average Latency
ax2.plot(y_unconstrained_latency, label='Unconstrained', linestyle='-', color="tab:orange", linewidth=1.5)
ax2.plot(y_single_path_latency, label='Single Path', linestyle='-', color="royalblue", linewidth=1.5)
ax2.plot(y_GEPAR_latency, label='GEPAR', color="forestgreen", linestyle='-', linewidth=1.5)
ax2.plot(y_agent_latency, label='MARL Agent', color="purple", linestyle='-', linewidth=1.5)

ax2.axhline(y=1000, color='red', linestyle='--', linewidth=1.5)
ax2.set_xlabel('Timestamp (#)', fontsize=fontsize)
ax2.set_ylabel('Avg Latency (ms)', fontsize=fontsize)
ax2.grid(linestyle='--', linewidth=1)
ax2.set_xlim(0, 100)
ax2.set_ylim(940, 1002)
ax2.set_yticks([940, 950, 960, 970, 980, 990, 1000])
ax2.set_xticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

plt.xticks(fontsize=fontsize)
plt.yticks(fontsize=fontsize)
plt.tight_layout()

plt.annotate(
    'Max. latency threshold',
    xy=(60, 1000), xycoords='data',
    xytext=(75, 990), textcoords='data',
    arrowprops=dict(arrowstyle="->", color='black', lw=2),
    fontsize=fontsize-1,
    color='black',
    ha='center',
    va='bottom'
)

# plt.yscale("log")

# plt.plot(y_GEPAR_total, label='GEPAR Total Cost', linestyle='--')
# plt.plot(y_optimal_total, label='Optimal Total Cost', linestyle='--')

plt.xlabel('Timestamp (#)', fontsize=fontsize)
plt.ylabel('Average Latency (ms)', fontsize=fontsize)
# plt.legend(fontsize=fontsize, loc="upper left", bbox_to_anchor=(0.046, 1.26), ncol=3)
plt.grid(linestyle='--', linewidth=1)
plt.xlim(0, 100)
plt.ylim(940, 1002)
plt.yticks(fontsize=fontsize)
plt.xticks(fontsize=fontsize)
plt.yticks([940, 950, 960, 970, 980, 990, 1000], fontsize=fontsize)
plt.tight_layout()
plt.savefig('latency_evaluation.pdf')
# # plt.show()