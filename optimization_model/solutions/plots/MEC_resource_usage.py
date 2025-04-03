import numpy as np
import matplotlib.pyplot as plt
import json

y_VRGamingX = []
y_C7 = []
x_values = list(range(2, 11))

for user in range(2, 11):
    json_obj = json.load(open("../{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    bh_sum = 0
    for i in json_obj["Solution"]["MEC_usage"]:
        bh_sum += json_obj["Solution"]["MEC_usage"][i]/(10 ** 9)
    y_VRGamingX.append(bh_sum)

    json_obj = json.load(open("../C7_{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    bh_sum = 0
    for i in json_obj["Solution"]["MEC_usage"]:
        bh_sum += json_obj["Solution"]["MEC_usage"][i]/(10 ** 9)
    y_C7.append(bh_sum)

# Define the width of the bars
bar_width = 0.35

# Create positions for the bars
r1 = np.arange(len(x_values))
r2 = [x + bar_width for x in r1]
# Set the figure size
plt.figure(figsize=(5, 3))
# Create bar plot
plt.bar(r1, y_VRGamingX, color="navy", width=bar_width, label='VR Gaming X')
plt.bar(r2, y_C7, color="firebrick", width=bar_width, label='C7')
plt.grid(axis="y", linestyle='--')
# Add labels and title
plt.xlabel('Users (#)', fontsize=16)
plt.ylabel('Bandwidth (%)', fontsize=16)
plt.xticks([r + bar_width / 2 for r in range(len(x_values))], x_values, fontsize=16)
plt.yticks(fontsize=16)
# plt.ylim(0, 100)
plt.legend(fontsize=14, ncol=2, loc="upper center", bbox_to_anchor=(0.594, 1.3))
plt.tight_layout()
plt.savefig("MEC_resource_usage.pdf", bbox_inches='tight')