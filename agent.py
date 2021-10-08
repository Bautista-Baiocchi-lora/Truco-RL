import torch as T
from torch import nn
from collections import deque
import itertools
import numpy as np
from actions import game_actions_list
import random
from player import Player

def load_model(name, path=None):
    if path is not None:
        return T.load(f"./model_saves/{path}/model-{name}.pt")
    return T.load(f"./model_saves/model-{name}.pt")

def load_agent(name, device):
    player = Player(name)
    loaded = load_model(name)
    return Agent(player,
                 state_space_dim=loaded['state_space_dim'], 
                 action_space_dim=loaded['action_space_dim'], 
                 model_type=loaded['model_type'], 
                 model_state_dict=loaded['model_state_dict'], 
                 optimizer_state_dict=loaded['optimizer_state_dict'],
                 save_freq=loaded['save_freq'],
                 batch_size=loaded['batch_size'],
                 target_update_freq=loaded['target_update_freq'],
                 min_replay_size=loaded['min_replay_size'],
                 learning_rate=loaded['learning_rate'],
                 replay_buffer_size=loaded['replay_buffer_size'],
                 reward_buffer_size=loaded['reward_buffer_size'],
                 epsilon_start=loaded['epsilon_start'],
                 epsilon_end=loaded['epsilon_end'],
                 epsilon_decay=loaded['epsilon_decay'],
                 gamma=loaded['gamma'],
                 step=loaded['step'],
                 device=device)

def save_agent(agent, name=None):
    name = agent.get_name() if name is None else name
    model = {
        "model_state_dict": agent.online_net.state_dict(), 
        "optimizer_state_dict": agent.optimizer.state_dict(), 
        "model_type": agent.model_type, 
        "action_space_dim": agent.action_space_dim,
        "state_space_dim": agent.state_space_dim,
        "save_freq": agent.save_freq,
        "batch_size": agent.batch_size,
        "target_update_freq": agent.target_update_freq,
        "min_replay_size": agent.min_replay_size,
        "learning_rate": agent.learning_rate,
        "replay_buffer_size": agent.replay_buffer.maxlen,
        "reward_buffer_size": agent.reward_buffer.maxlen,
        "epsilon_start": agent.epsilon_start,
        "epsilon_end": agent.epsilon_end,
        "epsilon_decay": agent.epsilon_decay,
        "gamma": agent.gamma,
        "step": agent.step
    }
    T.save(model, f"./model_saves/model-{name}.pt")
    print(f"Model {name} saved. \r")

class LessDQNetwork(nn.Module):
    
    def __init__(self, state_space_dim, action_space_dim):
        super().__init__()
        
        self.net = nn.Sequential(
            nn.Linear(state_space_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, action_space_dim)
        )
        
    def forward(self, x):
        return self.net(x)
    
    def act(self, game_state_t):
        q_values = self(game_state_t.unsqueeze(0))
        
        return q_values.detach().squeeze()

class VeryDQNetwork(nn.Module):
    
    def __init__(self, state_space_dim, action_space_dim):
        super().__init__()
        
        self.net = nn.Sequential(
            nn.Linear(state_space_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_space_dim)
        )
        
    def forward(self, x):
        return self.net(x)
    
    def act(self, game_state_t):
        q_values = self(game_state_t.unsqueeze(0))
        
        return q_values.detach().squeeze()

