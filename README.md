# Deep Reinforcement Learning: Teaching an Agent to play Argentine Truco through Self-Play


  The goal of this paper is to teach an unsupervised agent to play the traditional Argentine card game of Truco. The agent should, through trial and error and without any previous knowledge, learn the rules of the game and progressively become more proficient at it. The Agent’s goal is to find and implement new strategies that allow it to consistently win, while continuously improving upon previous iterations. The aspiration is that the agent will be able to conjure some sort of creativity to possibly uncover new meaningful strategies to play the game of Truco.


## **Approach** 
_basic knowledge of Truco is expected when reading._

  Unsupervised agents will play against each other in a game 1v1 Truco environment. This will effectively generate a plethora of possible game states for the agent to explore and act upon. Each action played will allow the agent to refine its policy to effectively maximize its expected future cumulative reward. 
	
  The reward is denoted as in-game points. The environment's reward policy will mimic that of Argentine Truco. In Truco, points are earned by winning small wagers. The first player to reach 30 points is the winner. There are two wagers that can be played every hand dealt: Envido and Truco. Both wagers have a set of calls and raises; each with their own respective bet. Envido has three calls: envido, real envido, falta envido. Their possible combinations are:

- envido, no quiero = +1
- envido, quiero = +2
- envido, envido, quiero = +4
- envido, real envido, quiero = +5
- envido, envido, no quiero = +2
- envido, real envido, no quiero = +3
- real envido, quiero = +3
- real envido, no quiero = +2

Truco has three calls: truco, retruco, vale cuatro. Their possible combinations are:

- truco, no quiero = +1
- truco, quiero = +2
- truco, re-truco, no quiero = +2
- truco, re-truco, quiero = +3
- truco, quiero vale cuatro, quiero = +4
- truco, quiero vale cuatro, no quiero = +3

_*Any illegal moves performed by the agent during play will result in an immediate forfeit._


## Model Evaluation

  Five players will be selected to play against the agent. Each player will play three games, resulting in a total of 15 games being played. Model performance will be evaluated based on the following metrics: 
- Win Rate (denoted as [games won]/[games played]) - The goal is to maximize this.
- Game duration (denoted in turns) - The goal is to minimize this.
- Points Conceded - The goal is to minimize this. 



### **Continue Reading**

https://docs.google.com/document/d/1piNtwfl80rUbxg6TNlFvWcsT8csIVHVhE_e34_uM-F0/edit?usp=sharing
