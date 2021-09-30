from wager import is_valid_wager_state, is_wager_active, get_wager_reward, is_wager_finished, is_wager_started
import logging
import numpy as np
from card_utils import encode_truco

truco_states = [
    (['truco', 'quiero'], 2),
    (['truco', 'no quiero'], 1),
   (['truco', 're-truco', 'quiero'], 3),
   (['truco', 're-truco', 'no quiero'], 2),
    (['truco', 're-truco', 'vale cuatro', 'quiero'], 4),
    (['truco', 're-truco', 'vale cuatro', 'no quiero'], 3),
    # double downs
   (['truco', 'quiero','re-truco', 'quiero'], 3),
    (['truco', 'quiero','re-truco', 'no quiero'], 2),
    (['truco', 're-truco', 'quiero', 'vale cuatro', 'quiero'], 4),
    (['truco', 're-truco', 'quiero', 'vale cuatro', 'no quiero'], 3),
    (['truco', 'quiero', 're-truco', 'vale cuatro', 'quiero'], 4),
    (['truco', 'quiero', 're-truco', 'vale cuatro', 'no quiero'], 3),
]


class Truco:


    def __init__(self, game):
        '''
        Initialize Truco.
        '''
        self.game = game
        self.finished = False
        self.truco_next = None
        self.has_retruco = None
        self.truco_calls = []
        
    def get_state(self, player):
        state = []
        for p, c in self.truco_calls:
            p_id = 1 if player == p else 0
            turn = [p_id, *encode_truco(c)]
            state.append(np.array(turn, dtype = np.int8))
            
        # Add padding 5 calls
        for i in range(5 - len(state)):
            state.append(np.zeros(1 + 5, dtype=np.int8))
            
        return state
    
    def get_legal_actions(self, player):
        if self.truco_next == player or self.has_retruco == player:
            raw_state = [call for player, call in self.truco_calls]
    
            legal_actions = []
            for state, val in truco_states:
                if state[:len(raw_state)] == raw_state:
                    legal_actions.append(state[len(raw_state)])

            return list(dict.fromkeys(legal_actions))
        elif not self.is_started():
            return ['truco']
        return []


    def get_reward(self):
        return get_wager_reward(truco_states, self.truco_calls)
        
    def is_started(self):
        return is_wager_started(self.truco_calls)

    def is_active(self):
        return is_wager_active(self.truco_calls)


    def is_valid_state(self, action):
        return is_valid_wager_state(truco_states, self.truco_calls, action)
    

    def is_finished(self):
        return is_wager_finished(self.truco_calls)
    
          
    def switch_turn(self):
        self.truco_next = self.game.get_opponent(self.truco_next)

    def take_action(self, player, action_played):
        if self.is_valid_state(action_played):
            if not self.is_started() and action_played == "truco" and self.game.get_mano() == player:
                self.truco_calls.append((player,action_played))
                logging.info(f"{player} called {action_played} to start truco")
                self.truco_next = self.game.get_opponent(player)
            elif self.is_active() and self.truco_next == player:
                self.truco_calls.append((player, action_played))
                logging.info(f"{player} called {action_played}")
                self.truco_next = self.game.get_opponent(player)
            elif self.has_retruco == player and action_played == "re-truco":
                self.truco_calls.append((player, action_played))
                logging.info(f"{player} called {action_played} for re-truco")
                self.truco_next = self.game.get_opponent(player)
                self.has_retruco = None 
            else:
                logging.warning(f"{player} can't call {action_played}. Not your turn.")
        else:
            logging.warn(f"{player} can't call {action_played}. Invalid Truco State.")

    def take_terminal_action(self, player, action_played):
        self.truco_calls.append((player, action_played))
        logging.info(f"{player} called {action_played} truco")
        if action_played == "no quiero":
            opponent = self.game.get_opponent(player)
            reward = self.get_reward()
            self.game.update_score(opponent, reward)
            logging.debug(f"{opponent} was rewarded {reward} for winning truco.")
            self.game.finish_hand()
        else:
            #is re-truco possible ?
            if self.has_retruco is None:
                self.has_retruco = player
            else:
                self.has_retruco = None
            self.truco_next = None
    
    def fold(self, player):
        if self.is_active():
            self.truco_calls.append((player, 'no quiero'))
        logging.debug(f"{player} forfeited truco")
        opponent = self.game.get_opponent(player)
        reward = self.get_reward()
        self.game.update_score(opponent, reward)
        logging.debug(f"{opponent} was rewarded {reward} for winning truco.")