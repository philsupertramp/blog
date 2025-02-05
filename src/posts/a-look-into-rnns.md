---
tags:
 - post
 - published
title: A Look Into RNNs
layout: mylayout.njk
author: Philipp
description: RNN is good, LSTM is better, GRU is the boss
date: 2025-02-04
---


## RNN
When processing things on larger scale, for instance understanding who a pronoun refers to, or how a stock's price changed over time, classical linear neural network architectures fail to be as flexible as the data would require them to be.

To be able to include a context to the model prediction, allowing it to consider more than the direct input, David Rumelhart introduced in 1986 early concepts of Recurrent Neural Networks, short RNNs.

### What are RNNs?
RNNs are neural networks that use feed-forward NNs over time, which adds internal memory to the network.

This _internal memory_ originates from the functionality of the network. Each node inside the network considers the past computations from previous nodes.

So instead of computing $y = f_i(x_i)$, we use $y = f_i(x_i, f_{i-1}(x_{i-1}))$.

Now, let's see how such networks might look like.

```text
           y^{1}           y^{2}                           y^{t}
            ^               ^                               ^
            |               |                               |
-(a^{0})> [A_1] -(a^{1})> [A_2] -(a^{2})> ... -(a^{t-1})> [A_t] -(a^{t})> ...
            ^               ^                               ^
            |               |                               |
           x_{1}           x_{2}                           x_{t}
```
As visualized, each Node ($A_i$) receives input $a^{i-1}$ and $x_i$ and yields $y^i$.

Next we look a little closer into the $A_i$ nodes.

In each node, we compute the following:

```python
# input: a^{t-1} = a1, x_{t} = x

aw = a1 * w_aa
xw = x * w_ax

axb = aw + xw + b_a
gaxb = dot(axb, g_1)
gya = gaxb * w_ya
gby = gya + b_y
y = dot(gby, g_2)
at = gaxb
```

here `w_aa`, `w_ax` and `w_ya` are weights, `b_a` and `b_y` are bias terms and `g_1` and `g_2` are activation functions.

Hence, for each timestep $t$, we can express the activation $a^{t}$ and the output $y^{t}$ as follows

$$
a^{t} = g_1(W_{aa}a^{t-1}+W_{ax}x_t+b_a)
$$
and
$$
y^t = g_2(W_{ya}a^t + b_y)
$$

Initially, $a^{t-1}$ with $t = 1$ is $0\Rightarrow a^0 = 0$.

Same as with regular NNs a forward pass doesn't update the models weights. To reach a global minima an algorithm like gradient descent is required to update the weights.

Once the loss between $y$ and $y^t$ is computed we can apply backpropagation to do that.

For RNNs the loss function $L$ is defined as
$$
L(\hat{y}, y) = \sum\limits_{t=1}^{T_y} L(\hat{y}^t, y^t)
$$

To compute the derivate of $L$ in backpropagation with respect to the weight matrix $W$ we calculate

$$
\frac{\partial L^{(T)}}{\partial W} = \left. \sum \limits_{t=1}^{T} \frac{\partial L^{(T)}}{\partial W} \right |_{(t)}
$$

With that being said, there are some issues that RNNs have.

1. they don't consider the future, only data from the past
2. *Vanishing Gradient*: when using sigmoid as activation function the derivate is in $(0, 0.25]$. When passed towards the first layer, it will be nearly $0$ due to the multiplications that happen along the way.
3. *Exploding Gradient*: A similar issue arrises when using ReLU, but instead of getting a very small gradient, we will end up with a very big one.

Issue #2 and #3 are of similar nature and result from the multiple multiplications during the backpropagation.


The following is an example implementation of an RNN in pure PyTorch
```python
import torch.nn as nn
import torch
from torch.nn import functional as F


param = lambda shape, factor: nn.Parameter(torch.randn(*shape) * factor)


class RNNCell(nn.Module):
    def __init__(self, input_dim, hidden_size):
        super().__init__()
        self.w_aa = param([input_dim, hidden_size], 0.1)
        self.w_ax = param([input_dim, hidden_size], 0.1)
        self.w_ya = param([input_dim, hidden_size], 0.1)
        self.b_a = param([hidden_size], 0.0)
        self.b_y = param([hidden_size], 0.0)

        self.g_1 = F.tanh
        self.g_2 = F.tanh

    def forward(self, x, h_c):
        gaxb = self.g_1((h_c * self.w_aa) + (x * self.w_ax) + self.b_a)
        y = self.g_2((gaxb @ self.w_ya) + self.b_y)
        return gaxb, y
```

