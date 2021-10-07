from more_itertools import locate
import numpy as np
import logging
from collections import Counter

from card_utils import encode_card_array

card_game_tie_states = [
    (['tie', 'tie', 'tie'], 'p0'),
    (['tie', 'tie', 'p0'], 'p0'),
    (['tie', 'tie', 'p1'], 'p1'),
    (['tie', 'p0'], 'p0'),
    (['tie', 'p1'], 'p1'),
    (['p0', 'tie'], 'p0'),
    (['p1', 'tie'], 'p1'),
    (['p0', 'p1', 'tie'], 'p0'),
    (['p1', 'p0', 'tie'], 'p1'),
]

class CardGame:

    def __init__(self, game, goes_first):
        '''
        Initialize Card Game.
        '''
        self.game = game
        self.finished = False
        self.card_next = goes_first
        self.cards_played = []
        
    def get_state(self, player):
        state = []
        for p, c in self.cards_played:
            p_id = 1 if player == p else 0
            turn = [p_id, *encode_card_array(c)]
            state.append(np.array(turn, dtype=np.int8))
        
        # Add padding for 6 turns
        for i in range(6 - len(state)):
            state.append(np.zeros(1 + 40, dtype=np.int8))
            
        state = np.vstack(state)
            
        return state
    
    def get_legal_actions(self, player):
        if self.card_next == player:
            return [card.get_index() for card in player.hand]
        return []

    def get_winner(self):
        p0_cards = [card for player, card in self.cards_played if player == self.game.first_move_by]
        p1_cards = [card for player, card in self.cards_played if player == self.game.second_move_by]
        
        # Minimum 4 cards must be played to have a winner
        if len(p0_cards) + len(p1_cards) < 4:
            return None
        
        results = []
        for c1, c2 in zip(p0_cards, p1_cards):
            comparison = c1.tier - c2.tier
            if comparison > 0:
                results.append('p0')
            elif comparison < 0:
                results.append('p1')
            elif comparison == 0:
                results.append('tie')
                    
        
        for tie_state, winner in card_game_tie_states:
            if results == tie_state:
                return self.game.first_move_by if winner == 'p0' else self.game.second_move_by
            
        counts = Counter(results)
         
        if counts['p0'] >= 2:
            return self.game.first_move_by
        elif counts['p1'] >= 2:
            return self.game.second_move_by
        else:
            return None

    
    def switch_turn(self):
        self.card_next = self.game.get_opponent(self.card_next)

    def take_action(self, player, action_played):
        if self.card_next != player:
            logging.warning(f"{player} can't play a card out of turn.")
            return

        card_played_indexes = list(locate(player.hand, lambda c: c.compare_as_str(action_played)))
        if len(card_played_indexes) == 1:
            card_played = player.hand.pop(card_played_indexes[0])
            self.cards_played.append((player, card_played))
            logging.info(f"{player} played {card_played}")
            if len(self.cards_played) % 2 == 0:
                self.game.finish_round()
            else:
                self.switch_turn()
        elif len(card_played_indexes) > 1:
            logging.critical(f"{player}: card_played_indexes should never be > 1. Current value: {card_played_indexes}")
        else:
            logging.warning(f"{player} can't play the card {action_played}. They don't have it.")