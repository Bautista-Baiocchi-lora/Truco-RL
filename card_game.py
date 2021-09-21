from more_itertools import locate
import logging

class CardGame:

    def __init__(self, game):
        '''
        Initialize Card Game.
        '''
        self.game = game
        self.finished = False
        self.card_next = None
        self.cards_played = []

    def get_card_winner(self):
        p1_cards = [card for player, card in self.cards_played if player == self.game.first_move_by]
        p2_cards = [card for player, card in self.cards_played if player == self.game.second_move_by]
        
        p1_wins=0
        p2_wins=0
        next_wins = False
        for c1, c2 in zip(p1_cards, p2_cards):
            comparison = c1.tier - c2.tier
            if comparison > 0:
                p1_wins += 1
                if next_wins:
                    break
            elif comparison < 0:
                p2_wins += 1
                if next_wins:
                    break
            elif comparison == 0:
                if p1_wins > p2_wins:
                    p1_wins += 1
                    break
                elif p2_wins > p1_wins:
                    p2_wins += 1
                    break
                else:
                    next_wins = True
                
        if p1_wins < 2 and p2_wins < 2:
            return None
        
        return self.game.first_move_by if p1_wins >= p2_wins or (p1_wins == 0 and p2_wins == 0 and next_wins) else self.game.second_move_by

    
    def switch_card_turn(self):
        self.card_next = self.game.get_opponent(self.card_next)

    def take_action(self, player, action_played):
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