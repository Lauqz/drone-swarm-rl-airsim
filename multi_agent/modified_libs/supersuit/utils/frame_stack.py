import numpy as np
import copy
from gymnasium.spaces import Box, Discrete, Dict


def get_tile_shape(shape, stack_size, stack_dim=-1):
    obs_dim = len(shape)

    if stack_dim == -1:
        if obs_dim == 1:
            tile_shape = (stack_size,)
            new_shape = shape
        elif obs_dim == 3:
            tile_shape = (1, 1, stack_size)
            new_shape = shape
        # stack 2-D frames
        elif obs_dim == 2:
            tile_shape = (1, 1, stack_size)
            new_shape = shape + (1,)
        else:
            assert False, "Stacking is only available for 1,2 or 3 dimensional arrays"

    elif stack_dim == 0:
        if obs_dim == 1:
            tile_shape = (stack_size,)
            new_shape = shape
        elif obs_dim == 3:
            tile_shape = (stack_size, 1, 1)
            new_shape = shape
        # stack 2-D frames
        elif obs_dim == 2:
            tile_shape = (stack_size, 1, 1)
            new_shape = (1,) + shape
        else:
            assert False, "Stacking is only available for 1,2 or 3 dimensional arrays"

    return tile_shape, new_shape


def stack_obs_space(obs_space, stack_size, stack_dim=-1):
    """
    obs_space_dict: Dictionary of observations spaces of agents
    stack_size: Number of frames in the observation stack
    Returns:
        New obs_space_dict
    """
    if isinstance(obs_space, Box):
        dtype = obs_space.dtype
        # stack 1-D frames and 3-D frames
        tile_shape, new_shape = get_tile_shape(
            obs_space.low.shape, stack_size, stack_dim
        )

        low = np.tile(obs_space.low.reshape(new_shape), tile_shape)
        high = np.tile(obs_space.high.reshape(new_shape), tile_shape)
        new_obs_space = Box(low=low, high=high, dtype=dtype)
        return new_obs_space
    elif isinstance(obs_space, Discrete):
        return Discrete(obs_space.n**stack_size)
    elif isinstance(obs_space, Dict):
        new_obs_space = copy.deepcopy(obs_space)
        for name, space in obs_space.items():
            dtype = space.dtype
            # stack 1-D frames and 3-D frames
            tile_shape, new_shape = get_tile_shape(
                space.low.shape, stack_size, stack_dim
            )

            low = np.tile(space.low.reshape(new_shape), tile_shape)
            high = np.tile(space.high.reshape(new_shape), tile_shape)
            new_obs_space[name] = Box(low=low, high=high, dtype=dtype)
        return new_obs_space
    else:
        assert (
            False
        ), "Stacking is currently only allowed for Box, Dict (with only Box spaces) and Discrete observation spaces. The given observation space is {}".format(
            obs_space
        )


def stack_init(obs_space, stack_size, stack_dim=-1):
    if isinstance(obs_space, Box):
        tile_shape, new_shape = get_tile_shape(
            obs_space.low.shape, stack_size, stack_dim
        )
        return np.tile(np.zeros(new_shape, dtype=obs_space.dtype), tile_shape)
    elif isinstance(obs_space, Dict):
        new_zeros = {}
        for name, space in obs_space.items():
            tile_shape, new_shape = get_tile_shape(
                space.low.shape, stack_size, stack_dim
            )
            new_zeros[name] = np.tile(np.zeros(new_shape, dtype=space.dtype), tile_shape)
        return new_zeros
    else:
        return 0


def stack_obs(frame_stack, obs, obs_space, stack_size, stack_dim=-1):
    """
    Parameters
    ----------
    frame_stack : if not None, it is the stack of frames
    obs : new observation
        Rearranges frame_stack. Appends the new observation at the end.
        Throws away the oldest observation.
    stack_size : needed for stacking reset observations
    """

    if isinstance(obs_space, Box):
        obs_shape = obs.shape
        agent_fs = frame_stack

        if len(obs_shape) == 1:
            size = obs_shape[0]
            agent_fs[:-size] = agent_fs[size:]
            agent_fs[-size:] = obs

        elif len(obs_shape) == 2:
            if stack_dim == -1:
                agent_fs[:, :, :-1] = agent_fs[:, :, 1:]
                agent_fs[:, :, -1] = obs
            elif stack_dim == 0:
                agent_fs[:-1] = agent_fs[1:]
                agent_fs[:-1] = obs

        elif len(obs_shape) == 3:
            if stack_dim == -1:
                nchannels = obs_shape[-1]
                agent_fs[:, :, :-nchannels] = agent_fs[:, :, nchannels:]
                agent_fs[:, :, -nchannels:] = obs
            elif stack_dim == 0:
                nchannels = obs_shape[0]
                agent_fs[:-nchannels] = agent_fs[nchannels:]
                agent_fs[-nchannels:] = obs

        return agent_fs
    
    elif isinstance(obs_space, Dict):
        agent_fs = frame_stack

        for name, value in agent_fs.items():
            obs_shape = obs[name].shape

            if len(obs_shape) == 1:
                size = obs_shape[0]
                value[:-size] = value[size:]
                value[-size:] = obs[name]

            elif len(obs_shape) == 2:
                if stack_dim == -1:
                    value[:, :, :-1] = value[:, :, 1:]
                    value[:, :, -1] = obs[name]
                elif stack_dim == 0:
                    value[:-1] = value[1:]
                    value[:-1] = obs[name]

            elif len(obs_shape) == 3:
                if stack_dim == -1:
                    nchannels = obs_shape[-1]
                    value[:, :, :-nchannels] = value[:, :, nchannels:]
                    value[:, :, -nchannels:] = obs[name]
                elif stack_dim == 0:
                    nchannels = obs_shape[0]
                    value[:-nchannels] = value[nchannels:]
                    value[-nchannels:] = obs[name]

            agent_fs[name] = value

        return agent_fs

    elif isinstance(obs_space, Discrete):
        return (frame_stack * obs_space.n + obs) % (obs_space.n**stack_size)
