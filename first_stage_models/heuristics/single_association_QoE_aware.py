from math import log2, log
import math
from methods import read_input_files
import os
import sys
import json
import time

def get_users_priority(Users, Games):
    users_priority = {}
    for u in Users:
        find = False
        for game in Games:
            if game.ID == u.my_game():
                find = True
                if game.game_type == "quality":
                    users_priority[u.my_ID()] = 1
                else:
                    users_priority[u.my_ID()] = 0
        if not find:
            print("Did not  find game for user {}: {}".format(u.my_ID(), u.my_game()))
            time.sleep(2)
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

def heuristic(n_CNs, n_GNBs, n_users, numerology, timestamp):
    
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

    # list of users served by each gNB
    gNBs_association = {}

    # list of users associated with a gNB
    users_associated_gNBs = {}

    # users selected resolution
    users_selected_resolution = {}

    # users selected frame rate
    users_selected_frame_rate = {}

    # Initialize users selected resolution and frame rate with zero/none values
    for user in Users:
        users_selected_resolution[user.my_ID()] = "None"
        users_selected_frame_rate[user.my_ID()] = 0  

    # availale PRBs of each gNB
    gNBs_available_PRBs = {}
    for gNB in GNBs:
        gNBs_available_PRBs[gNB.ID] = gNB.my_number_PRBs() * n_TTIs
    
    # users desired resolution and frame rate
    users_max_resolution = {}
    users_max_frame_rate = {}
    for user in Users:
        if users_priority[user.my_ID()] == 1:
            users_max_resolution[user.my_ID()] = user.my_max_resolution()
            users_max_frame_rate[user.my_ID()] = 30
        else:
            users_max_resolution[user.my_ID()] = "1080p"
            users_max_frame_rate[user.my_ID()] = user.my_max_frame_rate()

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
                        user_PRB_request[user.ID][gNB.ID][res][fps] = calculate_user_PRB_request(user, gNB, res, fps, codec_bpp, (delta_max - user_routing_latency))#  * 2

    # list that store the prefererd gNB of each user to the association based on its channel quality
    users_preference_list = {}
    for user in Users:
        users_preference_list[user.my_ID()] = []
        user_channel_quality = {}
        for gnb in GNBs:
            user_channel_quality[gnb.my_ID()] = user.my_SE(gnb.my_ID())
        # sort the gNBs based on the channel quality
        sorted_gNBs = sorted(user_channel_quality.items(), key=lambda x: x[1], reverse=True)
        for i in sorted_gNBs:
            users_preference_list[user.my_ID()].append(i[0])

    # list that store the prefererd user of each gNB to the association based on its channel quality
    gNBs_preference_list = {}
    for gnb in GNBs:
        gNBs_preference_list[gnb.my_ID()] = []
        gNB_channel_quality = {}
        for user in Users:
            gNB_channel_quality[user.my_ID()] = user.my_SE(gnb.my_ID())
        # sort the users based on the channel quality
        sorted_users = sorted(gNB_channel_quality.items(), key=lambda x: x[1], reverse=True)
        for i in sorted_users:
            gNBs_preference_list[gnb.my_ID()].append(i[0])
    
    elapsed_time = time.time()
    # While any user is not associated with a gNB it will try to associate with the gNB that has higher preference
    while len(users_associated_gNBs) < len(Users):
        for user in Users:
            # creates a temporary representation of the gNBs available PRBs
            tmp_gNBs_available_PRBs = gNBs_available_PRBs.copy()
            # if the user is associated with any gNB, it checks if it reaches the maximum number of connections (in this case 3). If it do not, it will try to associate with the gNB that has higher preference
            if user.my_ID() in users_associated_gNBs.keys():
                # if the user is associated with 3 gNBs, it will not try to associate with any other gNB
                if len(users_associated_gNBs[user.my_ID()]) == 1:
                    continue
            else:
                users_associated_gNBs[user.my_ID()] = []
            # try to associate with the gNB that has higher preference
            for gnb in users_preference_list[user.my_ID()]:
                if len(users_associated_gNBs[user.my_ID()]) == 1:
                    continue
                if int(math.ceil(user_PRB_request[user.my_ID()][gnb]["1080p"][30]/max(1, len(users_associated_gNBs[user.my_ID()])))) <= tmp_gNBs_available_PRBs[gnb]:
                        # update user selected resolution and frame rate
                        users_selected_resolution[user.my_ID()] = "1080p"
                        users_selected_frame_rate[user.my_ID()] = 30
                        # remove the PRBs from the gNB
                        tmp_gNBs_available_PRBs[gnb] -= int(math.ceil(user_PRB_request[user.my_ID()][gnb]["1080p"][30]/max(1, len(users_associated_gNBs[user.my_ID()]))))
                        # associate the user with the gNB
                        users_associated_gNBs[user.my_ID()].append(gnb)
                        # remove the gNB from the preference list of the user
                        users_preference_list[user.my_ID()].remove(gnb)
                        # add the user to the gNB association list
                        if gnb in gNBs_association.keys():
                            gNBs_association[gnb].append(user.my_ID())
                        else:
                            gNBs_association[gnb] = [user.my_ID()]
                # if the gNB does not have enough PRBs to serve the user, it will check if the user has a higher priority than the users already associated with the gNB
                else:
                    # check if the new user has a higher priority than the old users already associated with the gNB
                    for u in gNBs_association[gnb]:
                        if users_priority[user.my_ID()] > users_priority[u]:
                            # check if the gNB has enough PRBs to serve the new user considering the minimum resolution and frame rate, i.e. 1080p and 30 fps
                            if int(math.ceil(user_PRB_request[user.my_ID()][gnb]["1080p"][30]/max(1, len(users_associated_gNBs[user.my_ID()])))) <= tmp_gNBs_available_PRBs[gnb] + int(math.ceil(user_PRB_request[u][gnb]["1080p"][30]/max(1, len(users_associated_gNBs[u])))):
                                # update the available PRBs of the gNB
                                tmp_gNBs_available_PRBs[gnb] += int(math.ceil(user_PRB_request[u][gnb]["1080p"][30]/max(1, len(users_associated_gNBs[u])))) - int(math.ceil(user_PRB_request[user.my_ID()][gnb]["1080p"][30]/max(1, len(users_associated_gNBs[user.my_ID()]))))
                                # remove the old user from the gNB association list
                                gNBs_association[gnb].remove(u)
                                # add the new user to the gNB association list
                                gNBs_association[gnb].append(user.my_ID())
                                if gnb in users_preference_list[user.my_ID()]:
                                    # remove the gNB from the preference list of the new user
                                    users_preference_list[user.my_ID()].remove(gnb)
                                # remove the gNB from the association list of the old user
                                users_associated_gNBs[u].remove(gnb)
                                # add the gNB to the association list of the new user
                                if user.my_ID() in users_associated_gNBs.keys():
                                    users_associated_gNBs[user.my_ID()].append(gnb)
                                else:
                                    users_associated_gNBs[user.my_ID()] = [gnb]
            # update the available PRBs of the gNBs
            for gNB in users_associated_gNBs[user.my_ID()]:
                # update the available PRBs of the gNB considering the selected resolution and frame rate
                gNBs_available_PRBs[gNB] = gNBs_available_PRBs[gNB] - int(math.ceil(user_PRB_request[user.my_ID()][gnb]["1080p"][30]/max(1, len(users_associated_gNBs[user.my_ID()]))))
        # list with users utility - used to decide which user should be prioritized to improve its QoE
        users_utility = {}
        # list of users ID sorted by utility
        users_sorted_by_utility = []
        
        # calculate the utility of each user based on the current resolution and frame rate selection and with the desired resolution and frame rate
        for user in Users:
            if users_selected_frame_rate[user.my_ID()] > 0 and users_selected_resolution[user.my_ID()] != "None":
                user_desired_QoE = (users_priority[user.my_ID()] * log2(resolution_to_integer[users_max_resolution[user.my_ID()]])) + ((1 - users_priority[user.my_ID()]) * log2(users_max_frame_rate[user.my_ID()]/30))
                user_current_QoE = (users_priority[user.my_ID()] * log2(resolution_to_integer[users_selected_resolution[user.my_ID()]]) + ((1 - users_priority[user.my_ID()]) * log2(users_selected_frame_rate[user.my_ID()]/30)))
                users_utility[user.my_ID()] = user_desired_QoE - user_current_QoE
                users_sorted_by_utility.append(user.my_ID())
        users_sorted_by_utility = sorted(users_sorted_by_utility, key=lambda x: users_utility[x], reverse=True)

        while True:
            changed_any_user = False
            i = 0
            while i < len(users_sorted_by_utility):
                user = users_sorted_by_utility[i]
                # select the next desired resolution and frame rate
                if users_priority[user] == 1:
                    desired_frame_rate = 30
                    # select the next desired resolution and frame rate
                    if users_selected_resolution[user] == "1080p" and users_max_resolution[user] in ["2K", "4K"]:
                        desired_resolution = "2K"
                    elif users_selected_resolution[user] == "2K" and users_max_resolution[user] in ["4K"]:
                        desired_resolution = "4K"
                    else:
                        desired_resolution = users_selected_resolution[user]
                else:
                    desired_resolution = "1080p"
                    # select the next desired resolution and frame rate
                    if users_selected_frame_rate[user] == 30 and 30 < users_max_frame_rate[user] <= 60:
                        desired_frame_rate = 60
                    elif users_selected_frame_rate[user] == 60 and 60 < users_max_frame_rate[user] <= 120:
                        desired_frame_rate = 120
                    elif users_selected_frame_rate[user] == 120 and 120 < users_max_frame_rate[user]:
                        desired_frame_rate = users_max_frame_rate[user]
                    else:
                        desired_frame_rate = 30

                # verify if the user has already selected the desired resolution and frame rate
                if desired_resolution == users_selected_resolution[user] and desired_frame_rate == users_selected_frame_rate[user]:
                    i += 1
                    continue
                # if it do not receive the desired resolution and frame rate, it will try to increase the resolution and frame rate based on watter-filling algorithm
                else:
                    # Boolean variable that represent if it is possible to serve the user with the desired resolution and frame rate
                    is_it_possible = True
                    for gnb in users_associated_gNBs[user]:
                        # check if the gNB has enough PRBs to serve the user with the desired resolution and frame rate
                        if user_PRB_request[user][gnb][desired_resolution][desired_frame_rate]/max(1, len(users_associated_gNBs[user])) > gNBs_available_PRBs[gnb]:
                            is_it_possible = False
                            i += 1
                    if is_it_possible:
                        changed_any_user = True
                        # update the user selected resolution and frame rate
                        users_selected_resolution[user] = desired_resolution
                        users_selected_frame_rate[user] = desired_frame_rate
                        # remove the PRBs from the gNB
                        for gnb in users_associated_gNBs[user]:
                            # update the available PRBs of the gNB considering the selected resolution and frame rate
                            gNBs_available_PRBs[gnb] = gNBs_available_PRBs[gnb] - user_PRB_request[user][gnb][desired_resolution][desired_frame_rate]/max(1, len(users_associated_gNBs[user]))
                        # update the user utility
                        user_desired_QoE = (users_priority[user] * log2(resolution_to_integer[users_max_resolution[user]])) + ((1 - users_priority[user]) * log2(users_max_frame_rate[user]/30))
                        user_current_QoE = (users_priority[user] * log2(resolution_to_integer[users_selected_resolution[user]]) + ((1 - users_priority[user]) * log2(users_selected_frame_rate[user]/30)))
                        users_utility[user] = user_desired_QoE - user_current_QoE
                        # update the list of users sorted by utility
                        users_sorted_by_utility = sorted(users_sorted_by_utility, key=lambda x: users_utility[x], reverse=True)
            
            # if it has being checked for all users and none of the users update its resolution and frame rate, then break the loop
            if not changed_any_user:
                break
            # if all users has utility equal to 0, it means that all users are receiving the maximum resolution and frame rate, then break the loop
            if all(value == 0 for value in users_utility.values()):
                break

    elapsed_time = time.time() - elapsed_time

    total_QoE = 0
    users_QoE = {}

    print(users_priority)

    for user in users_priority:
        if users_priority[user] == 1:
            users_QoE[user] = math.log(resolution_to_integer[users_selected_resolution[user]])
            print("User {} selected resolution {} with frame rate {} and QoE {}".format(user, users_selected_resolution[user], users_selected_frame_rate[user], users_QoE[user]))
            total_QoE += users_QoE[user]

        else:
            users_QoE[user] = math.log(users_selected_frame_rate[user]/30)
            print("User {} selected resolution {} with frame rate {} and QoE {}".format(user, users_selected_resolution[user], users_selected_frame_rate[user], users_QoE[user]))
            total_QoE += users_QoE[user]

    solution_json = {"solution": {"Total_QoE": total_QoE, "time": elapsed_time, "users": [users_QoE[u.ID] for u in Users]}}
    
    json.dump(solution_json, open("../../solutions/first_stage/single_association_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), "w"), indent=4)

    return elapsed_time
    total_QoE = 0

    for user in users_selected_resolution:
        if users_selected_resolution[user] != "None" and users_selected_frame_rate[user] > 0:
            total_QoE += users_priority[user] * (math.log(resolution_to_integer[users_selected_resolution[user]])) + (1 - users_priority[user]) * (math.log(users_selected_frame_rate[user]/30))

    solution_json = {"solution": {"Total_QoE": total_QoE, "time": elapsed_time, "users": []}}

    solution_json["solution"]["users"] = []

    selected_resolutions = {}
    for user in Users:
        if users_selected_resolution[user.ID] not in selected_resolutions:
            selected_resolutions[users_selected_resolution[user.ID]] = 0
        selected_resolutions[users_selected_resolution[user.ID]] += 1
    
    for resolution in selected_resolutions:
        print("Resolution {} is selected by {} users".format(resolution, selected_resolutions[resolution]))
    
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
        for gNB in GNBs:
            if gNB.ID in users_associated_gNBs[user.ID]:
                solution_json["solution"]["users"][user.ID]["PRBs"][gNB.ID] = 0
    
    for user in Users:
        if users_selected_frame_rate[user.ID] > 0 and users_selected_resolution[user.ID] != "None":
            for gNB in users_associated_gNBs[user.ID]:
                # print("User {} is associated to gNB {} with traffic as {}".format(user.ID, gNB, 1/len(users_associated_gNBs[user.ID])))
                solution_json["solution"]["users"][user.ID]["ID"] = user.ID
                solution_json["solution"]["users"][user.ID]["serving_gNBs"].append(gNB)
                user_nPRBs = int(math.ceil(user_PRB_request[user.ID][gnb][users_selected_resolution[user.ID]][users_selected_frame_rate[user.ID]]/max(1, len(users_associated_gNBs[user.ID]))))
                # print("User {} receives {} PRBs from gNB {}".format(user.ID, user_nPRBs, gNB))
                solution_json["solution"]["users"][user.ID]["Total_PRBs"] += user_nPRBs
                solution_json["solution"]["users"][user.ID]["load_to_gNB"][gNB] = (resolution_pixel_size()[users_selected_resolution[user.ID]] * users_selected_frame_rate[user.ID] * codec_bpp)/max(1, len(users_associated_gNBs[user.ID]))
                solution_json["solution"]["users"][user.ID]["total_load"] += (user_nPRBs * GNBs[gNB - 1].my_PRB_BW() * 10 ** 6 * user.my_SE(gNB)) * users_selected_frame_rate[user.ID] * (1/max(1, len(users_associated_gNBs[user.ID])))
                solution_json["solution"]["users"][user.ID]["total_throughput"] += user_nPRBs * GNBs[gNB - 1].my_PRB_BW() * 10 ** 6 * user.my_SE(gNB)
                if gNB in solution_json["solution"]["users"][user.ID]["PRBs"]:
                    solution_json["solution"]["users"][user.ID]["PRBs"][gNB] = user_nPRBs
                    solution_json["solution"]["users"][user.ID]["throughput_to_gNB"][gNB] = user_nPRBs * GNBs[gNB - 1].my_PRB_BW() * 10 ** 6 * user.my_SE(gNB)
                    solution_json["solution"]["users"][user.ID]["latency_to_gNB"][gNB] = (solution_json["solution"]["users"][user.ID]["load_to_gNB"][gNB]/solution_json["solution"]["users"][user.ID]["throughput_to_gNB"][gNB]) + user_routing_latency
            
            solution_json["solution"]["users"][user.ID]["resolution"] = users_selected_resolution[user.ID]
            solution_json["solution"]["users"][user.ID]["frame_rate"] = users_selected_frame_rate[user.ID]
            if users_priority[user.ID] == 1:
                solution_json["solution"]["users"][user.ID]["priority"] = "quality"
            else:
                solution_json["solution"]["users"][user.ID]["priority"] = "performance"
    
    json.dump(solution_json, open("../../solutions/first_stage/single_association_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), "w"), indent=4)

if __name__ == "__main__":
    n_CNs = int(sys.argv[1])
    n_GNBs = int(sys.argv[2])
    n_users = int(sys.argv[3])
    numerology = 1
    run_times = {}
    for run in range(1):
        for timestamp in range(0, 1):
            progress = (run * 100 + timestamp + 1) / (30 * 100)
            bar_length = 40
            filled_length = int(bar_length * progress)
            bar = '=' * filled_length + '-' * (bar_length - filled_length)
            print(f"\rProgress: |{bar}| {progress*100:.2f}% (Run {run+1}/30, Timestamp {timestamp+1}/100)", end='', flush=True)
            if timestamp not in run_times.keys():
                run_times[timestamp] = 0
            elapsed_time = heuristic(n_CNs, n_GNBs, n_users, numerology, timestamp=timestamp)
            run_times[timestamp] += elapsed_time
    for timestamp in run_times.keys():
        run_times[timestamp] /= 30
    
    # json.dump(open("../../solutions/first_stage/single_association_model/time.json", 'w'), run_times, indent=4)
    