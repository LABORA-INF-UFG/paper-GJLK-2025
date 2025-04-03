import numpy as np
import matplotlib.pyplot as plt
import json

tamanho_fonte = 15

y_VRGamingX = []
y_C7 = []
x_values = list(range(1, 17))

for user in range(1, 17):
    json_obj = json.load(open("../{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    bh_sum = 0
    for i in json_obj["Solution"]["BSs_usage"]:
        bh_sum += json_obj["Solution"]["BSs_usage"][i]/(10 ** 6)
    y_VRGamingX.append(bh_sum)

    json_obj = json.load(open("../C7_{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    bh_sum = 0
    for i in json_obj["Solution"]["BSs_usage"]:
        bh_sum += json_obj["Solution"]["BSs_usage"][i]/(10 ** 6)
    y_C7.append(bh_sum)

# Define the width of the bars
bar_width = 0.35

# Create positions for the bars
r1 = np.arange(len(x_values))
r2 = [x + bar_width for x in r1]
# Set the figure size
plt.figure(figsize=(6, 3.2))
# Create bar plot
plt.bar(r1, y_VRGamingX, color="navy", width=bar_width, label='VR-GX model')
plt.bar(r2, y_C7, color="firebrick", width=bar_width, label='RCA model')
plt.grid(axis="y", linestyle='--')
# Add labels and title
plt.xlabel('Users (#)', fontsize=tamanho_fonte)
plt.ylabel('BW usage (MHz)', fontsize=tamanho_fonte)
plt.xticks([r + bar_width / 2 for r in range(len(x_values))], x_values, fontsize=14)
plt.yticks(fontsize=tamanho_fonte)
plt.ylim(0, 400)
plt.legend(fontsize=12, ncol=2, loc="upper center", bbox_to_anchor=(0.65, 1.22))
plt.tight_layout()
plt.savefig("BSs_resource_usage.pdf", bbox_inches='tight')