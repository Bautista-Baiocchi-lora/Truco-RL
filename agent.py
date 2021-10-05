import torch as T
from torch import nn
from collections import deque
import itertools
import numpy as np
from actions import game_actions_list
import random

def load_agent(name):
    return T.load(f"./model_saves/model-v4-{name}.pt")

class DQNetwork(nn.Module):
    
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
    def __init__(self, 
                 player, 
                 state_space_dim, 
                 action_space_dim, 
                 device, 
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
                 gamma=0.99
                ):
        
        self.player = player
        self.loss = loss
        self.device = device
        
        # ever how many steps the online_net params should be saved to disk
        self.save_freq = save_freq
        
        # Initialize the NNs
        self.online_net = DQNetwork(
            state_space_dim, 
            action_space_dim
        ).to(device)

        self.target_net = DQNetwork(
            state_space_dim, 
            action_space_dim
        ).to(device)

        # Initialize both with the same weight
        self.target_net.load_state_dict(self.online_net.state_dict())

        # Initialize optimizer with online_net 
        self.optimizer = T.optim.Adam(self.online_net.parameters(), lr=learning_rate)
        
        self.replay_buffer = deque(maxlen=replay_buffer_size)
        self.min_replay_size = min_replay_size
        
        self.reward_buffer = deque([0.0], maxlen=reward_buffer_size)
        
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.gamma = gamma
        self.step = 0
        
    def choose_action(self, legal_actions, game_state):
        epsilon = np.interp(self.step, [0, self.epsilon_decay], [self.epsilon_start, self.epsilon_end])
        use_random = random.random() <= epsilon

        action = None
        if use_random:
            # pick legal action given uniform distribution
            action = np.random.choice(legal_actions, 1, [1/len(legal_actions) for i in legal_actions])
            action = game_actions_list.index(action)
        else: 
            # Compute Q-Values
            game_state = T.as_tensor(game_state).to(self.device)
            q_values = self.online_net.act(game_state)
            # Get index of best action
            action = T.argmax(q_values, axis=0)
            # Send game_state and action to cpu so we can save it into replay memory
            game_state = game_state.cpu().data.numpy()
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
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update Target Network
        if self.step % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.online_net.state_dict())
    
    def save_transition(self, transition):
        self.replay_buffer.append(transition)
        
    def save_reward(self, episode_reward):
        self.reward_buffer.append(episode_reward)
        
    def save_model(self, name=None):
        name = self.get_name() if name is None else name
        T.save(self.online_net.state_dict(), f"./model_saves/model-v4-{name}.pt")
        print(f"Model {name} saved. \r")

    def get_name(self):
        return self.player.get_id()