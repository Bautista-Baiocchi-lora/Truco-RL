from card import Card, valid_suit, valid_rank

def init_truco_deck():
    ''' Initialize a truco deck of 52 cards
    Returns:
        (list): A list of Card object
    '''
    res = [Card(suit, rank) for suit in valid_suit for rank in valid_rank]
    return res

def shuffle_cards(cards, in_place=False):
    import random
    if in_place:
        random.shuffle(cards)
        return cards
    else:
        import copy 
        copied_cards = copy.deepcopy(cards)
        random.shuffle(copied_cards)
        return copied_cards