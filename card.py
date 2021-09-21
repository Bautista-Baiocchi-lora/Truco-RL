card_tiers = [
        (['E1'], 13),
        (['B1'], 12),
        (['E7'], 11),
        (['O7'], 10),
        (['E3', 'B3', 'O3', 'C3'], 9),
        (['E2', 'B2', 'O2', 'C2'], 8),
        (['O1', 'C1'], 7),
        (['E12', 'B12', 'O12', 'C12'], 6),
        (['E11', 'B11', 'O11', 'C11'], 5),
        (['E10', 'B10', 'O10', 'C10'], 4),
        (['C7', 'B7'], 3),
        (['E6', 'B6', 'O6', 'C6'], 2),
        (['E5', 'B5', 'O5', 'C6'], 1),
        (['E4', 'B4', 'O4', 'C4'], 0)
    ]

valid_suit = ['C', 'B', 'E', 'O']
valid_rank = ['1', '2', '3', '4', '5', '6', '7', '10', '11', '12']

''' Game-related base classes
'''
class Card:
    '''
    Card stores the suit and rank of a single card
    Note:
        The suit variable in a standard card game should be one of [C, B, E, O] meaning [Copa, Basto, Espada, Oro]
        Similarly the rank variable should be one of ['1', '2', '3', '4', '5', '6', '7', '10', '11', '12']
    '''
    suit = None
    rank = None
    

    def __init__(self, suit, rank):
        ''' Initialize the suit and rank of a card
        Args:
            suit: string, suit of the card, should be one of valid_suit
            rank: string, rank of the card, should be one of valid_rank
        '''
        self.suit = suit
        self.rank = rank
        for cards, tier in card_tiers:
            if suit+rank in cards:
                self.tier = tier
                break
        

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.rank == other.rank and self.suit == other.suit
        else:
            # don't attempt to compare against unrelated types
            return NotImplemented

    def __hash__(self):
        suit_index = Card.valid_suit.index(self.suit)
        rank_index = Card.valid_rank.index(self.rank)
        return rank_index + 100 * suit_index

    def __str__(self):
        ''' Get string representation of a card.
        Returns:
            string: the combination of rank and suit of a card. Eg: AS, 5H, JD, 3C, ...
        '''
        return self.get_index()
    
    def compare_as_str(self, card_as_string):
        return card_as_string == self.__str__()
    
    def get_index(self):
        ''' Get index of a card.
        Returns:
            string: the combination of suit and rank of a card. Eg: 1S, 2H, AD, BJ, RJ...
        '''
        return self.suit+self.rank