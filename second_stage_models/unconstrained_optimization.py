from docplex.mp.model import Model
from docplex.cp.parameters import CpoParameters
from math import log2, log
from methods import read_input_files
import os
import sys
import json
import time

def get_users_priority(Users, Games):
    users_priority = {}
    for u in Users:
        if Games[u.my_game() - 1].my_game_type() == "quality":
            users_priority[u.my_ID()] = 1
        else:
            users_priority[u.my_ID()] = 0
    return users_priority

def resolution_pixel_size():
    return {"1080p": 1920 * 1080,
            "2K": 2560 * 1440,
            "4K": 3840 * 2160}


def get_users_game_requirements(Users, Games, sol):
    flops_per_pixel = 440 # REF https://openaccess.thecvf.com/content/CVPR2023W/NTIRE/papers/Zamfir_Towards_Real-Time_4K_Image_Super-Resolution_CVPRW_2023_paper.pdf
    users_CPU_demand = {}
    users_RAM_demand = {}
    users_GPU_demand = {}
    users_total_load = {}
    users_load_to_gNB = {}
    users_latency_to_gNB = {}

    for user in Users:
        for g in Games:
            if g.my_ID() == user.my_game():
                game = g
        users_CPU_demand[user.my_ID()] = game.my_CPU_requirement()
        users_RAM_demand[user.my_ID()] = game.my_RAM_requirement()
        for u in sol["solution"]["users"]:
            if u["ID"] == user.my_ID():
                u_resolution = u["resolution"]
                u_frame_rate = u["frame_rate"]
                users_total_load[user.my_ID()] = u["total_load"]
                users_load_to_gNB[user.my_ID()] = {}
                users_latency_to_gNB[user.my_ID()] = {}
                for gNB in u["load_to_gNB"]:
                    users_load_to_gNB[user.my_ID()][gNB] = u["load_to_gNB"][gNB]
                    users_latency_to_gNB[user.my_ID()][gNB] = u["latency_to_gNB"][gNB]

        if u_resolution == "1080p":
            n_pixels = 1920 * 1080 * 2
        elif u_resolution == "2K":
            n_pixels = 2560 * 1440 * 2
        elif u_resolution == "4K":
            n_pixels = 3840 * 2160 * 2
        users_GPU_demand[user.my_ID()] = n_pixels * flops_per_pixel * u_frame_rate

    return users_CPU_demand, users_RAM_demand, users_GPU_demand, users_total_load, users_load_to_gNB, users_latency_to_gNB


