import numpy as np
import matplotlib.pyplot as plt
import json
from matplotlib.lines import Line2D
from matplotlib import rcParams

tamanho_fonte = 13

# Use Formata font
rcParams['font.family'] = 'sans-serif'

# Number of users
users = np.arange(1, 17)

# Random QoE values for two lines
qoe_line1 = []
qoe_line2 = []
qoe_line3 = []
qoe_line4 = []
qoe_line5 = []

qoe_avg_line1 = []
qoe_avg_line2 = []
qoe_avg_line3 = []
qoe_avg_line4 = []
qoe_avg_line5 = []

MEC_max_usage = 0
sol = -1
for user in range(1, 17):
    json_obj = json.load(open('../{}_users_4_BSs_2_MEC_solution.json'.format(user)))
    for i in json_obj["Solution"]["MEC_usage"]:
        if json_obj["Solution"]["MEC_usage"][i] > MEC_max_usage:
            MEC_max_usage = json_obj["Solution"]["MEC_usage"][i]
            sol = user
print(MEC_max_usage, sol)

scalar = 1

for user in range(1, 7):
    json_obj = json.load(open('../{}_users_4_BSs_2_MEC_solution.json'.format(user)))
    qoe_line1.append(json_obj["Solution"]["Total_QoE"])
    
    my_count = 0
    for i in json_obj["Solution"]["Users_QoE"]:
        if json_obj["Solution"]["Users_QoE"][i] > 0:
            my_count += 1
    avg = json_obj["Solution"]["Total_QoE"]/my_count
    qoe_avg_line1.append(avg * scalar)

for user in range(1, 17):
    json_obj = json.load(open('../RCA_{}_users_4_BSs_2_MEC_solution.json'.format(user)))
    qoe_line2.append(json_obj["Solution"]["Total_QoE"])

    my_count = 0
    for i in json_obj["Solution"]["Users_QoE"]:
        if json_obj["Solution"]["Users_QoE"][i] > 0:
            my_count += 1
    avg = json_obj["Solution"]["Total_QoE"]/my_count
    qoe_avg_line2.append(avg * scalar)

for user in range(1, 17):
    json_obj = json.load(open('../{}_users_4_BSs_2_MEC_solution.json'.format(user)))
    qoe_line3.append(json_obj["Solution"]["Total_QoE"])

    my_count = 0
    for i in json_obj["Solution"]["Users_QoE"]:
        if json_obj["Solution"]["Users_QoE"][i] > 0:
            my_count += 1
    avg = json_obj["Solution"]["Total_QoE"]/my_count
    qoe_avg_line3.append(avg * scalar)

for user in range(1, 17):
    json_obj = json.load(open('../Only_LQ_{}_users_4_BSs_2_MEC_solution.json'.format(user)))
    qoe_line4.append(json_obj["Solution"]["Total_QoE"])
    
    my_count = 0
    for i in json_obj["Solution"]["Users_QoE"]:
        if json_obj["Solution"]["Users_QoE"][i] > 0:
            my_count += 1
    avg = json_obj["Solution"]["Total_QoE"]/my_count
    qoe_avg_line4.append(avg * scalar)

for user in range(1, 13):
    json_obj = json.load(open('../Only_HQ_{}_users_4_BSs_2_MEC_solution.json'.format(user)))
    qoe_line5.append(json_obj["Solution"]["Total_QoE"])
    
    my_count = 0
    for i in json_obj["Solution"]["Users_QoE"]:
        if json_obj["Solution"]["Users_QoE"][i] > 0:
            my_count += 1
    avg = json_obj["Solution"]["Total_QoE"]/my_count
    qoe_avg_line5.append(avg * scalar)

print(qoe_avg_line1)
print(qoe_avg_line2)
print(qoe_avg_line3)
print(qoe_avg_line4)
print(qoe_avg_line5)

# Plotting Average QoE
plt.figure(figsize=(6, 2))
ax1 = plt.gca()

ax1.plot(users, qoe_avg_line4, label='4K/30FPS', color='darkgreen', marker="o", markersize=8, linewidth=1.5, linestyle='--')
ax1.plot(users, qoe_avg_line3, label='Du [10]', color='navy', marker="o", fillstyle="none", markersize=8, markerfacecolor='white', linewidth=1.5, linestyle='--')
ax1.plot(users[:6], qoe_avg_line1, label='VR-GamingX', color='navy', marker="o", markersize=8, linewidth=1.5, linestyle='--')
ax1.plot(users[4:], qoe_avg_line2[4:], label='Du [10]', color='firebrick', marker="o", fillstyle="none", markersize=8, markerfacecolor='white', linewidth=1.5, linestyle='--')
ax1.plot(users[:5], qoe_avg_line2[:5], label='Du [10]', color='firebrick', marker="o", markersize=8, linewidth=1.5, linestyle='--')

