from wager import is_valid_state, is_wager_active, get_wager_reward, is_wager_finished
import numpy as np
import logging


envido_states = [
    (['envido', 'quiero'], 2),
    (['envido', 'no quiero'], 1),
    (['envido','envido', 'quiero'], 4),
    (['envido','envido', 'no quiero'], 2),
   (['envido', 'real envido', 'quiero'], 5),
    (['envido', 'real envido', 'no quiero'], 2),
    (['real envido', 'quiero'], 3),
    (['real envido', 'no quiero'], 1)
]

def rank_to_envido_value(rank):
    if rank in ['10', '11', '12']:
        return 10
    else:
        return int(rank)

def calculate_envido(cards):
    groups = {}
    
    for card in cards:
        value = rank_to_envido_value(card.rank)
        if card.suit in groups:
            groups[card.suit].append(value)
        else:
            groups[card.suit] = [value]
    
    score = 0
    for key, values in groups.items():
        if len(values) == 1:
            score = max(score, values[0] if values[0] != 10 else 0)
        elif len(values) == 2:
            #list with no duplicates
            new_values = list(dict.fromkeys(values))
            # double face card
            if len(new_values) < len(values):
                score = max(score, sum(values))
            elif 10 in new_values:
                score = max(score, sum(new_values) + 10)
            else:
                score = max(score, sum(new_values) + 20)
        else:
            #list with no duplicates
            new_values = list(dict.fromkeys(values))
            if len(new_values) == 1:
                score = max(score, 20)
            elif len(new_values) == 2:
                score = max(score, sum(new_values) + 10)
            elif 10 in new_values:
                score = max(score, sum(new_values) + 10)
            else:
                two_largest = np.argsort(new_values)
                score = max(score, sum(two_largest[-2:]))
                
    return score

class Envido:

    def __init__(self, game):
        '''
        Initialize envido.
        '''
        self.game = game
        self.finished = False
        self.envido_next = None
        self.envido_calls = [] 
    
    def get_state(self):
        state = np.array(
            [
                
            ]
        )

        return state

    def get_envido_winner(self):    
        p1_cards = np.concatenate(([card for player, card in self.game.get_cards_played() if player == self.game.first_move_by], self.game.first_move_by.hand))
        p2_cards = np.concatenate(([card for player, card in self.game.get_cards_played() if player == self.game.second_move_by], self.game.second_move_by.hand))
        
        p1_envido = calculate_envido(p1_cards)
        p2_envido = calculate_envido(p2_cards)
        
        logging.debug(f"{self.game.first_move_by} has an envido of {p1_envido}")
        logging.debug(f"{self.game.second_move_by} has an envido of {p2_envido}")
        
        return self.game.first_move_by if p1_envido >= p2_envido else self.game.second_move_by

    
    def get_envido_reward(self):
        return get_wager_reward(envido_states, self.envido_calls)
    
    def switch_envido_turn(self):
        self.envido_next = self.game.get_opponent(self.envido_next)

    
    def is_envido_active(self):
        return is_wager_active(self.envido_calls)

    
    def is_envido_finished(self):
        return is_wager_finished(self.envido_calls)

    
    def is_valid_envido_state(self, action):
        return is_valid_state(envido_states, self.envido_calls, action)

    
    def is_envido_active(self):
        return is_wager_active(self.envido_calls)

    def take_action(self, player, action_played):
        if len(self.envido_calls) == 0:
            self.envido_calls.append((player, action_played))
            logging.info(f"{player} called {action_played}.")
            self.envido_next = self.game.get_opponent(player)
        elif self.envido_calls[-1][0] != player and self.is_valid_envido_state(action_played):
            self.envido_calls.append((player, action_played))
            logging.info(f"{player} called {action_played}")
            self.switch_envido_turn()
        else:
            logging.warn(f"{player} can't call {action_played}.")

    def take_terminal_action(self, player, action_played):
        self.envido_calls.append((player, action_played))
        logging.info(f"{player} called {action_played} envido")
        if action_played == "no quiero":
            opponent = self.game.get_opponent(player)
            reward = self.get_envido_reward()
            self.game.update_score(opponent, reward)
            logging.debug(f"{opponent} was rewarded {reward} for winning envido.")
        else:
            winner = self.get_envido_winner()
            reward = self.get_envido_reward()
            self.game.update_score(winner, reward)
            logging.debug(f"{winner} was rewarded {reward} for winning envido.")
        # de-activate envido    
        self.envido_next = None
        self.finished = True

    def fold(self, player):
        self.envido_calls.append((player, 'no quiero'))
        logging.debug(f"{player} forfeited envido")
        opponent = self.game.get_opponent(player)
        reward = self.get_envido_reward()
        self.game.update_score(opponent, reward)
        logging.debug(f"{opponent} was rewarded {reward} for winning envido.")
