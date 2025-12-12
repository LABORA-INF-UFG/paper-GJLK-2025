from docplex.cp.model import CpoModel
from docplex.cp.parameters import CpoParameters
from math import log2, log
from methods import read_input_files
import os
import sys
import json
import time
import math

def get_users_priority(Users, Games):
    users_priority = {}
    for u in Users:
        for game in Games:
            if game.ID == u.my_game():
                if game.game_type == "quality":
                    users_priority[u.my_ID()] = 1
                else:
                    users_priority[u.my_ID()] = 0
    return users_priority

def resolution_pixel_size():
    return {"1080p": 1920 * 1080 * 2,
            "2K": 2560 * 1440 * 2,
            "4K": 3840 * 2160 * 2}
    
def calculate_user_PRB_request(user, gNB, res, fps, codec_bpp, delta_max):
    resoultion_dict = resolution_pixel_size()
    PRBs_throughput = int(math.ceil((resoultion_dict[res] * codec_bpp * fps)/(gNB.my_PRB_BW() * 10 ** 6 * user.my_SE(gNB.ID))))
    PRBs_latency = int(math.ceil((resoultion_dict[res] * codec_bpp * fps)/(gNB.my_PRB_BW() * 10 ** 6 * user.my_SE(gNB.ID) * delta_max)))

    return max(PRBs_throughput, PRBs_latency)
    

