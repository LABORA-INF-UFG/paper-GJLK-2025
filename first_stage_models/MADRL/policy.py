#from ray.rllib.env import multi_vr_env as MultiAgentVRGameEnv
from VR_CG_env import MultiAgentVRGameEnv

policies = {
    "agent_res": (None, MultiAgentVRGameEnv({}).observation_spaces["agent_res"], 
                         MultiAgentVRGameEnv({}).action_spaces["agent_res"], {}),
    "agent_assoc": (None, MultiAgentVRGameEnv({}).observation_spaces["agent_assoc"], 
                           MultiAgentVRGameEnv({}).action_spaces["agent_assoc"], {}),
}

def policy_mapping_fn(agent_id):
    return agent_id  # agent_id is either "agent_res" or "agent_assoc"
