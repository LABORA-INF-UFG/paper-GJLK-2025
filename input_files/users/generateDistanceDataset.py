import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df_BSs = pd.read_csv("nodesPositions.csv", sep=';')

df_Users = pd.read_csv("offloadingDataSet.csv", sep=',')

def calculate_distance(x1, y1, x2, y2):
    x2 = float(x2)
    y2 = float(y2)
    # Calculate Euclidean distance and convert to kilometers
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2) / 1000

distances = []

for _, user in df_Users.iterrows():
    user_distances = {
        "UserID": user["UserID"],
        "Timestamp": int(user["Timestamp"])  # Add the Timestamp column
    }
    for _, node in df_BSs.head(10).iterrows():  # Limit to the first 10 BSs
        if node["X"] != 'X' or node["Y"] != 'Y':
            distance = calculate_distance(user["Xpos"], user["Ypos"], node["X"], node["Y"])
            user_distances[f"Distance_to_Node_{node['Node ID']}"] = distance
    distances.append(user_distances)

df_Distances = pd.DataFrame(distances)

df_Distances.to_csv("usersDistances.csv", sep=',', index=False)