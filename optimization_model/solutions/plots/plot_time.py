import numpy as np
import matplotlib.pyplot as plt
import json
from matplotlib.lines import Line2D
from matplotlib import rcParams

tamanho_fonte = 16

# Use Formata font
rcParams['font.family'] = 'sans-serif'

# Number of users
users = np.arange(1, 17)

# Random QoE values for two lines
qoe_line1 = []
qoe_line2 = []
qoe_line3 = []

for user in range(1, 7):
    json_obj = json.load(open('../{}_users_4_BSs_2_MEC_solution.json'.format(user)))
    qoe_line1.append(json_obj["Solution"]["Time"] * 1000)

for user in range(1, 6):
    json_obj = json.load(open('../C7_{}_users_4_BSs_2_MEC_solution.json'.format(user)))
    qoe_line2.append(json_obj["Solution"]["Time"] * 1000)

for user in range(1, 17):
    json_obj = json.load(open('../Heuristic_{}_users_4_BSs_2_MEC_solution.json'.format(user)))
    qoe_line3.append(json_obj["Solution"]["Time"] * 1000)

# Setting the figure size
plt.figure(figsize=(7.5, 2.8))

plt.yscale("log")

# Plotting the lines
plt.plot(users, qoe_line3, label='Du [16]', color='royalblue', marker="o", markersize=8, linewidth=1.25, linestyle='--')
plt.plot(users[:6], qoe_line1, label='VR-GamingX', color='navy', marker="o", markersize=8, linewidth=1.25, linestyle='--')
plt.plot(users[:5], qoe_line2, label='Du [16]', color='firebrick', marker="o", markersize=8, linewidth=1.25, linestyle='--')

plt.xticks([i for i in range(1, 17)], fontsize=tamanho_fonte)
plt.yticks([10 ** i for i in range(0, 8)], fontsize=tamanho_fonte)

# Adding labels and title
plt.xlabel('Users (#)', fontsize=tamanho_fonte)
plt.ylabel('Time (ms)', fontsize=tamanho_fonte)

plt.grid(True, linestyle="--", alpha=0.7)

# plt.ylim(0, 700)

# Custom legend

custom_lines = [
    Line2D([0], [0], color='navy', linestyle='-', marker='o', linewidth=2.5, markersize=8, label='VR-GX optimal'),
    Line2D([0], [0], color='royalblue', linestyle='-', linewidth=2.5, marker='o', markersize=8, label='VR-GX heuristic'),
    Line2D([0], [0], color='firebrick', linestyle='-', linewidth=2.5, marker='o', markersize=8, label='RCA optimal')
]

# Adding legend
plt.legend(handles=custom_lines, fontsize=12.4, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.22))

# Display the plot
plt.savefig('comparing_users_time.pdf', dpi=300, bbox_inches='tight')