class Agent:
    def __init__(self, player,
                 device, 
                 state_space_dim, 
                 action_space_dim, 
                 model_type='deep',
                 model_state_dict=None,
                 optimizer_state_dict=None,
                 loss=nn.MSELoss(),
                 save_freq=200000,
                 batch_size=32,
                 target_update_freq=1000,
                 min_replay_size=1000,
                 learning_rate=5e-4, 
                 replay_buffer_size=50000, 
                 reward_buffer_size=100, 
                 epsilon_start=1.0, 
                 epsilon_end=0.02, 
                 epsilon_decay=10000,
                 step=0,
                 gamma=0.99):
        
        self.player = player
        self.loss = loss
        self.device = device
        self.model_type = model_type
        self.state_space_dim = state_space_dim
        self.action_space_dim = action_space_dim
        self.learning_rate = learning_rate
        
        # ever how many steps the online_net params should be saved to disk
        self.save_freq = save_freq
        
        def init_weights(m):
            if isinstance(m, nn.Linear):
                T.nn.init.xavier_uniform_(m.weight)
                m.bias.data.fill_(0.01)
        
        # Initialize the NNs
        if self.model_type == 'deep':
            self.online_net = VeryDQNetwork(
                state_space_dim, 
                action_space_dim
            )
            
            self.online_net.apply(init_weights)

            self.target_net = VeryDQNetwork(
                state_space_dim, 
                action_space_dim
            )
            
            
            self.target_net.apply(init_weights)
        else:
            self.online_net = LessDQNetwork(
                state_space_dim, 
                action_space_dim
            )
            
            self.online_net.apply(init_weights)

            self.target_net = LessDQNetwork(
                state_space_dim, 
                action_space_dim
            )
            
            self.target_net.apply(init_weights)
            
        # Load model from state dict
        if model_state_dict is not None and optimizer_state_dict is not None:
            self.online_net.load_state_dict(model_state_dict)
            

        # Initialize both with the same weight
        self.target_net.load_state_dict(self.online_net.state_dict())
        
        self.target_net = self.target_net.to(device)
        self.online_net = self.online_net.to(device)
        
        
        # Initialize optimizer with online_net 
        self.optimizer = T.optim.AdamW(self.online_net.parameters(), lr=learning_rate)
        
        # Load optimizer from state dict
        if optimizer_state_dict is not None:
            self.optimizer.load_state_dict(optimizer_state_dict)
            
        
        self.replay_buffer = deque(maxlen=replay_buffer_size)
        self.min_replay_size = min_replay_size
        
        self.reward_buffer = deque([0.0], maxlen=reward_buffer_size)
        
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.gamma = gamma
        self.step = step
        
    def choose_action(self, legal_actions, game_state):
        epsilon = np.interp(self.step, [0, self.epsilon_decay], [self.epsilon_start, self.epsilon_end])
        use_random = random.random() <= epsilon

        action = None
        if use_random:
            # pick legal action given uniform distribution
            action = np.random.choice(legal_actions, 1, [1/len(legal_actions) for i in legal_actions])
            action = game_actions_list.index(action)
        else: 
            # Copy game state so we dont have to send it back to cpu after compute
            game_state_copy = game_state.copy()
            game_state_copy = T.as_tensor(game_state_copy).to(self.device)
            q_values = self.online_net.act(game_state_copy)
            # Get index of best action
            action = T.argmax(q_values, axis=0)
            # Send game_state and action to cpu so we can save it into replay memory
            action = action.cpu().data.numpy()
            
        self.step += 1
        
        return action
    
    def learn(self):
        # Start Gradient Step
        transitions = random.sample(self.replay_buffer, self.batch_size)

        all_obs = np.vstack([t[0] for t in transitions])
        all_actions = np.asarray([t[1] for t in transitions], dtype=np.int64)
        all_rews = np.asarray([t[2] for t in transitions], dtype=np.float32)
        all_dones = np.asarray([t[3] for t in transitions], dtype=np.float32)
        all_new_obs = np.vstack([t[4] for t in transitions])


        obs_t = T.as_tensor(all_obs).to(self.device)
        actions_t = T.as_tensor(all_actions).unsqueeze(-1).to(self.device)
        rews_t = T.as_tensor(all_rews).to(self.device)
        new_obs_t = T.as_tensor(all_new_obs).to(self.device)
        dones_t = T.as_tensor(all_dones).to(self.device)
        
        # Zero our gradients before training
        self.optimizer.zero_grad() 

        # Compute Targets
        target_q_values = self.target_net(new_obs_t)
        max_target_q_values = target_q_values.max(dim=1, keepdim=True)[0]


        targets = rews_t + self.gamma * (1 - dones_t) * max_target_q_values

        # Compute Loss
        q_values = self.online_net(obs_t)
        action_q_values = T.gather(input=q_values, dim=1, index=actions_t)

        # Calculate loss
        loss = self.loss(action_q_values, max_target_q_values).to(self.device)

        # Gradient Descent
        loss.backward()
        self.optimizer.step()
        
        # Update Target Network
        if self.step % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.online_net.state_dict())
    
    def save_transition(self, transition):
        self.replay_buffer.append(transition)
        
    def save_reward(self, episode_reward):
        self.reward_buffer.append(episode_reward)

    def get_name(self):
        return self.player.get_id()