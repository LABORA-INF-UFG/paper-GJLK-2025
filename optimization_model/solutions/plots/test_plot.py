import numpy as np
import matplotlib.pyplot as plt
import json
from matplotlib.lines import Line2D

fontsize = 15

def raj_jain_fairness(latencies):
    n = len(latencies)
    sum_latencies = sum(latencies)
    sum_latencies_squared = sum(latencies_i ** 2 for latencies_i in latencies)
    fairness_index = (sum_latencies ** 2) / (n * sum_latencies_squared)
    return fairness_index

latency = {}
RCA_latency = {}

QoE = {}
RCA_QoE = {}

Admission = []
RCA_Admission = []

for user in range(1, 17):
    if user in range(1, 7):
        json_obj = json.load(open("../{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    else:
        json_obj = json.load(open("../Heuristic_{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    
    latency[user] = []

    for i in json_obj["Solution"]["Users_QoE"]:
        latency[user].append(json_obj["Solution"]["Users_QoE"][i])
    
    json_obj = json.load(open("../RCA_{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    
    RCA_latency[user] = []

    for i in json_obj["Solution"]["Users_QoE"]:
        RCA_latency[user].append(json_obj["Solution"]["Users_QoE"][i])

# Prepare data for plotting
users = list(range(1, 17))

y1 = [raj_jain_fairness(latency[user]) * 100 for user in users]
RCA_y1 = [raj_jain_fairness(RCA_latency[user]) * 100 for user in users]

for user in range(1, 17):
    json_obj = json.load(open("../{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    
    QoE[user] = []

    for i in json_obj["Solution"]["BS_user_association"]:
        QoE[user].append(i["Latency"])
    
    json_obj = json.load(open("../RCA_{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    
    RCA_QoE[user] = []

    for i in json_obj["Solution"]["BS_user_association"]:
        RCA_QoE[user].append(i["Latency"])

# Prepare data for plotting
users = list(range(1, 17))
y2 = [raj_jain_fairness(QoE[user]) * 100 for user in users]
RCA_y2 = [raj_jain_fairness(RCA_QoE[user]) * 100 for user in users]

for user in range(1, 17):
    json_obj = json.load(open("../{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    my_count = 0
    for i in json_obj["Solution"]["Users_QoE"]:
        if json_obj["Solution"]["Users_QoE"][i] > 0:
            my_count += 1
    Admission.append((my_count * 100)/user)
    
    json_obj = json.load(open("../RCA_{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    RCA_count = 0
    for i in json_obj["Solution"]["Users_QoE"]:
            if json_obj["Solution"]["Users_QoE"][i] > 0:
                RCA_count += 1
    RCA_Admission.append((RCA_count * 100)/user)

# Generate random data
x = np.arange(1, 17)
y3 = Admission
RCA_y3 = RCA_Admission

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 5))

# Plot the first graph
ax1.plot(x[5:], y1[5:], marker='o', markersize=8, fillstyle="none", linestyle='--', color='navy', markerfacecolor='white')
ax1.plot(x[:6], y1[:6], marker='o', markersize=8, linestyle='--', color='navy')
ax1.plot(x[4:], RCA_y1[4:], marker='o', markersize=8, fillstyle="none", linestyle='--', color='firebrick', markerfacecolor='white')
ax1.plot(x[:5], RCA_y1[:5], marker='o', markersize=8, linestyle='--', color='firebrick')
ax1.set_ylabel('RJ QoE (%)', fontsize=fontsize-3)
ax1.set_ylim(0, 112)
ax1.set_yticks([0, 20, 40, 60, 80, 100], ["0", "20", "40", "60", "80", "100"])
ax1.set_xticks([i for i in range(1, 17)])
ax1.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)  # Remove x-axis ticks
ax1.grid(True, axis='both', linestyle='--')  # Add dashed grid lines to both x and y axes

# Plot the second graph
ax2.plot(x[5:], y2[5:], marker='o', markersize=8, fillstyle="none", linestyle='--', color='navy', markerfacecolor='white')
ax2.plot(x[:6], y2[:6], marker='o', markersize=8, linestyle='--', color='navy')
ax2.plot(x[4:], RCA_y2[4:], marker='o', markersize=8, fillstyle="none", linestyle='--', color='firebrick', markerfacecolor='white')
ax2.plot(x[:5], RCA_y2[:5], marker='o', markersize=8, linestyle='--', color='firebrick')
ax2.set_ylabel('RJ Latency (%)', fontsize=fontsize - 3)
ax2.set_ylim(0, 112)
ax2.set_yticks([0, 20, 40, 60, 80, 100], ["0", "20", "40", "60", "80", "100"])
ax2.set_xticks([i for i in range(1, 17)])
ax2.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)  # Remove x-axis ticks
ax2.grid(True, axis='both', linestyle='--')  # Add dashed grid lines to both x and y axes

# Plot the third graph
ax3.plot(x[5:], y3[5:], marker='o', markersize=8, fillstyle="none", linestyle='--', color='navy', markerfacecolor='white')
ax3.plot(x[:6], y3[:6], marker='o', markersize=8, linestyle='--', color='navy')
ax3.plot(x[4:], RCA_y3[4:], marker='o', markersize=8, fillstyle="none", linestyle='--', color='firebrick', markerfacecolor='white')
ax3.plot(x[:5], RCA_y3[:5], marker='o', markersize=8, linestyle='--', color='firebrick')
ax3.set_xlabel('Users (#)', fontsize=fontsize)
ax3.set_ylabel('Admission (%)', fontsize=fontsize-2)
ax3.set_ylim(0, 112)
ax3.set_yticks([0, 20, 40, 60, 80, 100], ["0", "20", "40", "60", "80", "100"])
ax3.set_xticks([i for i in range(1, 17)], [str(i) for i in range(1, 17)])
ax3.grid(True, axis='both', linestyle='--')  # Add dashed grid lines to both x and y axes
ax3.tick_params(axis='x', labelsize=fontsize)
ax3.tick_params(axis='y', labelsize=fontsize-2.5)
ax2.tick_params(axis='y', labelsize=fontsize-2.5)
ax1.tick_params(axis='y', labelsize=fontsize-2.5)

custom_lines = [
    Line2D([0], [0], color='navy', linestyle='-', linewidth=2.5, marker="o", markersize=8, label='VR-GX optimal'),
    Line2D([0], [0], color='navy', linestyle='-', linewidth=2.2, marker="o", fillstyle="none", markersize=8, markerfacecolor='white', label='VR-GX heuristic'),
    Line2D([0], [0], color='firebrick', linestyle='-', linewidth=2.5, markersize=8, marker="o", label='RCA optimal'),
    Line2D([0], [0], color='firebrick', linestyle='-', linewidth=2.2, marker="o", fillstyle="none", markersize=8, markerfacecolor='white', label='RCA approx.')
]

# Adding legend
plt.legend(handles=custom_lines, fontsize=12, ncol=4, loc='lower left', bbox_to_anchor=(-0.1, 2.96))

plt.subplots_adjust(hspace=0)  # Reduce the white space between the graphs
plt.savefig("raj_jain_comparison.png", bbox_inches='tight')