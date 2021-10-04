from wager import is_valid_wager_state, is_wager_active, get_wager_reward, is_wager_finished, is_wager_started
import numpy as np
import logging

from card_utils import encode_envido


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
    
    def get_state(self, player):
        state = []
        for p, c in self.envido_calls:
            p_id = 1 if player == p else 0
            turn = [p_id, *encode_envido(c)]
            state.append(np.array(turn, dtype=np.int8))
            
        # Add padding 3 calls
        for i in range(3 - len(state)):
            state.append(np.zeros(1 + 4, dtype=np.int8))
            
        envidos = np.array([self.calculate_player_envido(player), self.calculate_player_envido(self.game.get_opponent(player))])
            
        return state, envidos
    
    
    def get_legal_actions(self, player):
        if self.envido_next == player:
            raw_state = [call for player, call in self.envido_calls]
    
            legal_actions = []
            for state, val in envido_states:
                if state[:len(raw_state)] == raw_state and len(raw_state) < len(state):
                    legal_actions.append(state[len(raw_state)])

            return list(dict.fromkeys(legal_actions))
        elif not self.is_started():
            return ['envido', 'real envido']
        return []
    
    def calculate_player_envido(self, player):
        cards = np.concatenate(([c for p, c in self.game.get_cards_played() if player == p], player.hand))
        return calculate_envido(cards)

    def get_winner(self):    
        p1_envido = self.calculate_player_envido(self.game.first_move_by)
        p2_envido = self.calculate_player_envido(self.game.second_move_by)
        
        logging.debug(f"{self.game.first_move_by} has an envido of {p1_envido}")
        logging.debug(f"{self.game.second_move_by} has an envido of {p2_envido}")
        
        return self.game.first_move_by if p1_envido >= p2_envido else self.game.second_move_by

    
    def get_reward(self):
        return get_wager_reward(envido_states, self.envido_calls)
    
    def switch_turn(self):
        self.envido_next = self.game.get_opponent(self.envido_next)

    def is_started(self):
        return is_wager_started(self.envido_calls)
    
    def is_active(self):
        return is_wager_active(self.envido_calls)

    
    def is_finished(self):
        return is_wager_finished(self.envido_calls)

    
    def is_valid_state(self, action):
        return is_valid_wager_state(envido_states, self.envido_calls, action)


    def take_action(self, player, action_played):
        if self.is_valid_state(action_played):
            if len(self.envido_calls) == 0 and self.game.get_mano() == player:
                self.envido_calls.append((player, action_played))
                logging.info(f"{player} called {action_played}.")
                self.envido_next = self.game.get_opponent(player)
            elif self.is_active() and self.envido_calls[-1][0] != player:
                self.envido_calls.append((player, action_played))
                logging.info(f"{player} called {action_played}")
                self.switch_turn()
            else:
                logging.warn(f"{player} can't call {action_played}. Not Your Turn.")
        else:
            logging.warn(f"{player} can't call {action_played}. Invalid Envido State.")

    def take_terminal_action(self, player, action_played):
        self.envido_calls.append((player, action_played))
        logging.info(f"{player} called {action_played} envido")
        if action_played == "no quiero":
            opponent = self.game.get_opponent(player)
            reward = self.get_reward()
            self.game.update_score(opponent, reward)
            logging.debug(f"{opponent} was rewarded {reward} for winning envido.")
        else:
            winner = self.get_winner()
            reward = self.get_reward()
            self.game.update_score(winner, reward)
            logging.debug(f"{winner} was rewarded {reward} for winning envido.")
        # de-activate envido    
        self.envido_next = None
        self.finished = True

    def fold(self, player):
        self.envido_calls.append((player, 'no quiero'))
        logging.debug(f"{player} forfeited envido")
        opponent = self.game.get_opponent(player)
        reward = self.get_reward()
        self.game.update_score(opponent, reward)
        logging.debug(f"{opponent} was rewarded {reward} for winning envido.")