def model(n_CNs, n_GNBs, n_users, numerology, timestamp):
    
    # define number of TTIs in a second based on numerology
    if numerology == 0:
        n_TTIs = 1000
    elif numerology == 1:
        n_TTIs = 2000
    elif numerology == 2:
        n_TTIs = 4000
    elif numerology == 3:
        n_TTIs = 8000
    elif numerology == 4:
        n_TTIs = 16000

    # considering 20 ms for routing latency to the closest CN
    user_routing_latency = 0.02

    # maximum latency value (delta max)
    delta_max = 1

    # considering codec to compress the video stream as 0.25 bit per pixel
    codec_bpp = 0.25 # REF: https://arxiv.org/pdf/2408.12691

    # define list of resolutions
    resolution_list = ["1080p", "2K", "4K"]
    frame_rate_list = [30, 60, 120, 240]
    
    # define resolutions integer
    resolution_to_integer = {"1080p": 1, "2K": 2, "4K": 3}

    # define the size in pixel of the image based on its resolution
    pixel_size_list = resolution_pixel_size()
    
    # read input files
    CNs, GNBs, Games, Users, Paths, Links, Links_latency, Links_bandwidth = read_input_files(n_CNs, n_GNBs, n_users, timestamp)

    # get user's priority (quality or performance)
    users_priority = get_users_priority(Users, Games)

    # calculate PRBs request
    user_PRB_request = {}
    for user in Users:
        user_PRB_request[user.ID] = {}
        for gNB in GNBs:
            if user.my_SE(gNB.ID) > 0:
                user_PRB_request[user.ID][gNB.ID] = {}
                for res in resolution_list:
                    user_PRB_request[user.ID][gNB.ID][res] = {}
                    for fps in frame_rate_list:
                        user_PRB_request[user.ID][gNB.ID][res][fps] = calculate_user_PRB_request(user, gNB, res, fps, codec_bpp, (delta_max - user_routing_latency))

    # instantiate constraint programming model
    model = CpoModel()
    model.set_parameters(CpoParameters(LogPeriod=1000000) , TimeLimit=60*2)
    
    # define decision variable iterators
    gNBs_users = [(b.ID, u.ID) for b in GNBs for u in Users]
    
    resolution_user = []
    frame_rate_user = []
    for u in Users:
        resolution_user.append((u.ID, "1080p"))
        if u.my_max_resolution() in ["2K", "4K"]:
            resolution_user.append((u.ID, "2K"))
        if u.my_max_resolution() in ["4K"]:
            resolution_user.append((u.ID, "4K"))
                
        frame_rate_user.append((u.ID, 30))
        if u.my_max_frame_rate() >= 60:
            frame_rate_user.append((u.ID, 60))
        if u.my_max_frame_rate() >= 120:
            frame_rate_user.append((u.ID, 120))

    # decision variable that indicates if user u is associated to gNB b
    model.x = model.binary_var_dict(gNBs_users, name="gNBs_users")
    # decision variable that indicates if resolution r is selected to user u
    model.w = model.binary_var_dict(resolution_user, name="resolution_user")
    # decision variable that indicates if frame rate f is selected to user u
    model.z = model.binary_var_dict(frame_rate_user, name="frame_rate_user")
    # decision variable that indicates the load balance between multiple gNBs for each user u
    model.h = model.integer_var_dict(gNBs_users, name="load_balance")

    # objective function: Maximize users QoE based on resolution and frame rate selection - Webber Fatchner satisfaction logarithm function
    model.maximize(model.sum((users_priority[u.ID] * model.sum(model.w[i] * log(resolution_to_integer[i[1]]) for i in resolution_user if i[0] == u.ID)) +
                             ((1 - users_priority[u.ID]) * model.sum(model.z[j] * log(j[1]/30) for j in frame_rate_user if j[0] == u.ID)) for u in Users))

    # model.maximize(model.sum(model.x[gNB.ID, u.ID] for gNB in GNBs for u in Users))

    for user in Users:
        if users_priority[u.ID] == 1:
            model.add_constraint(model.z[u.ID, 30] == 1)
        else:
            model.add_constraint(model.w[u.ID, "1080p"] == 1)

    # each user may be connected to one or more gNBs (MULTI-CONNECTIVITY)
    for user in Users:
        model.add_constraint(model.sum(model.x[gNB.ID, user.ID] for gNB in GNBs if user.my_SE(gNB.ID) > 0) >= 1)
        model.add_constraint(model.sum(model.x[gNB.ID, user.ID] for gNB in GNBs if user.my_SE(gNB.ID) <= 0) == 0)
        
    # each user must be associated with a maximum number of gNBs - set to 4
    for user in Users:
        model.add_constraint(model.sum(model.x[gNB.ID, user.ID] for gNB in GNBs) <= 4)  # at most 4 gNBs per user

    # if a user is admitted by the gNB, than a positive amount (1% or higher) of its load must be transmitted by the gNB
    for i in gNBs_users:
        model.add_constraint(model.h[i] >= model.x[i])
    
    # each user may be associated with at most three gNB
    for user in Users:
        model.add_constraint(model.sum(model.x[gNB.ID, user.ID] for gNB in GNBs) <= 3)

    # if user is a user is not associated with the gNB, than it does not receive any data from the gNB, if it is associated, than it receives at most all (100%) of its load from the gNB
    for b in GNBs:
        for u in Users:
            model.add_constraint(model.x[b.ID, u.ID] * 100 >= model.h[b.ID, u.ID])
    
    # all trafic (100%) of a user must be transmitted by the gNB that it is associated
    for u in Users:
        model.add_constraint(model.sum(model.h[b.ID, u.ID] for b in GNBs) == 100)
    
    # exactly one resolution must be selected for each user
    for u in Users:
        model.add_constraint(model.sum(model.w[u.ID, r] for r in resolution_list if (u.ID, r) in resolution_user) == 1)
    
    # exactly one frame rate must be selected for each user
    for u in Users:
        model.add_constraint(model.sum(model.z[u.ID, f] for f in frame_rate_list if (u.ID, f) in frame_rate_user) == 1)
    
    # the user's requested PRBs must not exceed the gNB capacity
    for gNB in GNBs:
        model.add_constraint(model.sum(model.x[gNB.ID, u.ID] * model.w[u.ID, r] * model.ceil(user_PRB_request[u.ID][gNB.ID][r][f] * (model.h[gNB.ID, u.ID]/100)) * model.z[u.ID, f] for u in Users 
                                                                                                                                                 for r in resolution_list 
                                                                                                                                                 for f in frame_rate_list 
                                                                                                                                                     if (u.ID, f) in frame_rate_user
                                                                                                                                                 and (u.ID, r) in resolution_user
                                                                                                                                                 and u.my_SE(gNB.ID) > 0) <= gNB.my_number_PRBs() * n_TTIs)

    # print(gNB.my_number_PRBs() * n_TTIs)

    if os.path.exists('/opt/ibm/ILOG/CPLEX_Studio2211/cpoptimizer/bin/x86-64_linux/cpoptimizer'):
        execfile = '/opt/ibm/ILOG/CPLEX_Studio2211/cpoptimizer/bin/x86-64_linux/cpoptimizer'
    elif os.path.exists('/opt/ibm/ILOG/CPLEX_Studio221/cpoptimizer/bin/x86-64_linux/cpoptimizer'):
        execfile = '/opt/ibm/ILOG/CPLEX_Studio221/cpoptimizer/bin/x86-64_linux/cpoptimizer'
    elif os.path.exists('/opt/ibm/ILOG/CPLEX_Studio2211/cpoptimizer/bin/x86-64_linux/cpoptimizer'):
        execfile = '/opt/ibm/ILOG/CPLEX_Studio2211/cpoptimizer/bin/x86-64_linux/cpoptimizer'
    else:
        execfile = None

    start_time = time.time()
    msol = model.solve(agent='local', execfile=execfile)
    elapsed_time = time.time() - start_time

    solution_json = {"solution": {"Total_QoE": msol.get_objective_values()[0], "time": elapsed_time, "users": []}}

    solution_json["solution"]["users"] = []
    
    for user in Users:
        solution_json["solution"]["users"].append({})
        solution_json["solution"]["users"][user.ID]["serving_gNBs"] = []
        solution_json["solution"]["users"][user.ID]["Total_PRBs"] = 0
        solution_json["solution"]["users"][user.ID]["PRBs"] = {}
        solution_json["solution"]["users"][user.ID]["total_load"] = 0
        solution_json["solution"]["users"][user.ID]["load_to_gNB"] = {}
        solution_json["solution"]["users"][user.ID]["total_throughput"] = 0
        solution_json["solution"]["users"][user.ID]["throughput_to_gNB"] = {}
        solution_json["solution"]["users"][user.ID]["latency_to_gNB"] = {}
        solution_json["solution"]["users"][user.ID]["gNBs_PRBs"] = {}
        for gNB in GNBs:
            if msol[model.x[gNB.ID, user.ID]] == 1:
                solution_json["solution"]["users"][user.ID]["PRBs"][gNB.ID] = 0

    if msol:
        for i in gNBs_users:
            if msol[model.x[i]] == 1:
                # print("User {} is associated to gNB {} with traffic as {}".format(i[1], i[0], msol[model.h[i]]))
                solution_json["solution"]["users"][i[1]]["ID"] = i[1]
                solution_json["solution"]["users"][i[1]]["serving_gNBs"].append(i[0])
        for user in Users:
            for gNB in GNBs:
                for res in resolution_list: 
                    for fps in frame_rate_list:
                        if (user.ID, res) in resolution_user and (user.ID, fps) in frame_rate_user and msol[model.x[gNB.ID, user.ID]] == 1:
                            if msol[model.w[user.ID, res]] == 1 and msol[model.z[user.ID, fps]] == 1:
                                # print("User {} receives {} PRBs from gNB {}".format(user.ID, int(math.ceil(user_PRB_request[user.ID][gNB.ID][res][fps] * (msol[model.h[gNB.ID, user.ID]]/100))), gNB.ID))
                                solution_json["solution"]["users"][user.ID]["gNBs_PRBs"][gNB.ID] = int(math.ceil(user_PRB_request[user.ID][gNB.ID][res][fps] * (msol[model.h[gNB.ID, user.ID]]/100)))
                                solution_json["solution"]["users"][user.ID]["Total_PRBs"] += int(math.ceil(user_PRB_request[user.ID][gNB.ID][res][fps] * (msol[model.h[gNB.ID, user.ID]]/100)))
                                solution_json["solution"]["users"][user.ID]["total_load"] += (resolution_pixel_size()[res] * codec_bpp * fps) * (msol[model.h[gNB.ID, user.ID]]/100)
                                solution_json["solution"]["users"][user.ID]["total_throughput"] += user_PRB_request[user.ID][gNB.ID][res][fps] * (msol[model.h[gNB.ID, user.ID]]/100) * gNB.my_PRB_BW() * 10 ** 6 * user.my_SE(gNB.ID)
                                if gNB.ID in solution_json["solution"]["users"][user.ID]["PRBs"]:
                                    solution_json["solution"]["users"][user.ID]["PRBs"][gNB.ID] = int(math.ceil(user_PRB_request[user.ID][gNB.ID][res][fps] * (msol[model.h[gNB.ID, user.ID]]/100)))
                                    solution_json["solution"]["users"][user.ID]["load_to_gNB"][gNB.ID] = (resolution_pixel_size()[res] * codec_bpp * fps) * (msol[model.h[gNB.ID, user.ID]]/100)
                                    solution_json["solution"]["users"][user.ID]["throughput_to_gNB"][gNB.ID] = user_PRB_request[user.ID][gNB.ID][res][fps] * (msol[model.h[gNB.ID, user.ID]]/100) * gNB.my_PRB_BW() * 10 ** 6 * user.my_SE(gNB.ID)
                                    solution_json["solution"]["users"][user.ID]["latency_to_gNB"][gNB.ID] =  (solution_json["solution"]["users"][user.ID]["load_to_gNB"][gNB.ID]/solution_json["solution"]["users"][user.ID]["throughput_to_gNB"][gNB.ID]) + user_routing_latency
        for i in resolution_user:
            if msol[model.w[i]] == 1:
                # print("User {} resolution is {}".format(i[1], i[0]))
                solution_json["solution"]["users"][i[0]]["resolution"] = i[1]
        for i in frame_rate_user:
            if msol[model.z[i]] == 1:
                # print("User {} frame rate is {}".format(i[1], i[0]))
                solution_json["solution"]["users"][i[0]]["frame_rate"] = i[1]
        for u in Users:
            if users_priority[u.ID] == 1:
                solution_json["solution"]["users"][u.ID]["priority"] = "quality"
            else:
                solution_json["solution"]["users"][u.ID]["priority"] = "performance"
        # print("Objective function: {}".format(msol.get_objective_values()[0]))
        json.dump(solution_json, open("../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), "w"), indent=4)
        # print(elapsed_time)
    else:
        print("No solution found")

if __name__ == "__main__":
    n_CNs = int(sys.argv[1])
    n_GNBs = int(sys.argv[2])
    n_users = int(sys.argv[3])
    timestamps = 30
    numerology = 1
    for timestamp in range(0, timestamps):
        model(n_CNs, n_GNBs, n_users, numerology, timestamp)
    # model(n_CNs, n_GNBs, n_users, numerology, timestamp=0)
