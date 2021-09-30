import numpy as np
    

def is_valid_wager_state(all_states, current_state, action):
    raw_state = np.append([call for player, call in current_state], action)
    
    for state, score in all_states:
        zipped = list(zip(state, raw_state))
        if len(zipped) != len(raw_state):
            continue
        if np.all([True if a == b else False for a, b in zipped]):
            return True
    return False

def is_wager_finished(current_state):
    return len(current_state) > 0 and current_state[-1][1] == 'quiero' or current_state[-1][1] ==  'no quiero'

def is_wager_started(current_state):
    return len(current_state) > 0

def is_wager_active(current_state):
    return is_wager_started(current_state) and not is_wager_finished(current_state)

def get_wager_reward(all_states, current_state):
    raw_state = [call for player, call in current_state]
    for state, score in all_states:
        if len(state) == len(raw_state) and np.all(state == raw_state):
            return score
    raise Exception(f"Can't get wager reward. No wager matching {raw_state}")
    