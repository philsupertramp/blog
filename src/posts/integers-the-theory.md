---
tags:
 - post
 - published
 - integers
title: "Integers: The Theory"
layout: mylayout.njk
author: Philipp
description: In this post we'll discuss the theory behind integer native deep learning. 
date: 2026-03-12
---
<style>
table {border-collapse: collapse;, width: 50%} tr,table,th,td { border: 1px solid; }
</style>



_Part 2 of a series on native integer machine learning/deep learning_

#### Debug notes
After the [previous post]({{ "integers-training-neural-networks-without-floating-point" |  postsUrl }}) I jumped right into
debugging.

The increasing runtime in combination with the drastic difference between `lr_shift` and `momentum_shift` in the Iris example
gave me reason to believe that the code has a bug in regards to scaling (shifting values).

I am making this assumption out of two reasons.

First, both versions use different arithmetic operations. The `f32` uses raw arithmetic operators, e.g. `+` and `*`
whereas the `i32` uses saturating/wrapping arithmetic, i.e. values are either clipped or wrapped when overflowing.

Second, the `i32` version implements gradient clipping.

To get a clearer picture of the current state I added debugging statements to Iris test, checking runtime, overflow stats and outgoing shift of predictions.
The results were rather sobering; no wrapping, compute time per epoch is between 2700 - 3000µs (micro seconds). This could be influenced by a [gamma ray from outer space](https://hackaday.com/2021/02/17/cosmic-ray-flips-bit-assists-mario-64-speedrunner/).
So not really a great measurement for tracking down bugs.

Looking at the shifts of the network revealed something different.

For every training sample we see inside the logs

```text
Epoch #     Loss   Shift In    Forward Shift   Backward Shift
Epoch 1     XXXXXX      5           16              16
Epoch 2     XXXXXX      5           16              16
Epoch 3     XXXXXX      5           16              16
...
```
This doesn't look correct. Especially the backward shift looks completely wrong.

The layers are configured the following way

| Layer | Quant Shift | Incoming Shift | Outgoing Shift |
|:----- | -----------:| --------------:| --------------:|
| L1    | 0           | 3              | 4              |
| L2    | 0           | 4              | 4              |
| L3    | 0           | 4              | 2              |


Our input is created with the `QuantizationMethod::StandardScore`, so it carries a shift of `5`.

The calculation for the final shift of the forward pass $s_o$ is 
$$
\begin{align}
s_o = s_i + \sum_{k=1}^N s_{i_k} + s_{q_k}
\end{align}
$$
with $s_i$ the original input shift, $s_{i_k}$ the input shift of the $k$-th layer and $s_{q_k}$ the quantization
shift of layer $k$.

In our example
$$
\begin{align}
s_o = 5 + (3 + 0) + (4 + 0) + (4 + 0) = 5 + 3 + 4 + 4 = 16
\end{align}
$$

This shows that our forward pass is already computing the correct shift.
The backward pass should reduce this shift again, but it doesn't. Hence an issue is inside the backward pass.

A fresh set of eyes was one of the main drivers behind the initial solution. After adjustment we ran the experiment again.

Architecture: `4 -> 8 -> 8 -> 3` with ReLU activations and MSE loss.

<u>We now reach **higher** accuracy on i32</u> compared to its f32 counter implementation.
The i32 branch converges within 239 epochs reaching an accuracy of 95%, whereas f32 never reaches this level.

| | f32 | i32 |
|:-|-----:|-----:|
|Test accuracy | 90% | 95% |
| Epochs | 500 | 239 (early stopped) |
| `lr_shift` | 7 | 7 |
| `momentum_shift` | 1 | 1 |
| Batch size | 32 | 32 |
| Grad. Clip value | - | $2^{13}$ |

Reason for this "success" were two things. Fixing the internal shift bookkeeping, `Linear<S>`'s backward pass was using `Linear::output_shift` to transform the gradient w.r.t inputs. This resulted in wrong shifts for subsequent layers. And `Linear<S>`'s backward pass did not return a reduced `s_g` (gradient shift), but rather just forwarded the incoming value.
Apart from the bookkeeping, drastically increasing the gradient clip value to allow more information bytes flowing through the network helped to get more stable results.


The diff for the changes inside `Linear<S>::backward`
```diff
-        let local_delta_w = s_g + s_x;
+        let local_delta_w = s_g - s_x;
-        let local_delta_x = self.weights.quant_shift + self.output_shift;
+        let local_delta_x = self.weights.quant_shift + self.input_shift;
...
-        let s_g_prev = s_g;//.saturating_sub(local_delta_x);
+        let s_g_prev = s_g.saturating_sub(local_delta_x);
```

Especially the update to `s_g` was something I had implemented earlier, but forgot an didn't discover up until today.


#### Impact on MNIST
The change was clearly fixing _a_ bug, otherwise our performance on Iris would not look like this.
Running quickly some epochs shows that at least the increasing compute time issue that we had in the [previous post]({{ "integers-training-neural-networks-without-floating-point" |  postsUrl }}) is
resolved and we have a more stable value there
```text
 Epoch         Loss     Accuracy    Time(s)   Clamps FW Shift BW Shift
────────────────────────────────────────────────────────────────────────────────
     0    1612.0000         9.4%       9.12s       -1    31    5
     1    1612.0000         9.4%       9.09s       -1    31    5
     2    1612.0000         9.4%       9.08s       -1    31    5
     3    1612.0000         9.4%       9.09s       -1    31    5
     4    1612.0000         9.4%       9.08s       -1    31    5
     5    1612.0000         9.4%       9.08s       -1    31    5
     6    1612.0000         9.4%       9.07s       -1    31    5
     7    1612.0000         9.4%       9.10s       -1    31    5
     8    1612.0000         9.4%       9.08s       -1    31    5
     9    1612.0000         9.4%       9.09s       -1    31    5
```

{% tip "Obviously, the network in these logs did not learn anything, instead pay attention to the now more or less stable runtime." %}

## The core math
Right now, we're adjusting things and seemingly fix issues that we don't fully understand.
Instead of running around like a headless chicken, we will now look closer into the theory
behind the implementation of native integer training.
After we defined all the required theory, we will implement it and hopefully resolve all issues we faced so far, for good.

### Motivation

The fundamental problem with integer arithmetic is that multiplication accumulates scale.
When you multiply two integers, the result lives in a different "unit" than either operand,
and without an explicit mechanism to track and correct for that, values either explode or collapse
across layers in a artificial neural network.
The structure we want is one where the _scale_ is part of the value itself, so that every operation
is well-defined in terms  of what the numbers actually mean, not just what bits they hold.

### The carrier set

Let $\mathbb{Z}$ be the integers. Define the carrier set as the Cartesian product

$$
\begin{align}
\mathcal{D} = \mathbb{Z} \times \mathbb{Z}
\end{align}
$$

An element $x = (v, s) \in \mathcal{D}$ consists of a **mantissa** $v \in \mathbb{Z}$ and a **scale exponent** $s \in \mathbb{Z}$. The rational
number it encodes is given by the **interpretation map**

$$
\begin{align}
\[\[x\]\] = v \cdot 2^{-s}
\end{align}
$$

So a larger $s$ means the mantissa is "finer-grained", the unit each integer step represents is smaller.
A smaller $s$ (or negative $s$) means the value lives at a corser scale.

{% note "The formal definition admits $s\\in \\mathbb{Z}$, allowing negative scale exponents, which would represent values scaled <i>up</i> by a power of two rather than down. In the implementation, shift values are typed as <code>u32</code>, restricting $s\\geq 0$. This means the system can only represent dyadic rationals of magnitude $\\leq |v|$, never larger. The formal generality is retained here because the mathematical properties of the operations hold regardless, but any concrete instantiation should be understood as working in $\\mathbb{Z} \\times \\mathbb{N}_{0}$." %}



### Non-uniqueness

It is critical to note that $\mathcal{D}$ is a set of **representations**, not a set of distinct values.
Two elements $x_1 = (v_1, s_1)$ and $x_2 = (v_2, s_2)$ are said to be **equivalent**, written $x_1 \sim x_2$, if and only if they encode
the same rational number

$$
\begin{align}
x_1 \sim x_2 \Leftrightarrow v_1 \cdot 2^{-s_1} = v_2 \cdot 2^{-s_2}
\end{align}
$$

For instance, $(3, 2), (6,  3)$ and $(12, 4)$ all represent the rational $\frac{3}{4}$. This non-uniqueness is not a flaw, it is precisely what
gives the system its flexibility. The scale can be chosen to match the magnitude of the data at hand.

### Scale alignment

Before we can define addition and substraction, we need a way to bring two elements into a common representation.

Given $x_1 = (v_1, s_1)$ and $x_2 = (v_2, s_2)$, define the **target scale** $s^* = \max(s_1, s_2)$, which is the _coarser_ of the two scales.
The **alignment** of $x_i$ to scale $s^*$ is

$$
\begin{align}
\text{align}(x_i, s^*) = \left(\left\lfloor\frac{v\_i}{2^{s^\*-s\_i}}\right\rceil , s^{\*} \right)
\end{align}
$$
where $\left\lfloor ... \right\rceil$ denotes a stochastic down-scaling[^1](#stochastic-scaling) operation and $\frac{v\_i}{2^{s^\*-s\_i}}$ the aligned value according to the
target scale.

The element with the finer scale has its mantissa right-shifted (divided by $2^k$) to match the coarser unit.
This is the exact analogue of lining up decimal points before adding:

You can only add $1.27 + 1.3$ once they share the same number of decimal places.

Alignment is _lossy_ in general, i.e. the bits shifted out are gone for good.
This precision loss during alignment is the fundamental source of rounding error in this system, which is the equivalent
to floating-point roundoff.

<a name="stochastic-scaling"/>

### Stochastic scaling
Stochastic scaling/Requantization handles two things. **Rescaling** (adjusting the shift to a new target) and **clipping** (enforcing the hardware bit-width boundaries).

#### Rescaling
Let $x = (v_x, s_x) \in \mathcal{D}$ be an accumulated tuple, and $s_t \in \mathbb{Z}$ be the target shift such that $k = s_t - s_x \geq 0$.

We define the stochastic rounding function $\text{SR}(v, k): \mathcal{D} \rightarrow \mathcal{D}$ as:

$$
\begin{align}
\text{SR}(v, k) = \left\lfloor v \cdot 2^{-k} \right\rfloor + \mathbb{I}\left((v \mod 2^k) \gt U\right)
\end{align}
$$

where $U \sim \mathcal{U}\\{0, 2^k - 1\\}$ and $\mathbb{I}(\cdot )$ is the indicator function.

The requantization operator $\mathcal{R}: \mathcal{D} \times \mathbb{Z} \rightarrow \mathcal{D}$ is then defined as

$$
\mathcal{R}(x, s_t) = \left( \text{clip}\left( \text{SR}(v_x, s_t - s_x), \mathbf{Q}\_{\min}, \mathbf{Q}\_{\max}\right), s_t \right)
$$

where $\mathbf{Q}\_{\min}$ and $\mathbf{Q}\_{\max}$ represent the representable bounds of the target integer precision.
The function $\text{clip}$ is defined as:

Let $v \in \mathbb{Z}$ be an integer value, and let $\mathbf{Q}\_{\min}, \mathbf{Q}\_{\max} \in \mathbb{Z}$ represent the lower and upper bounds of the target
scale, where $\mathbf{Q}\_{\min} < \mathbf{Q}\_{\max}$.

$$
\text{clip}(v, \mathbf{Q}\_{min}, \mathbf{Q}\_{max}) = \begin{cases}
\mathbf{Q}\_{min} & \text{if } v < \mathbf{Q}\_{min} \\\\
v & \text{if } \mathbf{Q}\_{min} \le v \le \mathbf{Q}\_{max} \\\\
\mathbf{Q}\_{max} & \text{if } v > \mathbf{Q}\_{max}
\end{cases}
$$

We can derive the values of $\mathbf{Q}\_{\min}, \mathbf{Q}\_{\max} \in \mathbb{Z}$ based on the target bit-width $b \in \mathbb{N}^+$.

For targets for a signed two's complement integer (e.g. INT8 where $b = 8$):

$$
\begin{align}
\mathbf{Q}\_{\min} &= -2^{b-1} \\\\
\mathbf{Q}\_{\max} &= 2^{b-1} - 1
\end{align}
$$

For unsigned integer targets (e.g. UINT8):

$$
\begin{align}
\mathbf{Q}\_{\min} &= 0 \\\\
\mathbf{Q}\_{\max} &= 2^b - 1
\end{align}
$$


### Arithmetic operations

We can now define the four operations. All four preserve the invariant that the result is again an element of $\mathcal{D}$.
Let $x_1 = (v_1, s_1)$ and $x_2 = (v_2, s_2)$, and write $\hat{v} = \frac{v_i}{2^{s^\*-s_i}}$ for their aligned mantissas at $s^{\*} = \max(s_1, s_2)$.

**Addition** and **subtraction** require alignment first, then operate directly on mantissas

$$
\begin{align}
x_1 \oplus x_2 &= \left(\hat{v}_1 + \hat{v}_2, s^{\*}\right)\\\\
x_1 \ominus x_2 &= \left(\hat{v}_1 - \hat{v}_2, s^{\*}\right)
\end{align}
$$

**Multiplication** does not require alignment because the scales compose additively. The exact
product of two dyadic numbers has mantissa $v_1 \cdot v_2$ and scale $s_1 + s_2$. However,
the mantissa $v_1 \cdot v_2$ may be too large to store, so a **quantization shift** $q\in \mathbb{Z}$ is applied to rescale it 
back into a reusable range

$$
\begin{align}
x_1 \otimes x_2 = \left( \left\lfloor \frac{v_1 \cdot v_2}{2^q} \right\rceil, s_1 + s_2 - q \right)
\end{align}
$$

Note that the scale of the result is adjusted by $-q$ to compensate, so the encoded value is approximately preserved: $[[x_1 \otimes x_2]] \approx [[x_1]] \cdot [[x_2]]$

**Division** has the opposite problem. Integer division truncates, so a **precision shift** $p\in\mathbb{Z}$ is applied to the dividend **before** dividing,
in order to preserve low-order bits that would otherwise be lost

$$
\begin{align}
x_1 \oslash x_2 = \left( \left\lfloor \frac{v_1 \cdot 2^p}{v_2} \right\rceil, s_1 - s_2 + p \right)
\end{align}
$$

Again the scale is adjusted to compensate, so $[[x_1 \oslash x_2]] \approx \frac{[[x_1]]}{[[x_2]]}$.

#### A note on approximation

An important consequence of the above is that $(\mathcal{D}, \oplus, \otimes)$ is **not a ring**.
The operations are approximate, addition loses the bits shifted away during alignment and multiplication
loses the bits shifted away during quantization.
The choices of $q$ and $p$ are free parameters. Choosing them well is exactly the _shift management problem_ that sits at the heart
of integer neural network training.

The `lr_shift`, `quant_shift` and `grad_shift` parameters are all instances of this single decision appearing in different contexts.
This provides all necessary building blocks for the forward pass of a neural network using $\mathcal{D}$.

### Gradients

But this framework introduces a new problem.
Due to the randomness of $\text{SR}$, i.e. sampling from $\mathcal{U}$ and using $\mathbb{I}(\cdot)$, the forward pass becomes
non-differentiable.
This is a big problem, because we want to implement training of neural networks, which requires differentiable functions,
otherwise we can not compute the gradient with standard chain-rule calculus.
Unfortunately, $\text{SR}$ as well as $\text{clip}$ can both be considered step functions, meaning their true mathematical derivatives
are exactly zero almost everywhere.
The network would never train because the gradients would instantly vanish.

### Straight-Through Estimator

To overcome this we will formalize a Straight-Through Estimator (STE).
This STE essentially defines a "fake" derivative for the backward pass
that ignores the discrete steps and pretends the function was continuous.

Let $z = (W \otimes x) \oplus b$ be the high-precision accumulated tuple in $\mathcal{D}$ before requantization, so $y = \mathcal{R}(z, s)$.

During backpropagation, we receive the gradient of the loss w.r.t. $y$, denoted as $\nabla_y L\in \mathcal{D}$.
We need to compute the gradient w.r.t. $z$, denoted as $\nabla_z L\in \mathcal{D}$.

We break $\mathcal{R}$ into its two components and define the STE for each:

1. The STE for $\text{SR}$:

In continuous space, the rounding function is an approximation of the identity function (scaled by the bit-shift).
The STE assumes the gradient passes straight through the rounding operation unmodified.

$$
\begin{align}
\frac{\partial}{\partial z}\text{SR}(z, k) \approx 1
\end{align}
$$

2. The STE for $\text{clip}$:

For the clipping function, the gradient passes through identically if the value was within the representable bounds during the forward pass.
If the value was clipped to $\mathbf{Q}\_{\min}$ or $\mathbf{Q}\_{\max}$, the gradient is stopped (zeroed out).

Using the indicator function $\mathbb{I}$, the derivative is:

$$
\begin{align}
\frac{\partial}{\partial z}\text{clip}(z) \approx \mathbb{I}\left(\mathbf{Q}\_{\min}\leq v_y\leq \mathbf{Q}\_{\max}\right)
\end{align}
$$

Note that we evaluate the bounds check using $v_y$ which is the actual integer value of the output tuple $y$ from the forward pass.

Combining these, the gradient simply flows straight through the rounding operator but gets masked by the clipping bounds.

Let $\mathbf{0}\_{\nabla_y}$ be the zero-gradient tuple that matches the shift of the incoming gradient, meaning $\mathbf{0}\_{\nabla_y} = (0, s\_{\nabla_y})$.

The gradient $\nabla_z L$ is defined as

$$
\nabla_z L = \begin{cases}
\nabla_y L & \text{if } \mathbf{Q}\_{\min} \le v_y \le \mathbf{Q}\_{\max} \\\\
\mathbf{0}_{\nabla y} & \text{otherwise}
\end{cases}
$$


## Implementation
Now that we outlined the required theory to make integer native training work, we must align our implementation.
I will explain this in the [next post]({{ "integers" |  postsUrl }}).
