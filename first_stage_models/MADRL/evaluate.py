env = MultiAgentVRGameEnv()
obs = env.reset()
done = {"__all__": False}
while not done["__all__"]:
    actions = {
        "agent_res": algo.get_policy("agent_res").compute_single_action(obs["agent_res"]),
        "agent_assoc": algo.get_policy("agent_assoc").compute_single_action(obs["agent_assoc"]),
    }
    obs, rewards, done, info = env.step(actions)
    print(f"Rewards: {rewards}")
