from VR_CG_env import MultiAgentVRGameEnv
from ray.tune.registry import register_env

def env_creator(config):
    return MultiAgentVRGameEnv(config)

register_env("multi_vr_env", env_creator)