For more on RNNs and the upcoming section of LSTMs you can refer to [Andrej Karpathy's blog](http://karpathy.github.io/2015/05/21/rnn-effectiveness/).


## RNN issues
One major advantage of RNNs over regular NNs is the idea that they might be able to connect previous information to a present task, for instance using a previous article to understand the meaning of a new article.

Are RNNs capable of doing that? This depends on the task.

Consider for instance a language model trying to predict the next word based on the previous words.
If we try to predict the last word in the sentence 
> "A red fox jumps over the lazy _dog_"

it's obvious that the it should be "_dog_".

In such cases, when the gap or distance between the relevant information and the current location is very small, RNNs can learn to use information from the past.

Now consider another case, a long article about a person. Initially this person introduce themselves and states "While growing up in Germany." and several sentences later continues with "Thanks to my native language ...".

The current/present information suggests to predict a name of a language as next word, but to be able to determine which language is desired, the context from the beginning of the article is required.

Now for small distances/gaps this will work again, but imagine the gap being several paragraphs of text.

As the distance between relevant information and the current predicition increases, RNNs struggle to retain long-term dependencies.
There are some ways how one can achieve good quality results using RNNs on big context windows/long-term dependencies, but they have been proven to only work on toy examples.

Hochreiter explored this in depth in their diploma thesis ([Hochreiter Dipl.](https://people.idsia.ch/~juergen/SeppHochreiter1991ThesisAdvisorSchmidhuber.pdf)) and [Bengio et. al](http://www.comp.hkbu.edu.hk/~markus/teaching/comp7650/tnn-94-gradient.pdf) dug deeper into the reasons for it.

With that being said, an improved version was invented, called LSTM, Long Term Short Term.

A deep learning architecture created by Hochreiter & Schmidhuber in 1997 based on RNNs and has been a prominent architecture for natural language processing.

LSTMs are a special kind of RNN, which can remember long term dependencies.

## LSTM

Since it's introduction many people improved the popular architecture. Thanks to all the improvements LSTMs work very well on a large variety of problems.

The main design difference between LSTMs and regular RNNs is that they explicitly avoid the long-term dependency problem.
Instead, recalling information for long periods of time is the default behavior of LSTMs.

Architecture-wise, without considering the internals of a Node, there's no difference between LSTMs and RNNs. Each node get's the original input $x_i$ and the output of the previous node $y_{i-1}$ as an input.

Looking into the nodes themselves, there is a great difference.

If we consider the RNN cell/node to have one NN layer, then LSTMs have four layers, all interacting in a special way.


```
                                                   (a^t)
                                                     ^
(C_{t-1})---->(x)-------------->(+)-------------+----|----->(C_t)
               ^                 ^              |    |
               |                 |              |    |
               |                 |           [\tanh] |
               |                 |              |    |
               |        +------>(x)      +---->(x)   |
               |        |        |       |      |    |
           [\sigma] [\sigma] [\tanh] [\sigma]   |    |
(a^{t-1})->----+--------+--------+-------+      +----+----> a^t
               |
              x_t
```

-------
Legend:
- $C_{t-1}$ represents the cell state of the previous cell
- $C_t$ is the current cells state
- $a^{t-1}$ represents the hidden state of the previous cell
- $a^t$ is the hidden state of the current cell
- Pointwise operations are denoted by `(...)` bracelets
- NN layers are visualized using `[...]` bracelets

-------

An implementation of such LSTM cell could look like this

```python
import torch


class LSTMCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.w_x = param([input_size, hidden_size * 4], 0.1)
        self.w_h = param([input_size, hidden_size * 4], 0.1)
        self.b = param([hidden_size * 4], 0.0)
    
    def forward(self, x, h_c):
        h, c = h_c
        gates = torch.mm(x, self.w_x) + torch.mm(h, self.w_h) + self.b
        i, f, o, g = torch.chunk(gates, 4, dim=1)
        i, f, o, g = torch.sigmoid(i), torch.sigmoid(f), torch.sigmoid(o), torch.tanh(g)
        c_next = f * c + i * g
        h_next = o * torch.tanh(c_next)
        return h_next, c_next
```

### Core Ideas behind LSTMs
Let's dive deeper into the architecture of LSTMs.

The key to success in LSTMs is the cell state, this is denoted by the horizontal line passing through the top of the node in the diagram.

The cell state runs straight through the entire node, with only some minor linear interactions, which makes it very easy for information to flow along without major changes.

The LSTM-cell has the ability to remove or add information to this cell state,                   carefully regulated by structures called _gates_.

Gates are a way to manipulate the cell state. They are composed out of a sigmoid NN layer  and a pointwise multiplication operation.

The neural network layer produces outputs $\in [0, 1]$, describing how much of each component should be passed through.
A value of zero means blocking all, while a value of one considers all of it's content.

LSTMs-cells consist of three of these gates, to protect and control the cell state.

### A walk through

Alright, now we're aware of the building blocks for LSTM cells. Let's look into it step-by-step. I will use the diagram from before and gradually fill it while describing steps.
Keep in mind that all intermediate results are required for each cell to compute its outputs.

```
                                                   (a^t)
                                                     ^
(C_{t-1})---->(x)-------------->(+)-------------+----|-----> C_t
               ^                 ^              |    |
               |                 |              |    |
               |                 |            [...]  |
               |                 |              |    |
               |        +------>(x)      +---->(x)   |
               |        |        |       |      |    |
           [\sigma]   [...]    [...]   [...]    |    |
(a^{t-1})->----+--------+--------+-------+      +----+----> a^t
               |
              x_t
```
The first step in the LSTM is to decide which information is used inside the cell state.
This decision is made by a sigmoid layer called the "forget gate layer".

It considers $a^{t-1}$ and $x_t$ and outputs a value $\in [0, 1]$ for each element of the previous' cell state $C_{t-1}$.

We can formulate this as

$$
f_t = \sigma\left(W_f \cdot \left[a^{t-1},x_t\right ] + b_f \right)
$$
```
                                                   (a^t)
                                                     ^
(C_{t-1})---->(x)-------------->(+)-------------+----|-----> C_t
               ^                 ^              |    |
               |                 |              |    |
               |                 |            [...]  |
               |                 |              |    |
               |        +------>(x)      +---->(x)   |
               |        |        |       |      |    |
             [...]  [\sigma] [\tanh]   [...]    |    |
(a^{t-1})->----+--------+--------+-------+      +----+----> a^t
               |
              x_t
```

The second step is to decide what new information will be stored in the cell state.
This step consists of two parts. First, a sigmoid layer called "input gate layer", which decides which values to update $i_t$. The second part is a tanh layer. This layer creates a vector of the next candidate values $\tilde{C}_t$, which should be added to the state.

$$
i_t = \sigma\left(W_i \cdot \left[a^{t-1}, x_t\right] + b_i\right)
$$
$$
\tilde{C}_t = \tanh\left(W_C\cdot \left[ a^{t-1}, x_t \right] + b_C\right)
$$
```
                                                    (a^t)
                                                      ^
(C_{t-1})---->(x)-------------->(+)-------------------|-----> C_t
               ^                 ^               |    |
               |                 |               |    |
           f_t |                 |             [...]  |
               |        |------>(x)              |    |
               |    i_t |        |       |----->(x)   | 
               |        |    C_t |       |       |    |
             [...]    [...]    [...]   [...]     |    |
(a^{t-1})->----+--------+--------+-------+       +----+----> a^t
               |
              x_t
```

Once \[(\tilde{C}_t\] and $i_t$ are computed, it's time to update the old cell state $C_{t-1}$ into the new state $C_t$.

This is done by multiplying the old state $C_{t-1}$ by $f_t$, which essentially makes the cell forget about the things that were decided to forget earlier.
Then add $i_t \cdot \tilde{C}_t$, this yields the new candidate values for the state, scaled by how much it was decided to update each state value.
```
                                                    (a^t)
                                                      ^
(C_{t-1})---->(x)-------------->(+)--------------+----|-----> C_t
               ^                 ^               |    |
               |                 |               |    |
               |                 |            [\tanh] |
               |        +------>(x)              |    |
               |        |        |       |----->(x)   | 
               |        |        |       |       |    |
             [...]    [...]    [...]  [\sigma]   |    |
(a^{t-1})->----+--------+--------+-------+       +----+----> a^t
               |
              x_t
```

Finally, the decision is done of what will be the output.
This output will be the cell state, but filtered.

First, we run a sigmoid layer ($o_t$) which decides what parts of the cell state we're going to output. Then we put the cell state through $\tanh$ (to squeeze the values into $[-1, 1]$) and multiply it by the output of the sigmoid gate, so that it only outputs the parts we decided to.

This formula for $o_t$ and $a^t$ are given as
$$
o_t = \sigma\left(W_o\left[a^{t-1}, x_t\right] + b_o\right)
$$
and
$$
a^t = o_t \cdot \tanh\left(C_t\right)
$$

### Variations of LSTMs
So far we looked into the _pretty_ normal LSTM architecture.  
But not all LSTMs are the same. In fact, almost every paper involving LSTMs uses a slightly different approaches. Most of these differences are minor, but it's worth mentioning the most common variations.

#### Peephole LSTM
One of these popular approaches is the "peephole" LSTM, which is called like this due to it's "peephole connections".
Essentially, in this approach the individual gates are able to look at the cell state.

```
                                                      (a^t)
                                                        ^
(C_{t-1})+---->(x)-------------->(+)----+----------+----|----->(C_t)
         |      ^                 ^     |          |    |
         |      |                 |     |       [\tanh] |
         |      |                 |     |          |    |
         |      |        +------>(x)    |   ----->(x)   |
         |      |        |        |     v   |      |    |
         | [\sigma] [\sigma]   [\tanh] [\sigma]    |    |
         |   ^  |     ^  |        |       |        |    |
         +---+--|-----+  |        |       |        |    |
(a^{t-1})-->----+--------+--------+-------+        +----+----->(a^t)
                ^
                |
               x_t
```
This results in only the $\sigma$-gates being adjusted, the new formulas change to
$$
f_t = \sigma\left(W_f \cdot \left[C_{t-1}, a^{t-1}, x_t\right] + b_f\right)
$$
$$
i_t = \sigma\left(W_i \cdot \left[C_{t-1}, a^{t-1}, x_t\right] + b_i\right)
$$
$$
o_t = \sigma\left(W_o \cdot \left[C_{t-1}, a^{t-1}, x_t\right] + b_o\right)
$$

The above diagram adds peepholes to all of the gates, but in many publications the authors give some gates peepholes and others not.

<u>With that being said, it's smart to try out different variations for the same task.</u>

#### Coupled LSTM
Another variant is to use coupled forget and input gates. Instead of separately deciding what to forget and what to add, those decisions are done jointly.
```
                                                   (a^t)
                                                     ^
(C_{t-1})---->(x)-------------->(+)-------------+----|-----> C_t
               ^                 ^              |    |
               |                 |              |    |
               +------(1-)------>|            [...]  |
               |                 |              |    |
               |        +------>(x)      +---->(x)   |
               |        |        |       |      |    |
             [...]    [...]    [...]   [...]    |    |
(a^{t-1})->----+--------+--------+-------+      +----+----> a^t
               |
              x_t
```

This change would only affect $C_t$
$$
C_t = f_t * C_{t-1} + (1-f_t) * \tilde{C}_t
$$

Using the coupled gates will yield a model with reduced amount of parameters, which can in scale decrease the training time.

#### Gated Recurrent Unit
A slightly more dramatic variant of the LSTM is the Gated Recurrent Unit, short GRU, introduced by [Cho et al. (2014)](https://arxiv.org/pdf/1406.1078v3).

GRU combines the _forget_ and _input_ gates into a single _update_ gate. Apart from that it also merges the cell state with the hidden state and makes some other changes.

This results in a simpler architecture than the LSTM models that experiences great popularity.
Unfortunatey, the diagram get's more complex on first glance.

```
                                                     (a^t)
                                                       ^
(a^{t-1})-+-----+--------------->(x)------------(+)----|----->
          |     |                 ^              ^
          |     |               (1-)             |
          |    (x)<------+        |              |
          |     |    r_t |        |------------>(x)
          |     |        |    z_t |              | 
          |     |     [\sigma]    |              | \tilde{a^t}
          |     |        |     [\sigma]       [\tanh]
           >----|--------+--------+              |
          |     |                                |
          |     v                                |
           >-------------------------------------+
          ^
          | 
         x_t
```

These changes yield the functions
$$
z_t = \sigma\left(W_z \cdot \left[a^{t-1}, x_t\right]\right)
$$
$$
r_t = \sigma\left(W_r\cdot \left[a^{t-1}, x_t\right]\right)
$$
$$
{\tilde{a}}^{t} = \tanh\left(W \cdot \left[r_t * a^{t-1}, x_t\right]\right)
$$
$$
a^t = (1-z_{t}) * a^{t-1} + z_t * \tilde{a}^t
$$
But also the inputs change, each node doesn't receive $C^{t-1}$ but actually only $a^{t-1}$ and $x_t$.

As mentioned earlier GRUs have a simpler architecture than regular LSTMs, due to the fact that GRUs merge the cell state and the hidden state, which can sometimes lead to faster training.

A possible implementation for the GRU-cell could look like this
```python
class GRUCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.w_x = param([input_size, hidden_size * 3], 0.1)
        self.w_h = param([input_size, hidden_size * 3], 0.1)
        self.b = param([hidden_size * 3], 0.0)
    
    def forward(self, x, h):
        gates = torch.mm(x, self.w_x) + torch.mm(h, self.w_h) + self.b
        r, z, n = torch.chunk(gates, 3, dim=1)
        r, z = torch.sigmoid(r), torch.sigmoid(z)
        n = torch.tanh(torch.mm(x, self.w_x[:, :self.hidden_size]) + r * torch.mm(h, self.w_h[:, :self.hidden_size]))
        h_next = (1 - z) * n + z * h
        return h_next
```


## Conclusion
These are only three of the most notable LSTM variants, but there are plenty more.

Which of these variants is the best? Are the differences noticable?

These questions where explored by [Greff, et al. (2015)](http://arxiv.org/pdf/1503.04069.pdf), which resulted in no meaningful differences.
In 2015 [Jozefowicz, et al.](https://proceedings.mlr.press/v37/jozefowicz15.pdf) explored more than ten thousand RNN architectures, finding that some work better than LSTMs on certain tasks.

In this post we discovered the RNN architecture and looked into the next big step of improvements, LSTMs.

We briefly motivated several approaches for cells inside an LSTM that solve different issues.

LSTMs were a huge step in improving RNNs, so the next question would most likely be: "What's the next big step?".

Most researchers will probably state _Attention_ or _Transformers_.

Soon, we will look a bit further into the transformers architecture that is powered by the attention mechanism.

You can read more already about it in its original paper "Attention Is All You Need" by [A. Vaswani et al. (2017)](https://arxiv.org/pdf/1706.03762).


---------------

## Reading Resources

- [https://colah.github.io/posts/2015-08-Understanding-LSTMs/
](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)
- [https://medium.com/nerd-for-tech/understanding-rnn-91d548c86ac9
](https://medium.com/nerd-for-tech/understanding-rnn-91d548c86ac9)
- [http://karpathy.github.io/2015/05/21/rnn-effectiveness/
](http://karpathy.github.io/2015/05/21/rnn-effectiveness/)
- [https://arxiv.org/pdf/1406.1078v3](https://arxiv.org/pdf/1406.1078v3)
- [https://people.idsia.ch/~juergen/SeppHochreiter1991ThesisAdvisorSchmidhuber.pdf
](https://people.idsia.ch/~juergen/SeppHochreiter1991ThesisAdvisorSchmidhuber.pdf)
- [https://stanford.edu/~shervine/teaching/cs-230/cheatsheet-recurrent-neural-networks
](https://stanford.edu/~shervine/teaching/cs-230/cheatsheet-recurrent-neural-networks)

