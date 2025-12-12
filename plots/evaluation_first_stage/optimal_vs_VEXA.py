import json
import matplotlib.pyplot as plt

marker_size = 6
line_width = 2
font_size = 14

n_CNs = 10
n_gNBs = 10
n_users = 250

x = [i for i in range(0, 100)]

y_optimal = []
y_traditional = []
y_QoE_aware = []
y_single_association = []
y_dual_connectivity = []

for timestamp in x:
    json_optimal = json.load(open("../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    json_optimal = json_optimal["solution"]
    y_optimal.append(json_optimal["Total_QoE"])
    
    # json_traditional = json.load(open("../solutions/first_stage/traditional_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    # json_traditional = json_traditional["solution"]
    # y_traditional.append(json_traditional["Total_QoE"])
    
    json_QoE_aware = json.load(open("../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    json_QoE_aware = json_QoE_aware["solution"]
    y_QoE_aware.append(json_QoE_aware["Total_QoE"])

    # json_single_association = json.load(open("../solutions/first_stage/single_association_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    # json_single_association = json_single_association["solution"]
    # y_single_association.append(json_single_association["Total_QoE"])

    # json_dual_connectivity = json.load(open("../solutions/first_stage/dual_connectivity_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp)))
    # json_dual_connectivity = json_dual_connectivity["solution"]
    # y_dual_connectivity.append(json_dual_connectivity["Total_QoE"])

plt.figure(figsize=(8, 3))
plt.plot(x, y_optimal, marker='^', linestyle='-', markersize=marker_size, linewidth=line_width, color='red', label='Optimal')
plt.plot(x, y_QoE_aware, marker='o', linestyle='-', markersize=marker_size-1, linewidth=line_width, color='forestgreen', label='VEXA') # VR EXperience-aware Algorithm

plt.annotate(
    'Optimality\ngap 10%',
    xy=(34, 176), xycoords='data',
    xytext=(45, 188), textcoords='data',
    arrowprops=dict(arrowstyle="->", color='black', lw=2),
    fontsize=font_size-1,
    color='black',
    ha='center',
    va='bottom'
)

plt.errorbar(34, 183.5, yerr=[[17.3], [0]], fmt='none', ecolor='black', elinewidth=2, capsize=5)

gap = 0
gap_timestep = 0
gap_list = []
for i in range(0, len(y_optimal)):
    gap_list.append(1 - y_QoE_aware[i]/y_optimal[i])
    if 1 - y_QoE_aware[i]/y_optimal[i] > gap:
        gap = 1 - y_QoE_aware[i]/y_optimal[i]
        gap_timestep = i

print("Gap at timestep {}: {}".format(gap_timestep, gap))
print("Average gap: {}".format(sum(gap_list)/len(gap_list)))

plt.legend(loc='upper right', fontsize=font_size, ncol=3)

plt.xlabel('Timestamp (#)', fontsize=font_size)
plt.ylabel('Total QoE (#)', fontsize=font_size)
plt.xticks([i for i in range(0, len(x) + 1, 5)], fontsize=font_size)
plt.yticks(fontsize=font_size)
plt.xlim(0, 100)
plt.ylim(150, 200)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('Optimal_vs_heuristic_QoE_100_TTIs.pdf')