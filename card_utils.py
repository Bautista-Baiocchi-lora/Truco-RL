from card import Card
from deck import init_truco_deck
from actions import envido_actions, response_actions, truco_actions
import numpy as np

default_deck = np.array([card.get_index() for card in init_truco_deck()])

envido_actions = np.concatenate((envido_actions, response_actions))

truco_actions = np.concatenate((truco_actions, response_actions))


def encode_card_array(cards):
    if not isinstance(cards, list):
        cards = [cards]
    cards = [str(c) for c in cards]
    return  [1 if card in cards else 0 for card in default_deck]

    
def encode_envido(action):
    return [1 if a == action else 0 for a in envido_actions]

def encode_truco(action):
    return [1 if a == action else 0 for a in truco_actions]
    