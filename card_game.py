from more_itertools import locate
import logging

class CardGame:

    def __init__(self, game, goes_first):
        '''
        Initialize Card Game.
        '''
        self.game = game
        self.finished = False
        self.card_next = goes_first
        self.cards_played = []

    def get_card_winner(self):
        p0_cards = [card for player, card in self.cards_played if player == self.game.first_move_by]
        p1_cards = [card for player, card in self.cards_played if player == self.game.second_move_by]
        
        p0_wins=0
        p1_wins=0
        tie_exists = False
        for c1, c2 in zip(p0_cards, p1_cards):
            if p0_wins >= 2 or p1_wins >= 2:
                break
                
            comparison = c1.tier - c2.tier
            if comparison > 0:
                p0_wins += 1
                if tie_exists:
                    break
            elif comparison < 0:
                p1_wins += 1
                if tie_exists:
                    break
            elif comparison == 0:
                if p0_wins > p1_wins:
                    p1_wins += 1
                    break
                elif p1_wins > p0_wins:
                    p1_wins += 1
                    break
                else:
                    tie_exists = True
                    
            logging.debug(f"p0_wins: {p0_wins} | p1_wins: {p1_wins} | tie_exists: {tie_exists}")
            
        # incase of tie on last card
        if (p0_wins + p1_wins) > 0 and p0_wins == p1_wins and tie_exists:
            return self.game.first_move_by
        
        # incase of tie on all 3 cards
        if p0_wins == 0 and p1_wins == 0 and tie_exists:
            return self.game.first_move_by
                
        return self.game.first_move_by if p0_wins >= p1_wins else self.game.second_move_by

    
    def switch_card_turn(self):
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
                self.switch_card_turn()
        elif len(card_played_indexes) > 1:
            logging.critical(f"{player}: card_played_indexes should never be > 1. Current value: {card_played_indexes}")
        else:
            logging.warning(f"{player} can't play the card {action_played}. They don't have it.")