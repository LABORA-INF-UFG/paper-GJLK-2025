import numpy as np
import matplotlib.pyplot as plt
import json

# Set the random seed for reproducibility
np.random.seed(555)

# Define the circle parameters
diameter = 1
radius = diameter / 2

# Update the centers with the new coordinates
centers = [
    (-0.9, 0.5),
    (-0.5, 0.9),
    (-0.5, 0.1),
    (-0.1, 0.5)
]

# Number of users per circle
n_users = 4

# Dictionary to store user positions and distances
user_positions = {i: [] for i in range(len(centers))}

# Create a figure and axis
fig, ax = plt.subplots()

# Plot each circle
for i, (x, y) in enumerate(centers):
    circle = plt.Circle((x, y), radius, edgecolor='black', facecolor='none')
    ax.add_patch(circle)
    
    # Plot a blue square at the center of the circle
    ax.plot(x, y, 'bs', markersize=5)
    
    # Generate random points inside the circle
    user_id = i * n_users
    for _ in range(n_users):
        r = radius * np.sqrt(np.random.rand())
        theta = 2 * np.pi * np.random.rand()
        user_x = x + r * np.cos(theta)
        user_y = y + r * np.sin(theta)
        ax.plot(user_x, user_y, 'ro', markersize=4)
        
        # Annotate user ID
        ax.text(user_x, user_y, str(user_id), fontsize=8, ha='right')
        
        # Store user position
        user_positions[i].append((user_x, user_y))
        
        user_id += 1

# Set the aspect of the plot to be equal
ax.set_aspect('equal')

# Set limits to see the circles clearly
ax.set_xlim(-1.6, 0.6)
ax.set_ylim(-0.6, 1.6)

# Show the plot
plt.grid(True)

# Constants
frequency = 4.2e9  # Frequency in Hz
c = 3e8  # Speed of light in m/s

# Transmit power in dBm
transmit_power_dbm = 30

# Convert transmit power from dBm to mW
transmit_power_mw = 10 ** (transmit_power_dbm / 10)

# Noise power in mW (assuming a noise figure of 10 dB and bandwidth of 1 MHz)
noise_figure_db = 10
bandwidth_hz = 1e6
thermal_noise_dbm = -174 + 10 * np.log10(bandwidth_hz)
noise_power_dbm = thermal_noise_dbm + noise_figure_db
noise_power_mw = 10 ** (noise_power_dbm / 10)

# Example interference dictionary (interference power in mW for each user)
interference = {
    0: [0.1 * 4],  # Interference power for users in circle 0
    1: [0.2 * 4],  # Interference power for users in circle 1
    2: [0.15 * 4], # Interference power for users in circle 2
    3: [0.05 * 4]  # Interference power for users in circle 3
}

# Calculate SINR for each user to each blue square considering interference
sinr = {}
user_id = 0
for i, user_list in user_positions.items():
    for user_x, user_y in user_list:
        sinr[user_id] = {}
        for j, (center_x, center_y) in enumerate(centers):
            distance_to_center = np.sqrt((user_x - center_x) ** 2 + (user_y - center_y) ** 2)
            if distance_to_center == 0:
                fspl_value = float('inf')  # Avoid log(0) error
            else:
                fspl_value = 20 * np.log10(distance_to_center) + 20 * np.log10(frequency) - 20 * np.log10(c)
            
            # Convert FSPL from dB to linear scale
            path_loss_linear = 10 ** (fspl_value / 10)
            
            # Received power in mW
            received_power_mw = transmit_power_mw / path_loss_linear
            
            # Interference power for the current user
            interference_power_mw = interference[i][0]  # Assuming single user per circle
            
            # SINR calculation considering interference
            sinr_value = received_power_mw / (noise_power_mw + interference_power_mw)
            sinr[user_id][j] = 10 * np.log10(sinr_value)  # Convert SINR to dB
        
        user_id += 1

user_sinr_list = {}

for i in sinr:
    user_sinr_list[i] = []
    for j in sinr[i]:
        user_sinr_list[i].append({
            "BS_ID": j,
            "SINR": sinr[i][j]
        })

# Save the figure as a PDF file with a tight layout
plt.savefig('16_users_distribution_seed_555.pdf', bbox_inches='tight')

user_resolution = {}
user_fps = {}

for u in range(0, 17):
    user_resolution[u] = np.random.choice(["2k", "4k", "8k"])
    user_fps[u] = int(np.random.choice([30, 60, 90]))

for u in range(1, 17):
    json_dict = {}
    json_dict["users"] = []
    apps_ID = {}
    apps_ID[0] = 1
    apps_ID[1] = 1
    apps_ID[2] = 2
    apps_ID[3] = 2
    apps_ID[4] = 3
    apps_ID[5] = 4
    apps_ID[6] = 5
    apps_ID[7] = 1
    apps_ID[8] = 1
    apps_ID[9] = 2
    apps_ID[10] = 2
    apps_ID[11] = 1
    apps_ID[12] = 1
    apps_ID[13] = 2
    apps_ID[14] = 2
    apps_ID[15] = 3
        
    for id in range(u):
        json_dict["users"].append({
            "ID": id,
            "device": {
                "resolution": user_resolution[id],
                "fps": int(user_fps[id])
                },
            "application_ID": apps_ID[id],
            "SINR": user_sinr_list[id]
        })
    
    json.dump(json_dict, open("users/{}_users.json".format(u), "w"), indent=4)