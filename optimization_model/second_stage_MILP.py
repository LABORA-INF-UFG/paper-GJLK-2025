from docplex.mp.model import Model
from methods import read_input_files
import sys
import json
import time

def get_users_game_requirements(Users, Games, sol):
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
        
        bytes_per_pixel = 4  # RGBA8 color model - 

        buffers_per_stream = 3 # triple buffering - https://ieeexplore.ieee.org/abstract/document/6508274

        # this calculates the user demand in bytes - depends on the number of pixels, the frame rate, the byte_per_pixel defined by the RGBA8 color model and the buffer_per_stream considered in RT video transmission
        users_GPU_demand[user.my_ID()] = n_pixels * u_frame_rate * bytes_per_pixel * buffers_per_stream

    return users_CPU_demand, users_RAM_demand, users_GPU_demand, users_total_load, users_load_to_gNB, users_latency_to_gNB


def model(n_CNs, n_GNBs, n_users, timestamp):

    # maximum latency value (delta max)
    delta_max = 1
    
    # user latency considered in the first stage to the closest CN
    user_routing_latency = 0.02

    # read input files
    CNs, GNBs, Games, Users, Paths, Links, Links_latency, Links_bandwidth = read_input_files(n_CNs, n_GNBs, n_users, timestamp)

    # get user's computational requirements based on image quality and throughput
    if n_users <= 300:
        sol = json.load(open("../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))
    else:
        sol = json.load(open("../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))
    users_CPU_demand, users_RAM_demand, users_GPU_demand, users_total_load, users_load_to_gNB, users_latency_to_gNB = get_users_game_requirements(Users, Games, sol)

    users_last_CN = {}

    for user in Users:
        users_last_CN[user.my_ID()] = -1

    if timestamp > 0:
        last_timestamp_solution = json.load(open("../solutions/second_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp-1), 'r'))
        for user in Users:
            for u in last_timestamp_solution["solution"]["users"]:
                if u == str(user.my_ID()):
                    users_last_CN[user.ID] = last_timestamp_solution["solution"]["users"][u]["used_CN"]
                    break

    users_in_gNB = {}

    for gNB in GNBs:
        users_in_gNB[gNB.ID] = 0
        for user in Users:
            if str(gNB.ID) in users_load_to_gNB[user.my_ID()].keys():
                users_in_gNB[gNB.ID] += 1

    # instantiate constraint programming model
    model = Model(name="Second stage", log_output=False)
    model.context.cplex_parameters.timelimit = 60 * 60

    # define decision variable iterators
    Paths_users = [(p.ID, u.ID) for p in Paths for u in Users if str(p.destination) in users_load_to_gNB[u.my_ID()].keys()]

    # decision variable that indicates if path p routes the traffic of user u
    model.s = model.binary_var_dict(Paths_users, name="paths_users_S")
    # decision variable that indicates the amount of traffic of user u that is routed by path p
    model.q = model.continuous_var_dict(Paths_users, name="paths_users_Q")
    # decision variable that indicates if CN c is used
    model.u = model.binary_var_dict([cn.ID for cn in CNs], name="CNs_users")
    # decision variable that indicates if CN c is used for user u
    model.v = model.binary_var_dict([(cn.ID, u.ID) for cn in CNs for u in Users], name="CNs_users_v")

    migration_constant = 0.5 # range from 0.3 to 1.5

    # objective function - minimize the total cost of the CNs
    model.minimize(model.sum(model.u[cn.ID] * cn.my_Fixed_cost() + 
                                model.sum(model.v[cn.ID, u.ID] * (users_CPU_demand[u.my_ID()] * cn.Variable_cost["CPU"] + 
                                                                  users_GPU_demand[u.my_ID()] * cn.Variable_cost["GPU"] + 
                                                                  users_RAM_demand[u.my_ID()] * cn.Variable_cost["RAM"]) for u in Users)
                             for cn in CNs)
                        + model.sum(model.s[p.ID, u.ID] * migration_constant for p in Paths for u in Users if str(p.destination) in users_load_to_gNB[u.my_ID()].keys() and p.source != users_last_CN[u.ID] and timestamp > 0)
                )
    
    # model.maximize(model.sum(model.s[i] for i in Paths_users))
    
    # check if CN c is used - if yes, then variable u = 1, else u = 0
    for cn in CNs:
        model.add_constraint(model.sum(model.s[p.ID, user.ID] for p in Paths for user in Users if p.source == cn.ID and str(p.destination) in users_load_to_gNB[user.ID].keys()) >= model.u[cn.ID])
        model.add_constraint(model.sum(model.s[p.ID, user.ID] for p in Paths for user in Users if p.source == cn.ID and str(p.destination) in users_load_to_gNB[user.ID].keys())/(len(Paths) * len(Users)) <= model.u[cn.ID])

    # check if CN c is used by user u - if yes, then variable v = 1, else v = 0
    for cn in CNs:
        for user in Users:
            model.add_constraint(model.sum(model.s[p.ID, user.ID] for p in Paths if p.source == cn.ID and str(p.destination) in users_load_to_gNB[user.ID].keys()) >= model.v[cn.ID, user.ID])
            model.add_constraint(model.sum(model.s[p.ID, user.ID] for p in Paths if p.source == cn.ID and str(p.destination) in users_load_to_gNB[user.ID].keys())/len(Paths) <= model.v[cn.ID, user.ID])
    
    # the game engine of each user is running at exactly one CN
    for user in Users:
        model.add_constraint(model.sum(model.v[cn.ID, user.ID] for cn in CNs) == 1)
    
    for i in Paths_users:
        # if the path is selected to transmit the traffic of user u, then the amount of traffic must be less than the path capacity
        # if the path is not used, it must not transmit any traffic for the user
        model.add_constraint(model.s[i] * 0.00001 <= model.q[i])
        model.add_constraint(model.s[i] * 1.0 >= model.q[i])
    
    # At least one path must be used to transmit the data for each user according to its gNB association
    for user in Users:
        for gNB in users_load_to_gNB[user.my_ID()].keys():
            model.add_constraint(model.sum(model.s[p.ID, user.ID] for p in Paths if str(p.destination) == gNB) >= 1)
    
    # the amount of traffic routed by a path must not exceed its capacity
    for p in Paths:
        for gNB in GNBs:
            for link in Links:
                model.add_constraint(model.sum(model.q[p.ID, user.ID] * users_load_to_gNB[user.my_ID()][str(gNB.ID)] for user in Users if link in p.my_links_list() 
                                                                                                                                                and str(gNB.ID) in users_load_to_gNB[user.my_ID()]
                                                                                                                                                and p.my_destination() == gNB.ID) <= Links_bandwidth[link] * 10 ** 6, "Q13")
    
    # the selected path must not exceed the maximum latency delta
    for p in Paths:
        for gNB in GNBs:
            if p.my_destination() == gNB.ID:
                for user in Users:
                    if str(gNB.ID) in users_latency_to_gNB[user.my_ID()].keys():
                        model.add_constraint(model.s[p.ID, user.ID] * (p.my_latency()/1000) + (users_latency_to_gNB[user.my_ID()][str(gNB.ID)] - user_routing_latency) <= delta_max, "Q14")
    
    # the sum of traffic routed by all paths must respect the user's demand
    for user in Users:
        model.add_constraint(model.sum(model.q[p.ID, user.ID] for p in Paths if str(p.destination) in users_load_to_gNB[user.ID].keys()) == 1.0)

    start_time = time.time()
    model.solve()
    elapsed_time = time.time() - start_time

    user_CN = {}

    if model.solution is not None:
        print("The solution is {} and OF value is {}".format(model.get_solve_status(), model.solution.get_objective_value()))
        solution_json = {"solution": {"Total_Cost": model.solution.get_objective_value(), "time": elapsed_time, "Used_CNs": [], "users": {user.ID: {"max_latency": 0, "used_CN": -1} for user in Users}, "migration_cost": 0}}
        for user in Users:
            for p in Paths:
                if str(p.destination) in users_load_to_gNB[user.my_ID()].keys():
                    if model.s[p.ID, user.ID].solution_value >= 0.999:
                        # print("User {} is assigned to CN {}".format(user.ID, p.source))
                        if timestamp > 0 and p.source != users_last_CN[user.ID]:
                            solution_json["solution"]["migration_cost"] += migration_constant
                        if p.source not in solution_json["solution"]["Used_CNs"]:
                            solution_json["solution"]["Used_CNs"].append(p.source)
                        # print("User {} is using CN {}".format(user.ID, p.source))
                        user_CN[user.ID] = p.source
                        solution_json["solution"]["users"][user.ID]["used_CN"] = p.source
                        break
        for p in Paths:
            for user in Users:
                user_latency = 0
                if str(p.destination) in users_load_to_gNB[user.my_ID()].keys():
                    if model.s[p.ID, user.ID].solution_value >= 0.999:
                        if p.my_latency()/1000 + users_latency_to_gNB[user.ID][str(p.destination)] > user_latency:
                            user_latency = p.my_latency()/1000 + users_latency_to_gNB[user.ID][str(p.destination)]
                        # print("User {} is assigned to path {} with traffic ratio {}%".format(user.ID, p.ID, model.q[p.ID, user.ID].solution_value * 100))
                        if p.source != user_CN[user.ID]:
                            print("ERROR: User {} is assigned to path {} with source {} but CN {} is used".format(user.ID, p.ID, p.source, user_CN[user.ID]))
                        solution_json["solution"]["users"][user.ID]["max_latency"] = user_latency
        json.dump(solution_json, open("../solutions/second_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'w'), indent=4)
    else:
        print("No solution found")
        json.dump({"solution": "Not found"}, open("../solutions/second_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'w'), indent=4)
    
    # for user in Users:
    #     for p in Paths:
    #         for cn in CNs:
    #             if p.source == cn.ID and str(p.destination) in users_load_to_gNB[user.my_ID()].keys():
    #                 if model.s[p.ID, user.ID].solution_value >= 0.999:
    #                     print("User {} is assigned to CN {} with path {} and load rate {}".format(user.my_ID(), cn.ID, p.ID, model.q[p.ID, user.ID].solution_value))
    #                     print("Path {} used with source CN {} and destination {}".format(p.ID, p.source, p.destination))
    #                     # print("User {} is associated with gNBs {} and path goes to {}".format(user.my_ID(), users_load_to_gNB[user.my_ID()].keys(), p.destination))
    #                     break
    # for cn in CNs:
    #     if model.u[cn.ID].solution_value >= 0.999:
    #         print("CN {} is used".format(cn.ID))
    
    # for cn in CNs:
    #     for user in Users:
    #         if model.v[cn.ID, user.ID].solution_value >= 0.999:
    #             print("CN {} is used by user {}".format(cn.ID, user.my_ID()))

if __name__ == "__main__":
    n_CNs = int(sys.argv[1])
    n_GNBs = int(sys.argv[2])
    n_users = int(sys.argv[3])
    for t in range(0, 100):
        model(n_CNs, n_GNBs, n_users, timestamp=t)