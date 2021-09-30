import torch
from game import TrucoGame
from actions import game_actions

def encode_game_state(player, game):
    state = game.get_state(player)

    game_t = torch.tensor(state['game']).reshape(-1).squeeze()
    score_t = torch.tensor(state['score']).reshape(-1).squeeze()
    player_cards_t = torch.tensor(state['player_cards']).reshape(-1).squeeze()
    cards_played_t = torch.tensor(state['cards_played']).reshape(-1).squeeze()
    envido_state_t = torch.tensor(state['envido_state']).reshape(-1).squeeze()
    truco_state_t = torch.tensor(state['truco_state']).reshape(-1).squeeze()

    return torch.cat((game_t, score_t, player_cards_t, cards_played_t, envido_state_t, truco_state_t)).type(torch.CharTensor)

class TrucoEnvironment:

    def __init__(self, players):
        self.game = TrucoGame(players)
        self.action_space_dim=game_actions.shape[0]
        self.state_space_dim=encode_game_state(self.game.get_mano(), self.game).shape[0]
        self.players = players

    def reset(self):
        # Clear player cards
        for player in self.players:
            player.hand.clear()
            
        self.game = TrucoGame(self.players)
        return self.game.get_mano(), encode_game_state(self.game.get_mano(), self.game)

    def step(self, player, action):
        self.game.take_action(player, action)
        
        return self.game.get_mano(), encode_game_state(player, self.game)

            
