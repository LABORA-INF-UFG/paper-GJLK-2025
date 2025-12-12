import networkx as nx
import matplotlib.pyplot as plt
import sys
import random
import json


def create_links_list(n_nodes):

    # Calculate the number of nodes in each layer
    n_layer1 = 1
    n_layer2 = max(1, n_nodes // 4)
    n_layer3 = n_nodes - n_layer1 - n_layer2
    # Set a minimum latency for the edges
    min_latency = 0.25
    # Set a maximum latency for the edges
    max_latency = 5.0
    # Set a minimum bandwidth for the edges
    min_bandwidth = 25000
    # Set a maximum bandwidth for the edges
    max_bandwidth = 100000

    # Create an undirected graph
    G = nx.Graph()

    # Add nodes for each layer
    G.add_node(1, layer=1)
    for i in range(2, 2 + n_layer2):
        G.add_node(i, layer=2)
    for i in range(2 + n_layer2, 2 + n_layer2 + n_layer3):
        G.add_node(i, layer=3)

    # Add edges from layer 1 to all nodes in layer 2
    for i in range(2, 2 + n_layer2):
        G.add_edge(1, i, latency=round(random.uniform(min_latency, max_latency), 2),
                   bandwidth=random.randint(min_bandwidth, max_bandwidth))

    # Add edges from layer 2 to layer 3 with 20% probability
    for i in range(2, 2 + n_layer2):
        for j in range(2 + n_layer2, 2 + n_layer2 + n_layer3):
            if random.random() < 0.2:
                G.add_edge(i, j, latency=round(random.uniform(min_latency, max_latency), 2),
                           bandwidth=random.randint(min_bandwidth, max_bandwidth))

    # Ensure each node in layer 3 connects to at least 2 nodes in layer 2
    for j in range(2 + n_layer2, 2 + n_layer2 + n_layer3):
        connections = [i for i in range(2, 2 + n_layer2) if G.has_edge(i, j)]
        while len(connections) < 3:
            potential_connections = [i for i in range(2, 2 + n_layer2) if i not in connections]
            if not potential_connections:
                G.add_edge(1, j, latency=round(random.uniform(min_latency, max_latency), 2),
                           bandwidth=random.randint(min_bandwidth, max_bandwidth))
                connections.append(1)
                continue
            new_connection = random.choice(potential_connections)
            G.add_edge(new_connection, j, latency=round(random.uniform(min_latency, max_latency), 2),
                       bandwidth=random.randint(min_bandwidth, max_bandwidth))
            connections.append(new_connection)

    # Position nodes using a layered layout
    pos = {}
    pos[1] = (0, 2)
    for i in range(2, 2 + n_layer2):
        pos[i] = (i-2, 1)
    for i in range(2 + n_layer2, 2 + n_layer2 + n_layer3):
        pos[i] = (i-2 - n_layer2, 0)

    # Draw the graph
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_size=500, node_color='skyblue')

    # Draw edge labels for latency and bandwidth
    edge_labels = {edge: f"{data['latency']}ms, {data['bandwidth'] * 7.3}Mbps" for edge, data in G.edges.items()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    plt.savefig("figs/{}_nodes.png".format(n_nodes))

    # Generate a list of links with latencies and bandwidths
    all_pairs_latency = {}
    for source in G.nodes():
        for target in G.nodes():
            if source == target:
                latency = 0  # Self-loop with latency 0
            elif source < target:
                try:
                    # Compute the shortest path latency between source and target
                    latency = nx.shortest_path_length(G, source=source, target=target, weight='latency')
                except nx.NetworkXNoPath:
                    latency = float('inf')  # If no path exists, set latency to infinity
            else:
                continue
            all_pairs_latency[(source, target)] = latency

    paths = {}

    for source in G.nodes():
        for target in G.nodes():
            if source != target:
                try:
                    # Get all paths sorted by latency
                    all_paths = sorted(nx.all_simple_paths(G, source=source, target=target), 
                                       key=lambda path: sum(G[u][v]['latency'] for u, v in zip(path[:-1], path[1:])))
                    
                    # Select the three paths with minimum latency
                    for path_id, path in enumerate(all_paths[:3]):
                        latency = sum(G[u][v]['latency'] for u, v in zip(path[:-1], path[1:]))
                        bandwidth = min(G[u][v]['bandwidth'] for u, v in zip(path[:-1], path[1:]))
                        links = [(u, v) for u, v in zip(path[:-1], path[1:])]
                        paths[(source, target, path_id)] = {
                            "path": path,
                            "latency": latency,
                            "bandwidth": bandwidth,
                            "links": links
                        }
                except nx.NetworkXNoPath:
                    continue
            
    links = []

    for (i, j) in G.edges():
        l = G[i][j]['latency']
        b = G[i][j]['bandwidth']
        links.append({"from": i, "to": j, "latency": l, "bandwidth": b})
    
    nodes = []
    # Print the layer of each node
    for node, data in G.nodes(data=True):
        if data['layer'] == 1:
            nodes.append({
                "ID": node,
                "CPU_capacity": 192000,
                "GPU_capacity": 178 * 10**9,
                "RAM_capacity": 768,
                "Network_capacity": 100,
                "compression_ratio": 0.25,
                "Fixed_cost": 0,
                "Variable_cost": {
                    "CPU": 0.0000000193,
                    "GPU": 0.0000000000000208,
                    "RAM": 0.00000483,
                    "NET": 0.0000371,
                    "STO": 0.000000493
                }
            })
        elif data['layer'] == 2:
            nodes.append({
                "ID": node,
                "CPU_capacity": 192000,
                "GPU_capacity": 178 * 10**9,
                "RAM_capacity": 768,
                "Network_capacity": 100,
                "compression_ratio": 0.25,
                "Fixed_cost": 0,
                "Variable_cost": {
                    "CPU": 0.0000000280,
                    "GPU": 0.0000000000000302,
                    "RAM": 0.00000700,
                    "NET": 0.0000538,
                    "STO": 0.000000715
                }
            })
        elif data['layer'] == 3:
            nodes.append({
                "ID": node,
                "CPU_capacity": 192000,
                "GPU_capacity": 178 * 10**9,
                "RAM_capacity": 768,
                "Network_capacity": 100,
                "compression_ratio": 0.25,
                "Fixed_cost": 0,
                "Variable_cost": {
                    "CPU": 0.0000000328,
                    "GPU": 0.0000000000000354,
                    "RAM": 0.00000821,
                    "NET": 0.0000630,
                    "STO": 0.000000838
                }
            })

    # Convert paths dictionary keys to strings
    paths = {f"({source}, {target}, {path_id})": value for (source, target, path_id), value in paths.items()}

    topology_dict = {"nodes": nodes, "links": links, "paths": paths}

    json.dump(topology_dict, open("{}_gNBs.json".format(n_nodes), 'w'), indent=4)

    return all_pairs_latency


if __name__ == "__main__":
    random.seed(5)
    n_nodes = int(sys.argv[1])

    all_pairs_latency = create_links_list(n_nodes)