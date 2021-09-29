
import numbers
import numpy as np
from envido import Envido
from actions import game_actions, envido_actions, truco_actions, response_actions, playable_cards
from truco import Truco
from card_utils import encode_card_array, encode_envido, encode_truco
from card_game import CardGame

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class TrucoGame:
    
    
    def __init__(self, players, goes_first=0):
        '''
        Initialize a Game of Truco.
        '''
        self.players = players
        self.finished = False
        self.round = 0
        self.scoreboard = np.array([(p, 0) for p in players])
        self.first_move_by = self.players[goes_first] 
        self.second_move_by = self.players[1 - goes_first] 
        self.envido = Envido(self)
        self.truco = Truco(self)
        self.card_game = CardGame(self, self.first_move_by)

    def get_state(self, player):
        player_cards = np.array(encode_card_array(player.hand))
        
        started =  1 if player == self.first_move_by else 0
        mano = 1 if player == self.get_mano() else 0
        game_config = np.array([started, mano])
        
        score = []
        for p, s in self.scoreboard:
            p_id = 1 if player == p else 0
            turn = [p_id, s]
            score.append(np.array(turn, dtype=np.int8))
        
        score = np.hstack(score)
        
        cards_played = []
        for p, c in self.card_game.cards_played:
            p_id = 1 if player == p else 0
            turn = [p_id, *encode_card_array(c)]
            cards_played.append(np.array(turn, dtype=np.int8))
        
        # Add padding for 6 turns
        for i in range(6 - len(cards_played)):
            cards_played.append(np.zeros(1 + 40, dtype=np.int8))
            
        cards_played = np.hstack(cards_played)
        
        envido_state = []
        for p, c in self.envido.envido_calls:
            p_id = 1 if player == p else 0
            turn = [p_id, *encode_envido(c)]
            envido_state.append(np.array(turn, dtype=np.int8))
        
        # Add padding 3 calls
        for i in range(3 - len(envido_state)):
            envido_state.append(np.zeros(1 + 4, dtype=np.int8))
            
        envido_state = np.hstack(envido_state)
            
        truco_state = []
        for p, c in self.truco.truco_calls:
            p_id = 1 if player == p else 0
            turn = [p_id, *encode_truco(c)]
            truco_state.append(np.array(turn, dtype = np.int8))
            
        # Add padding 5 calls
        for i in range(5 - len(truco_state)):
            truco_state.append(np.zeros(1 + 5, dtype=np.int8))
            
        truco_state = np.hstack(truco_state)
            
        return np.concatenate((game_config, player_cards, score, cards_played, envido_state, truco_state))
        
    
    def get_cards_played(self):
        return self.card_game.cards_played

    def update_score(self, player, score):
        if player == self.scoreboard[0][0]:
            self.scoreboard[0][1] += score
        else:
            self.scoreboard[1][1] += score
        
    def get_opponent(self, player):
        if player == self.players[0]:
            return self.players[1]
        else:
            return self.players[0]
    
    def get_mano(self):
        return self.card_game.card_next
        
    def finish_hand(self):
        self.finished = True
        logging.info("Hand finished.")
        logging.info(f"{self.scoreboard[0][0]} scored {self.scoreboard[0][1]}")
        logging.info(f"{self.scoreboard[1][0]} scored {self.scoreboard[1][1]}")
    
    def finish_round(self):
        self.round += 1
        
        first_played = self.card_game.cards_played[-2]
        second_played = self.card_game.cards_played[-1]
        comparison = first_played[1].tier - second_played[1].tier
        if comparison >= 0:
            self.card_game.switch_card_turn() # switch if second person wins round
            logging.debug(f"{second_played[0]} won the round. They will start the next one.")
        
        winner = self.card_game.get_card_winner()
        if winner is not None: 
            if self.truco.is_truco_started():
                reward = self.truco.get_truco_reward()
                self.update_score(winner, reward)
                logging.debug(f"{winner} was rewarded {reward} for winning truco.")
            else:
                self.update_score(winner, 1)
                logging.debug(f"{winner} was rewarded 1 for winning hand.")
            self.finish_hand()
        else:
            logging.debug("Round finished")
        
    def take_action(self, player, action):
        action_played = game_actions[action] if isinstance(action, numbers.Number) else action
        
        if action_played in envido_actions:
            if self.round == 0:
                if not self.truco.is_truco_active():
                    self.envido.take_action(player, action_played) 
                else:
                    logging.warn(f"{player}: Envido can only be played before Truco.")
            else:
                logging.warning(f"{player}: Envido can only be played in the first round")
        elif action_played in truco_actions:
            if not self.envido.is_envido_active():
                self.truco.take_action(player, action_played)
            else:
                logging.warning(f"{player} can't call {action_played} unless envido has finished.")
        elif action_played in response_actions:
            if self.envido.is_envido_active() and self.envido.is_valid_envido_state(action_played):
                if self.envido.envido_next == player:
                    self.envido.take_terminal_action(player, action_played) 
                else:
                    logging.warning(f"{player} can't call {action_played} envido for others.")
            elif self.truco.is_truco_active() and self.truco.is_valid_truco_state(action_played):
                self.truco.take_terminal_action(player, action_played)
            else:
                logging.warning(f"{player} can't call {action_played} right now.")
        elif action_played in playable_cards:
            if not self.envido.is_envido_active():
                if not self.truco.is_truco_active():
                    self.card_game.take_action(player, action_played)
                else:
                    logging.warning(f"{player} can't play the card {action_played} before responding to truco.")
            else:
                logging.warning(f"{player} can't play the card {action_played} before responding to envido.")
        elif action_played == "fold":
            logging.info(f"{player} folded.")
            if self.envido.is_envido_active():
               self.envido.fold(player)
            if self.truco.is_truco_started():
                self.truco.fold(player)
            else:
                opponent = self.get_opponent(player)
                self.update_score(opponent, 1)
                logging.debug(f"{opponent} was rewarded 1 for winning hand.")
            self.finish_hand()

        state = None

        return state
            
        
            
    