def model(n_CNs, n_GNBs, n_users, numerology, timestamp):

    # maximum latency value (delta max)
    delta_max = 1

    # routing latency consireded in the first stage to the closest CN
    user_routing_latency = 0.02
    
    # read input files
    CNs, GNBs, Games, Users, Paths, Links, Links_latency, Links_bandwidth = read_input_files(n_CNs, n_GNBs, n_users, timestamp)

    # get user's computational requirements based on image quality and throughput
    if n_users <= 300:
        sol = json.load(open("../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))
    else:
        sol = json.load(open("../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))

    if timestamp > 0:
        last_timestamp_solution = json.load(open("../solutions/second_stage/unconstrained_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp-1), 'r'))
        users_last_CN = {}
        for user in Users:
            for u in last_timestamp_solution["solution"]["users"]:
                if u == str(user.my_ID()):
                    users_last_CN[user.ID] = last_timestamp_solution["solution"]["users"][u]["used_CN"]
                    break

    users_CPU_demand, users_RAM_demand, users_GPU_demand, users_total_load, users_load_to_gNB, users_latency_to_gNB = get_users_game_requirements(Users, Games, sol)

    # instantiate constraint programming model
    model = Model(name="Second stage", log_output=False)

    new_Paths_IDs = []

    for user in Users:
        for gNB in users_load_to_gNB[user.my_ID()].keys():
            for cn in CNs:
                min_path_length = 99999
                min_path_id = -1
                for p in Paths:
                    if str(p.destination) == gNB and p.source == cn.ID:
                        if len(p.my_links_list()) < min_path_length:
                            if min_path_id != -1:
                                new_Paths_IDs.remove(min_path_id)
                            min_path_length = len(p.my_links_list())
                            min_path_id = p.ID
                            new_Paths_IDs.append(p.ID)
    new_Paths = []
    for i in new_Paths_IDs:
        for p in Paths:
            if p.ID == i and p not in new_Paths:
                new_Paths.append(p)
    
    Paths = new_Paths
    # define decision variable iterators
    CNs_users = [(c.ID, u.ID) for c in CNs for u in Users]
    Paths_users = [(p.ID, u.ID) for p in Paths for u in Users]

    # decision variable that indicates if path p routes the traffic of user u
    model.s = model.binary_var_dict(Paths_users, name="paths_users_S")
    # decision variable that indicates the amount of traffic of user u that is routed by path p
    model.q = model.continuous_var_dict(Paths_users, name="paths_users_Q")
    # decision variable that indicates if CN c is used
    model.u = model.binary_var_dict([cn.ID for cn in CNs], name="CNs_users")
    # decision variable that indicates if CN c is used for user u
    model.v = model.binary_var_dict([(cn.ID, u.ID) for cn in CNs for u in Users], name="CNs_users_v")

    activation_cost = model.sum(model.u[cn.ID] * cn.my_Fixed_cost() for cn in CNs)
    placement_cost = model.sum(model.sum(model.v[cn.ID, u.ID] * (users_CPU_demand[u.my_ID()] * cn.Variable_cost["CPU"] + 
                                                                  users_GPU_demand[u.my_ID()] * cn.Variable_cost["GPU"] + 
                                                                  users_RAM_demand[u.my_ID()] * cn.Variable_cost["RAM"]) for u in Users) for cn in CNs)
    proximity_cost = model.sum(model.sum(model.s[p.ID, u.ID] * p.my_latency() for p in Paths for u in Users if p.source == cn.ID) for cn in CNs)
    colocation_cost = model.sum(model.sum(model.s[p.ID, u.ID] for p in Paths for u in Users if p.source == cn.ID) for cn in CNs)

    # objective function - minimize the total cost of the CNs
    model.minimize(activation_cost + placement_cost + proximity_cost + colocation_cost)
    
    # check if CN c is used by any user u - if yes, then variable u = 1, else u = 0
    for cn in CNs:
        model.add_constraint(model.sum(model.s[p.ID, u.ID] for p in Paths for u in Users if p.source == cn.ID) >= model.u[cn.ID], "Q1")
        model.add_constraint(model.sum(model.s[p.ID, u.ID] for p in Paths for u in Users if p.source == cn.ID)/(len(Users) * len(Paths)) <= model.u[cn.ID], "Q2")
    
    # check if CN c is used by user u - if yes, then variable v = 1, else v = 0
    for cn in CNs:
        for user in Users:
            model.add_constraint(model.sum(model.s[p.ID, user.ID] for p in Paths if p.source == cn.ID) >= model.v[cn.ID, user.ID], "Q1")
            model.add_constraint(model.sum(model.s[p.ID, user.ID] for p in Paths if p.source == cn.ID)/len(Paths) <= model.v[cn.ID, user.ID], "Q2")
    
    # the game engine of each user is running at exactly one CN
    for user in Users:
        model.add_constraint(model.sum(model.v[cn.ID, user.ID] for cn in CNs) == 1, "Q3")
    
    for i in Paths_users:
        # if the path is selected to transmit the traffic of user u, then the amount of traffic must be less than the path capacity
        # if the path is not used, it must not transmit any traffic for the user
        model.add_constraint(model.s[i] * 1.0 <= model.q[i], "Q8")
        model.add_constraint(model.s[i] * 1.0 >= model.q[i], "Q9")
    
    # Exactly one path must be used to transmit the data for each user according to its gNB association
    for user in Users:
        for gNB in users_load_to_gNB[user.my_ID()].keys():
            model.add_constraint(model.sum(model.s[p.ID, user.ID] for p in Paths if str(p.destination) == gNB) == 1, "Q10")
    
    # A user can only be assigned to a path if the path destination is one of its gNBs
    for user in Users:
        for p in Paths:
            if str(p.my_destination()) not in users_load_to_gNB[user.my_ID()].keys():
                model.add_constraint(model.s[p.ID, user.ID] == 0, "Q11")
    
    # the amount of traffic routed by a path must not exceed its capacity
    for p in Paths:
        for gNB in GNBs:
            for link in Links:
                model.add_constraint(model.sum((model.q[p.ID, user.ID]) * users_load_to_gNB[user.my_ID()][str(gNB.ID)] for user in Users if link in p.my_links_list() 
                                                                                                                                                and str(gNB.ID) in users_load_to_gNB[user.my_ID()]
                                                                                                                                                and p.my_destination() == gNB.ID) <= Links_bandwidth[link] * 10 ** 6, "Q13")

    start_time = time.time()
    model.solve()
    elapsed_time = time.time() - start_time

    user_CN = {}

    if model.solution is not None:
        solution_json = {"solution": {"Total_Cost": placement_cost.solution_value, "time": elapsed_time, "Used_CNs": [], "users": {user.ID: {"max_latency": 0, "used_CN": -1} for user in Users}, "migration_cost": 0}}
        for user in Users:
            for p in Paths:
                if model.s[p.ID, user.ID].solution_value == 1:
                    # print("User {} is assigned to CN {}".format(user.ID, p.source))
                    if timestamp > 2 and p.source != users_last_CN[user.ID]:
                        solution_json["solution"]["migration_cost"] += 1
                    if p.source not in solution_json["solution"]["Used_CNs"]:
                        solution_json["solution"]["Used_CNs"].append(p.source)
                    user_CN[user.ID] = p.source
                    solution_json["solution"]["users"][user.ID]["used_CN"] = p.source
                    break
        for p in Paths:
            for u in Users:
                user_latency = 0
                if model.s[p.ID, u.ID].solution_value == 1:
                    if p.my_latency()/1000 + (users_latency_to_gNB[u.ID][str(p.destination)] - user_routing_latency) > user_latency:
                        user_latency = p.my_latency()/1000 + (users_latency_to_gNB[u.ID][str(p.destination)] - user_routing_latency)
                    # print("User {} is assigned to path {} with traffic ratio {}%".format(u.ID, p.ID, model.q[p.ID, u.ID].solution_value * 100))
                    if p.source != user_CN[u.ID]:
                        print("ERROR: User {} is assigned to path {} with source {} but CN {} is used".format(u.ID, p.ID, p.source, user_CN[u.ID]))
                    solution_json["solution"]["users"][u.ID]["max_latency"] = user_latency
        json.dump(solution_json, open("../solutions/second_stage/unconstrained_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'w'), indent=4)
    else:
        print("No solution found")
        json.dump({"solution": "Not found"}, open("../solutions/second_stage/unconstrained_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'w'), indent=4)

if __name__ == "__main__":
    n_CNs = int(sys.argv[1])
    n_GNBs = int(sys.argv[2])
    n_users = int(sys.argv[3])
    numerology = 1
    for t in range(0, 1):
        model(n_CNs, n_GNBs, n_users, numerology, timestamp=t)