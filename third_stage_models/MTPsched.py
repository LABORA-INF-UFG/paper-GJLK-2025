import time
from math import ceil, floor

def MTPsched(GNBs, users_served_PRBs_gNB, TTIs, number_of_time_blocks):
    # defining the number of time blocks | 40 time blocks of ~ 50 TTIs each
    number_of_time_blocks = 40
    # initializing the users_offered_PRBs_gNB - this stores the number of PRBs offered to each user by each gNB and starts with 0s
    users_offered_PRBs_gNB = {}
    for user in users_served_PRBs_gNB:
        users_offered_PRBs_gNB[user] = {str(gNB): 0 for gNB in users_served_PRBs_gNB[user]}
    # defining the set of time_blocks limits - it means the TTI it starts and ends in each time block
    time_block_limits = {}
    # defines the next TTI free in each time block of each gNB - if all PRBs of a gNB is used in a TTI, it is not free anymore
    next_TTI_free_in_TB_of_gNB = {}
    # calculate the limits of each time block - TTI start and TTI end
    for i in range(number_of_time_blocks):
        time_block_limits[i] = (i * len(TTIs) // number_of_time_blocks, (i + 1) * len(TTIs) // number_of_time_blocks)
    # initialize the next TTI free in each time block of each gNB - in this time is all first TTI in each TTI block
    for gNB in GNBs:
        next_TTI_free_in_TB_of_gNB[str(gNB.ID)] = {i: time_block_limits[i][0] for i in range(number_of_time_blocks)}
    # represent the gNB spectrum indicating which user receive PRBs in each TTI in each gNB - starts with 0s
    gNB_spectrum = {}
    for gNB in GNBs:
        gNB_spectrum[str(gNB.ID)] = [[] for _ in range(0, len(TTIs))]
    
    gNB_used_PRBs = {str(gNB.ID): 0 for gNB in GNBs}

    for user in users_served_PRBs_gNB:
        # calculate the amount of PRBs allocated to the user by each gNB
        user_total_PRBs = sum(users_served_PRBs_gNB[user].values())
        
        # calculate the amount of time blocks the user will be receiving PRBs
        if user_total_PRBs >= number_of_time_blocks:
            user_time_blocks = number_of_time_blocks
        else:
            user_time_blocks = user_total_PRBs

        # calculate the number of PRBs allocated in each time block
        for timeblock in range(number_of_time_blocks):
            for gNB in GNBs:
                if str(gNB.ID) not in users_served_PRBs_gNB[user]:
                    continue
                # calculate the amount of PRBs to be allocated in each time block
                user_number_of_PRBs_per_TB = ceil(user_total_PRBs / user_time_blocks)
                # if the number of PRBs to be allocated in the timeblock will exceed the number of PRBs to be allocated to the user, we fix it to be the remaining PRBs
                if users_served_PRBs_gNB[user][str(gNB.ID)] - users_offered_PRBs_gNB[user][str(gNB.ID)] < user_number_of_PRBs_per_TB:
                    user_number_of_PRBs_per_TB = users_served_PRBs_gNB[user][str(gNB.ID)] - users_offered_PRBs_gNB[user][str(gNB.ID)]
                # starting the PRB allocation process
                for _ in range(user_number_of_PRBs_per_TB):
                    # take the next TTI free in the time block of the gNB
                    tti = next_TTI_free_in_TB_of_gNB[str(gNB.ID)][timeblock]
                    # if the TTI is valid, allocate ONE PRB at this TTI to the user
                    if tti != -1 and tti < len(TTIs):
                        # verify if the gNB has available PRBs in the selected TTI - if it has, allocate the PRB
                        if len(gNB_spectrum[str(gNB.ID)][tti]) <= gNB.my_number_PRBs() - 1:
                            gNB_spectrum[str(gNB.ID)][tti].append(user)
                            users_offered_PRBs_gNB[user][str(gNB.ID)] += 1
                            gNB_used_PRBs[str(gNB.ID)] += 1
                        if tti + 1 < time_block_limits[timeblock][1]:
                            if len(gNB_spectrum[str(gNB.ID)][tti]) == gNB.my_number_PRBs() - 1:
                                next_TTI_free_in_TB_of_gNB[str(gNB.ID)][timeblock] = tti + 1
                        else:
                            next_TTI_free_in_TB_of_gNB[str(gNB.ID)][timeblock] = -1
                    else:
                        # Find the next available TTI across all time blocks for this gNB
                        allocated = False
                        tti_candidate = 0
                        while tti_candidate < len(TTIs) and not allocated:
                            if len(gNB_spectrum[str(gNB.ID)][tti_candidate]) < gNB.my_number_PRBs() - 1:
                                gNB_spectrum[str(gNB.ID)][tti_candidate].append(user)
                                users_offered_PRBs_gNB[user][str(gNB.ID)] += 1
                                # next_TTI_free_in_TB_of_gNB[str(gNB.ID)][timeblock] = tti_candidate + 1
                                gNB_used_PRBs[str(gNB.ID)] += 1
                                allocated = True
                            tti_candidate += 1
                            if tti_candidate >= len(TTIs):
                                break
                        if not allocated:
                            # Could not allocate PRB for this user/gNB in any time block
                            print("gNB {} is using {} PRBs, but could not allocate PRB for user {} in any time block".format(gNB.ID, gNB_used_PRBs[str(gNB.ID)], user))
                            print(gNB.my_number_PRBs() * len(TTIs))
                            pass
    for user in users_served_PRBs_gNB:
        print("User {} received {} PRBs of {} PRBs defined".format(user, sum(users_offered_PRBs_gNB[user].values()), sum(users_served_PRBs_gNB[user].values())))
    # this only appears if there is an error in the allocation process - a user received less PRBs than it was supposed to receive (offered PRBs < served PRBs)
    for user in users_served_PRBs_gNB:
        for gNB in users_served_PRBs_gNB[user]:
            if users_offered_PRBs_gNB[user][gNB] < users_served_PRBs_gNB[user][gNB]:
                print("User {} not allocated all PRBs on gNB {}".format(user, gNB))
                print("Offered: {}, Served: {}".format(users_offered_PRBs_gNB[user][gNB], users_served_PRBs_gNB[user][gNB]))
                # time.sleep(100)
    
    # calculate the max MTP latency based on the PRB schedule process - the higher sequence of TTIs that the user do not receive PRBs - consequently do not receive video frames nether
    print("Calculating the MTP latency based on the gNB spectrum allocation to each user")
    users_MTP_latency = {}
    for user in users_served_PRBs_gNB:
        user_TTI_list = [0 for _ in range(len(TTIs))]
        for gNB in users_served_PRBs_gNB[user]:
            for i in range(len(gNB_spectrum[gNB])):
                if user in gNB_spectrum[gNB][i]:
                    user_TTI_list[i] = 1
        max_gap = 0
        current_gap = 0
        in_ones = False
        for val in user_TTI_list:
            if val == 1:
                if in_ones:
                    if current_gap > max_gap:
                        max_gap = current_gap
                    current_gap = 0
                else:
                    in_ones = True
            elif in_ones:
                current_gap += 1
        print(f"User {user}: Max. MTP-latency is {max_gap * 0.5} miliseconds - Received {users_offered_PRBs_gNB[user]} PRBs of {users_served_PRBs_gNB[user]} PRBs")
        users_MTP_latency[user] = max_gap * 0.5  # Assuming each TTI is 0.5 ms
    print("Users average MTP latency: {}".format(sum(users_MTP_latency.values()) / len(users_MTP_latency)))
    
    return users_offered_PRBs_gNB, users_MTP_latency, gNB_spectrum