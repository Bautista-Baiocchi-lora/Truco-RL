from deck import init_truco_deck, shuffle_cards

class Dealer:
    
    def __init__(self):
        '''
        Initialize a dealer.
        '''
        self.deck = init_truco_deck()
        shuffle_cards(self.deck, True)
        
    def deal_cards_in_order(self, players, amount=3):
        player_index = 0
        for _ in range(amount * len(players)):
            if player_index == len(players):
                player_index = 0
            players[player_index].hand.append(self.deck.pop())
            player_index+=1
