from classes import CN, GNB, GAME, USER, PATH
import json

def read_input_files(n_CNs, n_GNBs, n_users, timestamp):
    CNs_list = json.load(open("../../input_files/topology/{}_gNBs.json".format(n_CNs), 'r'))["nodes"]
    CNs = []
    for cn in CNs_list:
        CNs.append(CN(cn["ID"], cn["CPU_capacity"], cn["GPU_capacity"], cn["RAM_capacity"], cn["compression_ratio"], cn["Network_capacity"], cn["Fixed_cost"], cn["Variable_cost"]))
    
    GNBs_list = json.load(open("../../input_files/gNBs/{}_gNBs.json".format(n_GNBs), 'r'))["gNBs"]
    GNBs = []
    for gnb in GNBs_list:
        GNBs.append(GNB(gnb["ID"], gnb["TX_power"], gnb["number_PRBs"], gnb["PRB_BW"]))
    
    Games_list = json.load(open("../../input_files/games/{}_users_games_timestamp_0.json".format(n_users, timestamp), 'r'))["games"]
    Games = []
    for game in Games_list:
        Games.append(GAME(game["ID"], game["CPU_requirement"], game["RAM_requirement"], game["game_type"]))
    
    Users_list = json.load(open("../../input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(n_GNBs, n_users, timestamp), 'r'))["users"]
    Users = []
    for user in Users_list:
        Users.append(USER(user["ID"], user["SE"], user["game"], user["game_instance"], user["max_resolution"], user["max_frame_rate"]))
    
    Paths_list = json.load(open("../../input_files/topology/{}_gNBs.json".format(n_GNBs), 'r'))["paths"]
    Paths = []
    pathID = 0
    Links_latency = {}
    Links_bandwidth = {}
    for path in Paths_list:
        Paths.append(PATH(pathID, Paths_list[path]["path"][0], Paths_list[path]["path"][1], Paths_list[path]["latency"], Paths_list[path]["bandwidth"], Paths_list[path]["links"]))
        pathID += 1
    Links_list = json.load(open("../../input_files/topology/{}_gNBs.json".format(n_GNBs), 'r'))["links"]
    Links = []
    for link in Links_list:
        i = link["from"]
        j = link["to"]
        if (i, j) not in Links:
            Links.append((i, j))
            Links.append((j, i))
        Links_latency[(i, j)] = link["latency"]
        Links_latency[(j, i)] = link["latency"]
        Links_bandwidth[(i, j)] = link["bandwidth"]
        Links_bandwidth[(j, i)] = link["bandwidth"]
    
    return CNs, GNBs, Games, Users, Paths, Links, Links_latency, Links_bandwidth