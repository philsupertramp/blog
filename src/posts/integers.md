---
tags:
 - post
 - published
 - integers
title: "Integers: An integer native ML engine"
layout: mylayout.njk
author: Philipp
description: In this post I explain how I aligned the framework with our theoretic definition.
published: 2026-03-03
---
<style>
table {border-collapse: collapse;, width: 50%} tr,table,th,td { border: 1px solid; }
</style>

_This is part 3 of my **integers** series_.

Today we'll summarize the framework to get a better understanding why all of the things actually work out that we
discussed in the [previous post]({{"integers-the-theory" |  postsUrl}}).

{% caution "The library went through a major refactoring, almost all parts received changes." %}

## RNG
Using the `random` library to generate uniform distributed values is quite a pain, especially because the internal algorithm is
[ChaCha8](https://en.wikipedia.org/wiki/Salsa20#ChaCha_variant) which requires 20+ OPs,
whereas [XOR-Shift (64bit)](https://en.wikipedia.org/wiki/Xorshift) requires only 3 bit OPs.

To make the `XorShift64` object even more accessible, we're using `cell::Cell` to create a global singleton instance from which
we can sample values using the public `rng_next`
helper method.

And to empower the user we provide a simple `seed_rng` method that allows setting the global seed.
So instead of initializing our `XORShift64` object whenever we need it, we can just call `rng::seed_rng` intially
and then sample values using `rng::rng_next` or `rng::rng_range`.

```rust
use integers::rng::{seed_rng, rng_next};

fn main() {
    seed_rng(420);

    for i in 0..10 {
        println("{}", rng_next());
    }
}
```

## Dyadic
The `Dyadic` struct is basically the `f32` replacement in our implementation, the core of the integer engine.

To implement these scaled value tuples, $(v, s) \in \mathcal{D}$, introduced in the [previous post]({{"integers-improving-mnist" |  postsUrl}}), we implemented `./src/lib/dyadic.rs`.

This module holds the `Dyadic` struct definition, all defined arithmetic operators $\oplus, \ominus, \otimes$ and $\oslash$ as well as the requantization method $\mathcal{R}(x, s_t)$ with $\text{clip}(v_x, \mathbf{Q}\_{\min}, \mathbf{Q}\_{\max})$ and $\text{SR}(v_x, s_t - s_x)$.

For now all operators are implemented in a functional programming approach.

Here's a small example how to use them

```rust
use integers::dyadic::{Dyadic, add, sub, mul, div, clip, requantize};

fn main() {
    let a = Dyadic { v: 10, s: 0 };
    let b = Dyadic { v: 5, s: 0 };

    assert_eq!(add(a, b).v, 15);
    assert_eq!(add(a, b).s, 0);
    assert_eq!(sub(a, b).v, 5);
    assert_eq!(sub(a, b).s, 0);

    assert_eq!(mul(a, b).v, 50);
    assert_eq!(mul(a, b).s, 0);
    assert_eq!(div(a, b).v, 2);
    assert_eq!(div(a, b).s, 0);

    assert_eq!(clip(130, -128, 127), 127);

    let (val, was_clipped) = requantize(a, 0, -128, 127);
    assert_eq!(val.s, 0);
    assert_eq!(val.v, 10);

    assert_ne!(was_clipped, true);

    let (val, was_clipped) = requantize(a, 0, -8, 7);
    assert_eq!(val.s, 0);
    assert_eq!(val.v, 7);

    assert!(was_clipped);
    
}
```
All operators use rust's `saturating_*` traits for the built-in numeric types to ensure we don't overflow values during training and inference.

As described in the previous post, multiplication (`mul`) expands the value $v$ from `i32` to `i64`, then uses
`stochastic_round_i64` for downcasting the value back into `i32`.
This is done to ensure gradients don't immediately explode once a value comes close to `i32::MAX` or vanish approaching `i32::MIN`.

{% note "We might move towards native operators again, once we have a fully stable solution, but for now we'll stick to the functional implementation." %}


## Scalar and Numeric
The `Numeric` trait was used to describe accumulator types and `Scalar` was describing "true" types.
This created a lot of confusion when using both in calculations.

We're currently dropping `f32` support, in favor of a more easy to understand overall architecture.

This allows us to completely replace `Numeric` **and** `Scalar` with `Dyadic`.

`Tensor` is still part of the stack and didn't change much, it's still a row-major $n$ dimensional array.
The major change here is that we removed the operator implementations and it only acts as a container of `Dyadic` elements, with a "shape".

## Quantization
We implemented three quantization methods before for data pre-processing, namely `none_quantize`, `minmax_quantize` and `standard_score_quantize`. All these three methods remained the same way as prior to the refactoring.

- `none_quantize`: Noop operator, passes the value straight through
- `minmax_quantize`: [Min-max](https://en.wikipedia.org/wiki/Feature_scaling#Rescaling_(min-max_normalization)) normalization
- `standard_score_quantize`: [Standard score](https://en.wikipedia.org/wiki/Standard_score) or z-score quantization

Each of these methods accept arrays of `f32` values and return a tuple of `i32` quantised values and a shift value.
where the shift is the scale exponent $s$ such that the decoded value is $v \cdot 2^{-s}$.

{% note "All quantization strategies that map values to the range \\([-127, 127]\\) must return <code>shift = 7</code>, since $127 \\cdot 2^{-7} \\approx 0.992 \\approx 1.0$." %}

## Data loading
To fix the library we didn't need to update much of the data module. We still support TSV/CSV and Parquet files.
Dedicated implementations for data loaders were moved into the `./examples` directory, right next to the example that need it.

The chore library doesn't need to be aware of MNIST or the CIFAR datasets. All it needs to provide is an API to use these datasets for interacting with the library.

Datasets now yield `Dyadic` samples and labels that are already represented with the datasets desired `shift` value.

## NN
The majority of changes happen inside the `nn` module, which got replaced more or less from the ground up.

We still maintain a `Module` trait that must be implemented from all module types like `Linear` or `ReLU`.
And we can still stack layers of `Module` instances together using the `Sequential` struct that holds a `Vec<Module>`.

`Params` got deprecated completely, so layers must now track their own gradients.
Also the `optim` module containing the optimizers got deprecated and we currently have two methods `nn::sgd_step` and `nn::momentum_step` that implement
SGD and SGD with momentum respectively.
You can use `nn::apply_updates` with `momentum` or without it.

To get a base level implementation we started with only `Linear` and `ReLU`.

### Linear
Generally speaking, a linear (feed forward) layer performs an affine transformation.

Let $n\_{\text{in}}$ and $n\_{\text{out}}$ be the input and output dimensions
and let $W \in \mathbb{R}^{n\_{\text{in}}\times n\_{\text{out}}}$ be a matrix of weights and $b \in \mathcal{R}^{n\_{\text{out}}}$ a vector of bias values.
Then for $x \in \mathbb{R}^{n\_{\text{in}}}$ the regular forward pass for a linear layer is given by
$$
f(x) = Wx + b
$$

This can be translated to our dyadic arithmetic as follows.
The layer is parameterized by the weight matrix $W \in \mathcal{D}^{n\_{\text{out}} \times n\_{\text{in}}}$, $b\in\mathcal{D}^{n\_{\text{out}}}$ the bias vector
and the quantization parameters $s_q$ the precision and $B$ the output bit-width, which is used to compute $\mathbf{Q}\_{\min}$ and $\mathbf{Q}\_{\max}$ with
$$
\mathbf{Q}\_{\min} = -2^{B-1}, \mathbf{Q}\_{\max} = 2^{B - 1} - 1
$$

The forward pass implements a quantized dot product.
For an input vector $x \in \mathcal{D}^{n\_{\text{in}}}$, the $j$-th output element is computed as
$$
\hat{y}_i = \mathcal{R}\left(b\_j \oplus \bigoplus\_{i=1}^{n\_{\text{in}}}\left(w\_{ji}\otimes x\_i\right)\_{s\_{q}}\right)
$$
with $\mathcal{R}$ the requantization function that clamps the results into the bounded domain $\mathcal{Q}$.
The subscript $s\_{q}$ indicates that products are immediately rescaled by $2^{-s\_{q}}$ to prevent bit-overflow during accumulation.

Because the requantization function $\mathcal{R}$ is a step function (non-differentiable), the backward pass employs a STE.

The gradient $g_j$ is clipped by a threshold $\tau$ to maintain training stability in fixed-point arithmetic
$$
g_j = \text{clamp}(\nabla y_i, -\tau, \tau)
$$

For weights initialization we're using Xavier initialization.
Given a weight scale $s\_w$, we compute a bound $k$ to preserve variance accross the layer using 
$$
k = \max\left(1, \left\lfloor \frac{2^{s\_{n}}}{\sqrt{n\_{\text{in}}}} + 0.5 \right\rfloor \right)
$$
Each weight $w_{ij}$ is sampled uniformly from the discrete interval $[-k, k]$ with a fractional scale of $2^{s\_w}$.
This ensures that the magnitutde of activations remains stable despite the integer constraints.

The constructor of `Linear` accepts `output_bits` ($B$), the output domain that is used to compute $\mathbf{Q}\_{\min}$ and $\mathbf{Q}\_{\max}$,
`quant_shift` ($s\_q$) the $s_q$ used for quantization during the multiplication and
`weight_shift` ($s\_w$) the fixed-point exponent for the weights, determining the "resolution" of the initialized linear kernels.

This allowed us to run the first experiments again, `xor` and `iris`.
After adjustments that meet the new API we can see something like this, solving the [XOR problem](https://github.com/philsupertramp/integers/blob/e73977352f62bb4b8be7395d46c9b5ec49dc31cc/examples/xor.rs)
with SGD without momentum using a network of two layers `[2, 8] -> ReLU -> [8, 1]`
```text
Sequential(
  (0): Linear(in=2, out=8, w_shift=7, q=7, bits=31, clip=2^13, mom=off)
  (1): ReLU
  (2): Linear(in=8, out=1, w_shift=7, q=7, bits=31, clip=2^13, mom=off)
)
epoch   0  mse = 1.2390
epoch  50  mse = 0.0152
epoch 100  mse = 0.0000
epoch 150  mse = 0.0000
epoch 200  mse = 0.0000
epoch 250  mse = 0.0000
epoch 299  mse = 0.0000

Final predictions:
  [ 1.00,  1.00] → -1.000  (target -1.00)
  [ 1.00, -1.00] →  1.000  (target  1.00)
  [-1.00,  1.00] →  1.008  (target  1.00)
  [-1.00, -1.00] → -1.000  (target -1.00)
```
With high confidence I would state that this one is solved.

Testing on the [iris dataset](https://github.com/philsupertramp/integers/blob/e73977352f62bb4b8be7395d46c9b5ec49dc31cc/examples/iris.rs) with a slightly bigger network `[4, 8] -> ReLU -> [8, 8] -> ReLU -> [8, 3]` and using SGD with momentum
```text
Loading Iris train dataset from 'data/iris_train.tsv' …
Loading Iris test dataset from 'data/iris_test.tsv' …
  130 samples,  4 features,  3 classes  (input_shift=7)

Sequential(
  (0): Linear(in=4, out=8, w_shift=7, q=7, bits=31, clip=2^13, mom=shift=1)
  (1): ReLU
  (2): Linear(in=8, out=8, w_shift=7, q=7, bits=31, clip=2^13, mom=shift=1)
  (3): ReLU
  (4): Linear(in=8, out=3, w_shift=7, q=7, bits=31, clip=2^13, mom=shift=1)
)

  Epoch      Train Loss   Train Acc      Test Acc
──────────────────────────────────────────────────
      0        0.692266      43.85%        65.00%
     50        0.061413      97.69%       100.00%
    100        0.054837      97.69%       100.00%
    150        0.047041      96.92%       100.00%
    200        0.044273      97.69%       100.00%
    250        0.040003      97.69%       100.00%
    300        0.039991      97.69%       100.00%
    350        0.039659      96.92%       100.00%
    400        0.038539      96.92%       100.00%
    450        0.040134      96.92%        95.00%
    499        0.035578      97.69%        95.00%

──────────────────────────────────────────────────
Best train accuracy : 99.23%
Best test  accuracy : 100.00%

Final pass accuracy: 126/130 = 96.9%

Per-class accuracy:
  class 0: 46/46 = 100.0%
  class 1: 40/43 = 93.0%
  class 2: 41/41 = 100.0%
```

This is an outstanding improvement compared to the results from the beginning.

It took 5k iterations before to reach an accuracy of $90\\%$, now we hit the $100\\%$ on the test data
right after 50 epochs!

There was one more open problem from the original implementation, the increasing compute time.
To verify that I extended the `iris.rs` example with a timer per epoch
```text
Loading Iris train dataset from 'data/iris_train.tsv' …
Loading Iris test dataset from 'data/iris_test.tsv' …
  130 samples,  4 features,  3 classes  (input_shift=7)

Sequential(
  (0): Linear(in=4, out=8, w_shift=7, q=7, bits=31, clip=2^13, mom=shift=1)
  (1): ReLU
  (2): Linear(in=8, out=8, w_shift=7, q=7, bits=31, clip=2^13, mom=shift=1)
  (3): ReLU
  (4): Linear(in=8, out=3, w_shift=7, q=7, bits=31, clip=2^13, mom=shift=1)
)

  Epoch      Train Loss   Train Acc      Test Acc
──────────────────────────────────────────────────
      0        0.674407      56.92%        80.00%
  └─ Epoch 0 duration: 0.0006s
     50        0.060718      96.92%        95.00%
  └─ Epoch 50 duration: 0.0005s
    100        0.049270      97.69%       100.00%
  └─ Epoch 100 duration: 0.0005s
    150        0.039540      97.69%       100.00%
  └─ Epoch 150 duration: 0.0005s
    200        0.039154      97.69%       100.00%
  └─ Epoch 200 duration: 0.0005s
    250        0.036128      97.69%       100.00%
  └─ Epoch 250 duration: 0.0005s
    300        0.037236      97.69%       100.00%
  └─ Epoch 300 duration: 0.0005s
    350        0.031032      98.46%       100.00%
  └─ Epoch 350 duration: 0.0005s
    400        0.029830      98.46%       100.00%
  └─ Epoch 400 duration: 0.0005s
    450        0.029145      99.23%       100.00%
  └─ Epoch 450 duration: 0.0005s
    499        0.029192      98.46%       100.00%
  └─ Epoch 499 duration: 0.0005s

──────────────────────────────────────────────────
Best train accuracy : 99.23%
Best test  accuracy : 100.00%

Total training time: 0.2573s
Final pass accuracy: 127/130 = 97.7%

Per-class accuracy:
  class 0: 46/46 = 100.0%
  class 1: 41/43 = 95.3%
  class 2: 40/41 = 97.6%
```
Unfortunately, we're too fast to see any real difference. Verifying over spans of 50 epochs we can see a rather constant duration of $0.0005$s.
If we check that with the total value $0.2573 = 500 \cdot x \Rightarrow x = 0.0005146$.
It's correct, but we should move onto a bigger scale.

Of course I immediately moved to MNIST in the hope of seeing fast results
```text
Loading MNIST from 'data/mnist' …
  Format: IDX binary
  [IDX] loaded 60000 samples in 309ms
  [IDX] loaded 10000 samples in 53ms
  train pool: 60000 samples
  test  pool: 10000 samples

Sequential(
  (0): Linear(in=784, out=128, w_shift=7, q=7, bits=31, clip=2^13, mom=shift=1)
  (1): ReLU
  (2): Linear(in=128, out=128, w_shift=7, q=7, bits=31, clip=2^13, mom=shift=1)
  (3): ReLU
  (4): Linear(in=128, out=10, w_shift=7, q=7, bits=31, clip=2^13, mom=shift=1)
)

  max_epochs=500,  n_train=60000,  batch=32
  n_eval=10000,  stop_patience=5 consecutive 100%
  lr=2^(-7),  momentum_shift=1,  grad_clip=2^13

 Epoch   Train Acc    Eval Acc   Streak (100%)        Time
────────────────────────────────────────────────────────────
     0       10.2%       10.3%               —     120.08s  
     1       10.3%        9.8%               —     119.74s  
     2       10.2%        9.7%               —     119.29s  
     3       10.3%       11.3%               —     119.85s  
     4       10.1%       11.3%               —     119.13s  
     5       10.1%        8.9%               —     118.97s  
     6       10.1%        9.7%               —     119.24s  
     7       10.2%       10.1%               —     118.36s  
^C
```
I interrupted here. 120s per epoch was something I didn't want to watch training until it converges.

My first idea for optimization was to run the "Stochastic" Gradient Descent I knew from uni.
Instead of training on all batches or all samples individually, we train on a subset of the randomized dataset.
Let's say we train on 128 samples, then we 
1. shuffle dataset
2. sample 128 samples from it
3. train on the samples
4. repeat until satisfied

But I also know that the classic FF neural network is really really bad with image data.
We might be able to get fine performance on MNIST, but once we move to real image data, e.g. CIFAR-10,
we will have bigger issues.

Another approach is required, namely we need a few things.
In the next post we will look at **Regularization** and **Convolutions**.

Those two building blocks will help us reach amazing performance on MNIST, and actually get something done on CIFAR-10.

Here's a small teaser for the next post
```text
Loading MNIST from 'data/mnist' …
  Format: IDX binary
  [IDX] loaded 60000 samples in 310ms
  [IDX] loaded 10000 samples in 52ms
  train pool: 60000 samples
  test  pool: 10000 samples

Sequential(
  (0): Conv2D(in=1, out=4, 3×3, 28×28→26×26, clip=2^13, mom=shift=1)
  (1): ReLU
  (2): MaxPool2D(C=4, 26×26→13×13, k=2, s=2)
  (3): Conv2D(in=4, out=8, 3×3, 13×13→11×11, clip=2^13, mom=shift=1)
  (4): ReLU
  (5): MaxPool2D(C=8, 11×11→5×5, k=2, s=2)
  (6): Flatten
  (7): Linear(in=200, out=64, w_shift=7, q=7, bits=32, clip=2^13, mom=shift=1)
  (8): ReLU
  (9): Linear(in=64, out=10, w_shift=7, q=7, bits=32, clip=2^13, mom=shift=1)
  (10): Softmax(shift=7)
)

  max_epochs=500,  n_train=256,  batch=32
  n_eval=20,  stop_patience=5 consecutive 100%
  lr=2^(-7),  momentum_shift=1,  grad_clip=2^13

 Epoch   Train Acc    Eval Acc   Streak (100%)        Time
────────────────────────────────────────────────────────────────
     0       13.3%       25.0%               —           0.37s
     1       17.6%       20.0%               —           0.36s
     2       30.5%       35.0%               —           0.36s
     3       39.5%       35.0%               —           0.36s
     4       62.5%       70.0%               —           0.36s
     5       66.8%       65.0%               —           0.36s
     6       68.8%       65.0%               —           0.36s
     7       71.9%       90.0%               —           0.36s
     8       74.6%       85.0%               —           0.36s
     9       79.7%       90.0%               —           0.37s
    10       84.8%       70.0%               —           0.37s
    11       80.5%       95.0%               —           0.36s
    12       85.5%      100.0%               1           0.36s
```
