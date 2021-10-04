import numpy as np
from deck import init_truco_deck

truco_actions = np.array([ 
    'truco', 
    're-truco', 
    'vale cuatro'
])

envido_actions = np.array([ 
    'envido',
    'real envido',
])

response_actions = np.array([ 
    'quiero',
    'no quiero',
])

other_actions = np.array([
    'fold'
])

playable_actions = np.concatenate((truco_actions, envido_actions, response_actions, other_actions))


playable_cards = np.array([str(c) for c in init_truco_deck()])

game_actions = np.concatenate((playable_actions, playable_cards))

game_actions_list = game_actions.tolist()