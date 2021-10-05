import numbers
import numpy as np
from envido import Envido
from actions import game_actions, envido_actions, truco_actions, response_actions, playable_cards
from truco import Truco
from card_utils import encode_card_array, encode_envido, encode_truco
from card_game import CardGame
from dealer import Dealer

import logging


class TrucoGame:
    
    
    def __init__(self, players, goes_first=0):
        '''
        Initialize a Game of Truco.
        '''
        self.players = players
        self.dealer = Dealer()
        self.finished = False
        self.round = 0
        self.scoreboard = np.array([(p, 0) for p in players])
        self.first_move_by = self.players[goes_first] 
        self.second_move_by = self.players[1 - goes_first] 
        
        self.dealer.deal_cards_in_order(self.players)
        
        self.envido = Envido(self)
        self.truco = Truco(self)
        self.card_game = CardGame(self, self.first_move_by)

    def get_state(self, player):
        started =  1 if player == self.first_move_by else 0
        mano = 1 if player == self.get_mano() else 0
        game_config = np.array([started, mano], dtype=np.int8)
        
        score = []
        for p, s in self.scoreboard:
            p_id = 1 if player == p else 0
            turn = [p_id, s]
            score.append(np.array(turn, dtype = np.int8))
        
        score = np.vstack(score)
            
        state = {
            'game': game_config,
            'player_cards': np.array(encode_card_array(player.hand), dtype=np.int8),
            'score': score,
            'cards_played': self.card_game.get_state(player),
            'envido_state': self.envido.get_state(player),
            'truco_state': self.truco.get_state(player)
            
        }
            
        return state
    
    def get_score(self, player):
        if self.scoreboard[0][0] == player:
            return self.scoreboard[0][1]
        else:
            return self.scoreboard[1][1]
        
        return 0
    
    def get_winner(self):
        if self.finished:
            if self.scoreboard[0][1] >= self.scoreboard[1][1]:
                return self.scoreboard[0][0]
            else:
                return self.scoreboard[1][0]
            
        return None
        
    def get_legal_actions(self, player):
        if self.get_mano() != player:
            return []
        elif self.envido.is_active():
            return self.envido.get_legal_actions(player)  + ['fold']
        elif self.truco.is_active():
            return self.truco.get_legal_actions(player)  + ['fold']
        
        aggregate = ['fold']
        
        if self.round == 0 and not self.truco.is_started():
            aggregate.extend(self.envido.get_legal_actions(player))
    
        aggregate.extend(self.truco.get_legal_actions(player))
        
        return np.hstack((aggregate, self.card_game.get_legal_actions(player)))
            
    
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
        if self.envido.envido_next is not None:
            return self.envido.envido_next
        elif self.truco.truco_next is not None:
            return self.truco.truco_next
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
            self.card_game.switch_turn() # switch if second person wins round
            logging.debug(f"{second_played[0]} won the round playing {str(second_played[1])}. They will start the next one.")
        
        winner = self.card_game.get_winner()
        if winner is not None: 
            if self.truco.is_started():
                reward = self.truco.get_reward()
                self.update_score(winner, reward)
                logging.debug(f"{winner} was rewarded {reward} for winning truco.")
            else:
                self.update_score(winner, 1)
                logging.debug(f"{winner} was rewarded 1 for winning hand.")
            self.finish_hand()
        else:
            logging.debug("Round finished")
        
    def take_action(self, player, action):
        if self.get_mano() != player:
            logging.warning(f"{player}: Can't play out of turn.")
            return 
        
        action_played = game_actions[action] if isinstance(action, numbers.Number) else action
        
        if action_played in envido_actions:
            if self.round == 0:
                if not self.truco.is_started():
                    self.envido.take_action(player, action_played) 
                else:
                    logging.warn(f"{player}: Envido can only be played before Truco.")
            else:
                logging.warning(f"{player}: Envido can only be played in the first round")
        elif action_played in truco_actions:
            if not self.envido.is_active():
                self.truco.take_action(player, action_played)
            else:
                logging.warning(f"{player} can't call {action_played} unless envido has finished.")
        elif action_played in response_actions:
            if self.envido.is_active() and self.envido.is_valid_state(action_played):
                if self.envido.envido_next == player:
                    self.envido.take_terminal_action(player, action_played) 
                else:
                    logging.warning(f"{player} can't call {action_played} envido for others.")
            elif self.truco.is_active() and self.truco.is_valid_state(action_played):
                self.truco.take_terminal_action(player, action_played)
            else:
                logging.warning(f"{player} can't call {action_played} right now.")
        elif action_played in playable_cards:
            if not self.envido.is_active():
                if not self.truco.is_active():
                    self.card_game.take_action(player, action_played)
                else:
                    logging.warning(f"{player} can't play the card {action_played} before responding to truco.")
            else:
                logging.warning(f"{player} can't play the card {action_played} before responding to envido.")
        elif action_played == "fold":
            logging.info(f"{player} folded.")
            if self.envido.is_active():
                self.envido.fold(player)
            if self.truco.is_started():
                self.truco.fold(player)
            else:
                opponent = self.get_opponent(player)
                self.update_score(opponent, 1)
                logging.debug(f"{opponent} was rewarded 1 for winning hand.")
            self.finish_hand()

            
        
            
    