ax1.set_ylabel('Average QoE (#)', fontsize=tamanho_fonte)
ax1.set_xlabel('Users (#)', fontsize=tamanho_fonte)
ax1.set_yticks([i * 10 for i in range(0, 8)])
ax1.tick_params(axis='y', labelsize=tamanho_fonte)
plt.xticks([i for i in range(1, 17)], fontsize=tamanho_fonte)
plt.grid(True, linestyle="--", alpha=0.7)

custom_lines_avg = [
    Line2D([0], [0], color='navy', linestyle='-', linewidth=2.5, marker="o", markersize=8, label='VR-GX optimal'),
    Line2D([0], [0], color='firebrick', linestyle='-', linewidth=2.5, markersize=8, marker="o", label='RCA optimal'),
    Line2D([0], [0], color='navy', linestyle='-', linewidth=2.2, marker="o", fillstyle="none", markersize=8, markerfacecolor='white', label='VR-GX heuristic'),
    Line2D([0], [0], color='firebrick', linestyle='-', linewidth=2.2, marker="o", fillstyle="none", markersize=8, markerfacecolor='white', label='RCA approx.'),
    Line2D([0], [0], color='darkgreen', linestyle='-', linewidth=2.2, marker="o", markersize=8, label='4K/30FPS')
]

plt.legend(handles=custom_lines_avg, fontsize=10.2, loc='lower left', bbox_to_anchor=(-0.02, 0.98), ncol=3)
plt.savefig('average_QoE.pdf', dpi=300, bbox_inches='tight')

# Plotting Total QoE
plt.figure(figsize=(6, 2))
ax2 = plt.gca()


ax2.plot(users, qoe_line4, label='4K/30FPS', color='darkgreen', marker="o", markersize=8, linewidth=1.5, linestyle='--')
ax2.plot(users, qoe_line3, label='Du [10]', color='navy', marker="o", fillstyle="none", markersize=8, markerfacecolor='white', linewidth=1.5, linestyle='--')
ax2.plot(users[:6], qoe_line1, label='VR-GamingX', color='navy', marker="o", markersize=8, linewidth=1.5, linestyle='--')
ax2.plot(users[4:], qoe_line2[4:], label='Du [10]', color='firebrick', marker="o", fillstyle="none", markersize=8, markerfacecolor='white', linewidth=1.5, linestyle='--')
ax2.plot(users[:5], qoe_line2[:5], label='Du [10]', color='firebrick', marker="o", markersize=8, linewidth=1.5, linestyle='--')

ax2.set_ylabel('Total QoE (#)', fontsize=tamanho_fonte)
ax2.set_xlabel('Users (#)', fontsize=tamanho_fonte)
ax2.set_yticks([i * 100 for i in range(0, 8)])
ax2.tick_params(axis='y', labelsize=tamanho_fonte)
plt.xticks([i for i in range(1, 17)], fontsize=tamanho_fonte)
plt.grid(True, linestyle="--", alpha=0.7)

custom_lines_total = [
    Line2D([0], [0], color='navy', linestyle='-', linewidth=2.5, marker="o", markersize=8, label='VR-GX optimal'),
    Line2D([0], [0], color='firebrick', linestyle='-', linewidth=2.5, markersize=8, marker="o", label='RCA optimal'),
    Line2D([0], [0], color='navy', linestyle='-', linewidth=2.2, marker="o", fillstyle="none", markersize=8, markerfacecolor='white', label='VR-GX heuristic'),
    Line2D([0], [0], color='firebrick', linestyle='-', linewidth=2.2, marker="o", fillstyle="none", markersize=8, markerfacecolor='white', label='RCA approx.'),
    Line2D([0], [0], color='darkgreen', linestyle='-', linewidth=2.2, marker="o", markersize=8, label='4K/30FPS')
]

plt.legend(handles=custom_lines_total, fontsize=10.2, loc='lower left', bbox_to_anchor=(-0.02, 0.98), ncol=3)
plt.savefig('total_QoE.png', dpi=300, bbox_inches='tight')
