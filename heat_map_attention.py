import numpy as np

import matplotlib.pyplot as plt

def make_heatmap(heatmap, height, width, center_x, center_y, radius, max_attention, min_attention):
    # Create a grid of (x, y) coordinates
    y_indices, x_indices = np.ogrid[:height, :width]

    # Calculate the distance from each point to the center
    distance = np.sqrt((x_indices - center_x) ** 2 + (y_indices - center_y) ** 2)

    # Create a mask for points inside the circle
    mask = distance <= radius

    # Calculate heatmap values: 100 at center, 50 at edge
    heatmap[mask] = max_attention - min_attention * (distance[mask] / radius)

    return heatmap

# Define the dimensions
width, height = 640, 360

# Generate random heatmap values between 0 and 100
heatmap = np.zeros((height, width))

make_heatmap(heatmap, height, width, 250, 250, 40, 100, 80)
make_heatmap(heatmap, height, width, 250, 180, 40, 80, 50)

# Create the plot
plt.figure(figsize=(12, 6))
plt.imshow(heatmap, extent=[0, width, 0, height], origin='lower', aspect='auto', cmap='hot')
plt.colorbar(label='Heatmap Value')
plt.xlabel('X axis')
plt.ylabel('Y axis')
plt.title('Random Heatmap (0-100)')
plt.show()