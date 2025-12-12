from typing import List, Dict
from collections import defaultdict
from methods import read_input_files
import json
import sys

def served_PRBs(Users, sol):
    users_served_PRBs_gNB = {}

    for user in Users:
        for u in sol["solution"]["users"]:
            if u["ID"] == user.my_ID():
                users_served_PRBs_gNB[user.my_ID()] = {}
                for gNB in u["load_to_gNB"]:
                    if "gNB_PRBs" in u:
                        users_served_PRBs_gNB[user.my_ID()][gNB] = u["gNB_PRBs"][gNB]
                    else:
                        users_served_PRBs_gNB[user.my_ID()][gNB] = u["gNBs_PRBs"][gNB]

    return users_served_PRBs_gNB

def proportional_fair_allocation(users, total_PRBs: int, users_served_PRBs_gNB, num_TTIs=2000):
    """
    Distribute PRBs to users per gNB using the proportional fair algorithm over multiple TTIs.
    Returns a dict: {gNB: {user_ID: allocated_PRBs}}, and a dict: {user_ID: max_sequential_no_PRB_TTIs}
    """
    allocation = defaultdict(lambda: defaultdict(int))

    # For each gNB, get users connected to it
    gNB_users = defaultdict(list)
    for user in users:
        user_id = user.my_ID()
        if user_id in users_served_PRBs_gNB:
            for gNB in users_served_PRBs_gNB[user_id]:
                gNB_users[gNB].append(user)

    prbs_per_gNB = total_PRBs // max(1, len(gNB_users))

    # Initialize past throughput for PF for each user per gNB
    past_throughput = {gNB: {user: 1e-6 for user in gnb_users} for gNB, gnb_users in gNB_users.items()}

    # Track sequential TTIs without PRB for each user
    user_no_PRB_streak = {user.my_ID(): 0 for user in users}
    user_max_no_PRB_streak = {user.my_ID(): 0 for user in users}
    user_last_PRB = {user.my_ID(): False for user in users}

    for tti in range(num_TTIs):
        # Track which users get PRB in this TTI
        users_got_PRB = {user.my_ID(): False for user in users}
        for gNB, gnb_users in gNB_users.items():
            for _ in range(prbs_per_gNB):
                pf_metric = {user: user.my_SE(gNB) / past_throughput[gNB][user] for user in gnb_users}
                selected_user = max(pf_metric, key=pf_metric.get)
                allocation[gNB][selected_user.my_ID()] += 1
                past_throughput[gNB][selected_user] += selected_user.my_SE(gNB)
                users_got_PRB[selected_user.my_ID()] = True

        # Update streaks
        for user in users:
            uid = user.my_ID()
            if users_got_PRB[uid]:
                user_no_PRB_streak[uid] = 0
            else:
                user_no_PRB_streak[uid] += 1
                if user_no_PRB_streak[uid] > user_max_no_PRB_streak[uid]:
                    user_max_no_PRB_streak[uid] = user_no_PRB_streak[uid]

    return allocation, user_max_no_PRB_streak

def main(n_CNs, n_GNBs, n_users, timestamp, total_PRBs):
    # Read input files
    CNs, GNBs, Games, Users, Paths, Links, Links_latency, Links_bandwidth = read_input_files(n_CNs, n_GNBs, n_users, timestamp)
    
    if n_users <= 400:
        sol = json.load(open("../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))
    else:
        sol = json.load(open("../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))
    users_served_PRBs_gNB = served_PRBs(Users, sol)

    # Allocate PRBs using proportional fair algorithm
    prb_allocation, user_max_no_PRB_streak = proportional_fair_allocation(Users, total_PRBs, users_served_PRBs_gNB)

    # Example: print allocation
    # for gNB, prbs in prb_allocation.items():
        # print(f"gNB {gNB}: {prbs}")

    # print("\nMax sequential TTIs without PRB for each user:")
    # for user_id, max_streak in user_max_no_PRB_streak.items():
        # print(f"User {user_id}: {max_streak} TTIs")
    avg_streak = sum(user_max_no_PRB_streak.values()) / len(user_max_no_PRB_streak) if user_max_no_PRB_streak else 0
    # print(f"\nAverage max sequential TTIs without PRB: {avg_streak:.2f}")

    # Print latency for each user (TTIs * 0.5 ms)
    # print("\nMax sequential latency without PRB for each user (ms):")
    for user_id, max_streak in user_max_no_PRB_streak.items():
        latency_ms = max_streak * 0.5
        # print(f"User {user_id}: {latency_ms:.2f} ms")

    avg_latency = avg_streak * 0.5
    # print(f"\nAverage max sequential latency without PRB: {avg_latency:.2f} ms")
    return avg_latency

# Example usage:
if __name__ == "__main__":
    avg_latency_values = []
    for n_users in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]:
        print(f"Running for {n_users} users...")
        avg_latency_values.append(main(n_CNs=10, n_GNBs=10, n_users=n_users, timestamp=0, total_PRBs=16))
    print("Average latencies for different user counts:", avg_latency_values)