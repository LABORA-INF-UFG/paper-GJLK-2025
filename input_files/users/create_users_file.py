import json
import sys
import random
import pandas as pd
import math

random.seed(42)

def create_users_file(n_gNBs, games_df, n_users, hmds_df, cqi_df, users_distance):
    json_dict = {"users": []}
    games = {}

    for i in range(n_users):
        select_user_game = random.choices(
            games_df["appid"], 
            weights=games_df["userPercentage"], 
            k=1
        )[0]
        competitive = games_df[games_df["appid"] == select_user_game]["competitive"].values[0]
        
        if competitive == "No":
            game_type = "quality"
        else:
            game_type = "performance"
        
        if select_user_game not in games:
            games[select_user_game] = {
                "ID": int(select_user_game),
                "CPU_requirement": random.choice([1000, 2000, 4000]),
                "RAM_requirement": random.choice([3, 8, 16]),
                "game_type": game_type
            }

        select_user_hmd = random.choices(
            hmds_df["Headset"], 
            weights=hmds_df["User-percentage"], 
            k=1
        )[0]
        
        resolution = hmds_df[hmds_df["Headset"] == select_user_hmd]["Per-eye-resolution"].values[0]
        if resolution in ["1080x1200", "960x1080"]:
            resolution = "1080p"
        elif resolution in ["1832x1920", "2064x2208", "1440x1600", "1280x1440", "2000x2040", "1800x1920", "1920x1920", "1440x1700", "2048x2160"]:
            resolution = "2K"
        elif resolution in ["2160x2160", "2448x2448", "2560x2560", "2880x2720"]:
            resolution = "4K"
        
        frame_rate = hmds_df[hmds_df["Headset"] == select_user_hmd]["Refresh-rate"].values[0]

        se = {}
        for j in range(n_gNBs):
            user_distance = users_distance[i][j]
            # Calculate Path Loss using Urban Micro PL formula
            if user_distance > 0:
                path_loss = 32.4 + 21 * math.log10(user_distance) + 20 * math.log10(3.5) + 63
                Noise = -174 + 10 * math.log10(100*10**6)
                SNR = 30 - path_loss - Noise
            if int(SNR) >= 20:
                CQI = 12                   # MCS: 256QAM = 5.5547 bit/Hz
            elif int(SNR) >= 18:
                CQI = 11                   # MCS: 64QAM = 5.1152 bit/Hz
            elif int(SNR) >= 16:
                CQI = 10                   # MCS: 64QAM = 4.5234 bit/Hz
            elif int(SNR) >= 14:
                CQI = 9                    # MCS: 64QAM = 3.9023 bit/Hz
            elif int(SNR) >= 12:
                CQI = 8                    # MCS: 64QAM = 3.3223 bit/Hz
            elif int(SNR) >= 10:
                CQI = 7                    # MCS: 64QAM = 2.7305 bit/Hz
            elif int(SNR) >= 8:
                CQI = 6                    # MCS: 16QAM = 2.4063 bit/Hz
            elif int(SNR) >= 6:
                CQI = 5                    # MCS: 16QAM = 1.9141 bit/Hz
            elif int(SNR) >= 4:
                CQI = 4                    # MCS: 16QAM = 1.4766 bit/Hz
            elif int(SNR) >= 2:
                CQI = 3                    # MCS: QPSK = 0.8770 bit/Hz
            elif int(SNR) >= 0:
                CQI = 2                    # MCS: QPSK = 0.3770 bit/Hz
            else:
                CQI = 1                    # MCS: QPSK = 0.1523 bit/Hz
            select_user_cqi = CQI
            efficiency = cqi_df[cqi_df["cqi"] == select_user_cqi]["efficiency"].values[0]
            se[j+1] = efficiency
        
        json_dict["users"].append({
            "ID": int(i),
            "SE": se,
            "game": int(select_user_game),
            "game_instance": i,
            "max_resolution": resolution,
            "max_frame_rate": int(frame_rate)
        })
    
    json_games = {"games": [games[i] for i in games.keys()]}
    
    return json_dict, json_games

def take_games_df():
    games_df = pd.read_csv(open("../vrGames.csv"))
    return games_df

def take_HMDs_df():
    # https://www.etsi.org/deliver/etsi_ts/136200_136299/136213/18.03.00_60/ts_136213v180300p.pdf - - Table 7.2.3-2: 4-bit CQI Table 2 (VALUES FOR CQI AND EFFICIENCY)
    hmds_df = pd.read_csv(open("../vrHeadsets.csv"))
    return hmds_df

def take_CQI_df():
    cqi_df = pd.read_csv(open("../CQI_map.csv"))
    return cqi_df


if __name__ == "__main__":
    n_gNBs = int(sys.argv[1])
    n_users = int(sys.argv[2])
    
    games_df = take_games_df()

    hmds_df = take_HMDs_df() 

    cqi_df = take_CQI_df()

    users_distance_df = pd.read_csv(open("usersDistances.csv"))
    users_distance = {}
    
    for timestamp in [9]:
        user_ID = 0
        print("Number of users: {}".format(users_distance_df["UserID"].nunique()))
        print("Number of TTIs: {}".format(users_distance_df["Timestamp"].nunique()))
        df_timestamp = users_distance_df[users_distance_df["Timestamp"] == timestamp]
        for user in df_timestamp["UserID"].unique():
            subframe_user = users_distance_df[(users_distance_df["UserID"] == user) & (users_distance_df["Timestamp"] == timestamp)]
            users_distance[user_ID] = {}
            for gNB in range(n_gNBs):
                if not subframe_user.empty:
                    distance = subframe_user["Distance_to_Node_{}".format(gNB)].values[0]
                users_distance[user_ID][gNB] = float(distance)
            user_ID += 1
        
        json_obj, json_games = create_users_file(n_gNBs, games_df, n_users, hmds_df, cqi_df, users_distance)
    
        json.dump(json_obj, open("{}_gNBs/{}_users_timestamp_0.json".format(n_gNBs, n_users, timestamp), "w"), indent=4)
        json.dump(json_games, open("../games/{}_users_games_timestamp_0.json".format(n_users, timestamp), "w"), indent=4)