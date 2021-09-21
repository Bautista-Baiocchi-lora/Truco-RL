class Player:
    
    def __init__(self, player_id):
        ''' Initilize a player.
        Args:
            player_id (int): The id of the player
        '''
        self.player_id = player_id
        self.hand = []
        
    def __str__(self):
        return f"Player {self.player_id} | Cards: {[str(c) for c in self.hand]}"
    
    def __eq__(self, other):
        if isinstance(other, Player):
            return self.get_id() == other.get_id()
        return False

    def get_id(self):
        ''' Return the id of the player
        '''

        return self.player_id