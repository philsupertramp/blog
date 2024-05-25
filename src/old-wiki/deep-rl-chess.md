---
tags:
 - old-wiki
 - published
title: Deep RL for chess
description: In this post I describe my findings and learning about reinforcement learning in the game of chess.
layout: mylayout.njk
author: Philipp
date: 2021-07-10
---
Source code can be found [here](https://github.com/philsupertramp/chess).
### The idea
The basic idea is to create a chess engine combined with a playable game.
Before playing the user can chose between different pre-trained models, a GUI version of the game and  a headless CLI version.

The game itself and the headless version is implemented in [chess](https://github.com/philsupertramp/chess), therefore I will not go into details how to implement a game using Python.
I decided to use the [`pygame`](https://pypi.org/project/pygame/) project to do the heavy lifting of graphics processing and input handling.

### Initial approach
In the beginning I implemented a regular reinforcement learning model.  
For that I implemented an agent and an environment.  
The environment class' purpose is to hold the current state of the game and needs to be capable
of computing the state after an action has been performed. Meaning the environment class not only holds
the current state, it also holds the state for any following state after an action. Short
\(s_n\) and \(s_{n+1}\).  
The state is a \([8x8]\)-Matrix representing the game board. The initial state looks like
$$
\begin{pmatrix}
5 & 3 & 3 & 9 & 100 & 3 & 3 & 5\\\\
1 & 1 & 1 & 1 &    1 & 1 & 1 & 1\\\\
0 & 0 & 0& 0 &     0 & 0 & 0 & 0\\\\
0 & 0 & 0& 0 &     0 & 0 & 0 & 0\\\\
0 & 0 & 0& 0 &     0 & 0 & 0 & 0\\\\
0 & 0 & 0& 0 &     0 & 0 & 0 & 0\\\\
1 & 1 & 1 & 1 &    1 & 1 & 1 & 1\\\\
5 & 3 & 3 & 9 & 100 & 3 & 3 & 5
\end{pmatrix}
$$

The agent holds a Sequental-Model tailored for the input values we get from the environment.  
The model consisted of 4 layers:

- 3 dense layers with 64 neurons each
- 1 output dense layer with 4-dimensional output values

```python
Model: "sequential"
_________________________________________________________________
Layer (type)                 Output Shape              Param #   
=================================================================
dense (Dense)                (None, 1, 8, 64)          576       
_________________________________________________________________
dense_1 (Dense)              (None, 1, 8, 64)          4160      
_________________________________________________________________
dense_2 (Dense)              (None, 1, 8, 64)          4160      
_________________________________________________________________
dense_3 (Dense)              (None, 1, 8, 4)           260       
=================================================================
Total params: 9,156
Trainable params: 9,156
Non-trainable params: 0
```

To keep predictions consistent during the training phase the agent holds a second model equally to the training model for prediction targets, this second model
will be updated every `UPDATE_TARGET_EVERY` steps and will be used to validate the prediction of the training model.  
Using this second model we achieve a consistency in predictions, while the agent is allowed to freely explore the environment.  

As earlier mentioned the output values of the models are 4-demensional, an example:

```python
[[ 2.3008184e-01 -1.4492449e-01 -2.9498902e-01 -4.9934822e-01]
 [ 9.2305988e-04  7.2111059e-03 -5.2097915e-03 -2.9294785e-02]
 [-9.8136133e-03 -2.4896236e-03 -3.5403362e-03 -5.2478639e-03]
 [-9.1470964e-04  6.2038745e-03 -5.6211166e-03 -9.8542329e-03]
 [-1.4108000e-03  1.5814116e-03 -1.0969832e-03 -3.5430947e-03]
 [-2.2000135e-03  2.7022450e-03 -1.9933917e-03 -5.8960477e-03]
 [-2.0452226e-03 -2.7348497e-04 -1.8162774e-03 -5.0680051e-03]
 [-3.2047349e-01 -1.1664207e-01 -3.1540787e-01 -1.7664778e-01]]
```

applying `max()` onto the output matrix to retrieve the row with max values results in the new action.  
 To allow further exploration a parameter \(\epsilon\) was introduces to allow gradual decreasing probability
 of exploring a random move. The parameter will be reduced by a factor of `EPSILON_DECAY` each episode until
 a minimum of `MIN_EPSILON` is reached.

![myplot](https://user-images.githubusercontent.com/9550040/131493372-3e4e83d7-7299-45b1-a910-a86c4bad8761.png)

Rewards are chosen fairly simple. Each iteration we check the state and generate an approximated outcome by computing the sum over all values in game.
Meaning each piece gets a value and we compute their sum, handling black pieces as negative values and white as positive ones.
$$
\sum \lambda v
$$
with
$$
\lambda = \left\\{\begin{matrix}1 & \text{if is white}\\\\ -1 & \text{else}\end{matrix}\right.
$$
## New idea
This approach was found in several other implementations including 
[jonzia/Chess_RL](https://github.com/jonzia/Chess_RL).

The general idea is to bypass the phase were we train the model to select right moves based on a given state.
This selection process can be simplified by arguing:
> If one wants to learn chess, it can be presupposed that one will be able to look up allowed moves for each piece.

Having that out of the way we can fully focus on training the agagent to select the right action. Yet we need to redefine the action space
as well as the current reward approach.


## Improvements
After reading [this paper](https://arxiv.org/pdf/1902.00183.pdf) I had a better understanding how to handle rewards and penalties
as well as how to configure the training pipeline in such way that we can achieve proper learing and reduce the probability of
exploiting the rewarding system.

That being said I started implementing several things:

1. A base reward of N
2. maximum number of steps during one episode
3. use step penalties
4. reward positive outcomes


