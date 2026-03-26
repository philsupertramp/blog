---
tags:
 - post
 - published
 - integers
title: "Integers: Training Neural Networks Without Floating Point"
layout: mylayout.njk
author: Philipp
description: 
date: 2026-03-11
---
<style>
table {border-collapse: collapse;, width: 50%} tr,table,th,td { border: 1px solid; }
</style>

_Part 1 of a series on native integer machine learning_


When you train a neural network today, you're almost certainly doing it in float32,
or if you're lucky enough to have the hardware, bfloat16. The floating point unit 
is so deeply assumed in modern ML that most frameworks don't even expose a seam where you could swap it out.
But floating point is not free, and it's not universal.
This series is about what happens when you take that assumption away entirely.

## The Problem with Float

The case for integer arithmetic in neural networks is usually framed around inference:
quantize your trained float model down to integers, ship it to a phone, profit.
This is well-understood, well-supported and wildely implemented. HuggingFace provides a great overview of these quantization methods
in their [transformer documentation](https://huggingface.co/docs/transformers/quantization/overview).

What's less explored is whether you can skip the float phase entirely, i.e. training, backpropagation, and weight updates all in integer arithmetic,
on hardware that might not have a floating point unit (FPU) at all.

The motivation isn't exotic. A large and growing class of compute targets, i.e. microcontrollers, FPGAs, custom ASICs, and edge accelerators,
either lack FPUs entirely or pay a significant power and area penalty to use them.
The standard answer is "train in float, quantize to int for deployment,"
but this creates a fundamental mismatch: you optimize a float model, then approximate it as integers and hope the gap is small.
You also need float hardware to train in the first place, which rules out the scenario where the 
training itself needs to happen on the edge, e.g. on-device fine tuning.

Beyond hardware constraints, there's a more fundamental question:
_is floating point load-bearing for learning, or is it just what we've always used because the math looks nicer?_
The smooth gradients, the dynamic range, the precise intermediate values — how much of that actually matters for convergence?

That's the question I started trying to answer about a month ago.


## What "Native Integer" Means
"Native Integer" in this context means something specific. <u>It doesn't mean</u>:
- Training in float, then quantization to integer afterward
- Using floats for gradients and integers for activations
- Simulating integer arithmetic in float space

It means the core tensor operations, forward pass, backward pass and weight updates are comptued directly in integer
types, with no floating point involved in the hot path.

The main technical challenge this creates is scale management.
Floating point values handle scale implicitly through their exponent field. Integers don't do that.
When you multiply two i32 values together, the product has roughly double the bit-width of meaningful signal, and 
you need to decide how to downcast it back to a representable range without losing too much information.
If this is done natively, the activations either explode to saturation or collapse to zero within a few layers.

A numerical example motivates this better. Say you have a two-layer network where weights and inputs are stored 
as i32 values in range $[-127, 127]$ (roughly one signed byte of useful signal).

Layer 1 has 128 inputs. A single dot product accumulates 128 multiplications, each up to $127 \cdot 127 = 16129$,
giving a maximum accumulator value around $128 \cdot (127 \cdot 127) = 2064512 \approx 2.1 \cdot 10^6$.

This still fits in a i32 (max. $\approx 2.1 \cdot 10^9$), so layer 1 is fine.

Now pass that accumulator without scaling into layer 2 as the input.
Layer 2 also has 128 input, and now each element of the input vector is up to $\approx 2.1 \cdot 10^6$, rather than $127$.
A single dot product accumulates to $128 \cdot (2.1\cdot 10^6) \cdot 127 \approx 32 \cdot 10^9$. That overflows i32.
Every output neuron in layer 2 saturates to the maximum value, and all gradient signal through that layer is dead.


The opposite failure is just as easy to each. If you right-shift the layer  1 output aggressively to bring it back into $[-127, 127]$ range,
you're dividing by a power of two. Shift by too many bits and the rounded-down values are mostly zero. You've discarded the signal before
layer 2 ever sees it.

With three or four layers and naively chosen shifts, the activations reliably collapse to an all-zero tensor within the first few forward passes.

The solution that we will use for now is _shift-based fixed-point arithmetic_:
Every tensor carries an associated `shift` value that represents its effective scale as a power of two.
Multiplying two tensors at shifts `s_a` and `s_b` produces an accumulator at shift `s_a + s_b`, and downcasting
applies _stochastic rounding_ to avoid the systematic bias that straight truncation introduces.

## The Project: [`integers`](https://github.com/philsupertramp/integers)
For compatibility reasons, and because I really want to get better in Rust, I decided to build the codebase in Rust.
The library is completely built from scratch, with no ML framework dependencies.

The code base abstractions are:

### `Scalar` and `Numeric` traits
Rathert than hardcoding a type, every module is generic over a `Scalar`, currently `i32` and `f32`.
This means the same `Linear` layer, the same `ReLU`, the same optimizer can run in either mode.
These traits implement mathematical operators for the underlying data types, e.g. `matmul`.

The `f32` path serves as a correctness baseline. If integer training diverges wildly from float training on the same architecture and seed, that's an indicator
something is wrong in the shift logic.

`Scalar`s implement types for inference, `Numeric` for accumulators.

### `Tensor<T>`
A simple row-major flat array with a shape vector. No striding, no accelerator backend.
The shift value is not stored in the tensor itself, it's tracked as a `u32` value that threads
through the computation graph alongside the tensor.

This is deliberate: keeping shifts out of the tensor type means fewer abstraction layers
and easier reasoning about where scale changes happen.

### `Params<S>`
The weight store, which maintains both a `master` copy (full `S::Acc` precision for accumulating gradient updates)
and a `storage` copy (quantized `S` for use in forward/backward).
The `quant_shift` on a parameter set controls how aggressively the master weights are compressed when synced to storage.
`Params` are used in objects that implement the `Module` trait.

### `Module<S>` trait
The standard forward/backward interface, both methods carry shift values, `s_x` the input shift and `s_g` the output shift.
```rust
fn forward(&mut self, input: &Tensor<S>, s_x: u32, rng: &mut XorShift64) -> (Tensor<S>, u32);
fn backward(&mut self, grad: &Tensor<S::Acc>, s_g: u32) -> (Tensor<S::Acc>, u32);
```
Apart from the incoming shift values each methods returns the shift value of the resulting output tensor.

### Sequential<S>
A container that chains modules and threads shifts through the full forward and backward passes automatically.

### Optimizers
The optimizers (SGD with optional momentum, Adam) are also integer-native,
with learning rates expressed as bit shifts: `lr_shift = 4` means a learning rate of `1/16`.
This sounds limiting, but it aligns with how you would implement a fixed-point optimizer on hardware anyway.

**Note**: The `f32` implementation of both optimizers use "raw" arithmetic, only the `i32` version uses our internal
`Scalar` and `Numeric` operations.

### Random number generator
Random numbers are generated using a shift-register generator ([Xorshift](https://en.wikipedia.org/wiki/Xorshift)), specifically the 64 bit version.
```rust
#[derive(Debug, PartialEq)]
pub struct XorShift64 {
    pub state: u64,
}

impl XorShift64 {
    pub fn new(seed: u64) -> Self {
        // edge case handleing for state = 0
        let state = if seed == 0 { 0xC0FFEE } else { seed };
        Self { state }
    }

    pub fn next(&mut self) -> u64 {
        let mut x = self.state;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.state = x;
        x
    }

    /// Random value generator for value in range [0, range)
    #[inline(always)]
    pub fn gen_range(&mut self, range: u32) -> u32 {
        (self.next() as u32) % range
    }
}
```


### Stochastic rounding
The downcast path uses the `XorShift64` random number generator to round fractional remainders
probabilistically rather than always truncating. Over many samples, this gives unbiased estimates
where truncation would introduce a systematic downward drift.

```rust
pub fn stochastic_downcast(val: i32, shift: u32, rng: &mut XorShift64) -> i32 {
    if shift == 0 { return val; }

    let mask = (1 << shift) - 1;
    let frac = val & mask;

    let thresh = rng.gen_range(1 << shift) as i32;
    let round_bit = if frac.abs() > thresh { 1 } else { 0 };

    let shifted = (val >> shift) + round_bit;

    shifted
}
```

Again a quick numerical example.
Let's say we want to downscale a 5 dimensional vector with elements $i=0,...,4$ and $x_i = 5$ with a shift value of $1$.
In the naive approach we do $x_i = 5 \>\> 1 = 2$ on every element, losing the information about the lost $0.5$ for every element.
With stochastic downcasting some elements are scaled to $2$ some to $3$, retaining the lost information from the naive shift.


---

## Current State: A Baseline

At this point the project is a working baseline, not a polished library.
The immediate goals were to prove out the architecture and establish that integer training can learn something on real tasks.

Both experiments use the same architecture and batch size accross float and integer runs.
The f32 path serves as the baseline; the i32 path uses the same `Sequential` container and module implementations,
with the `Scalar` type swapped out.

### Iris
The [Iris dataset](https://archive.ics.uci.edu/dataset/53/iris) has 150 samples, 4 continuous features, and 3 classes. Features are [z-score
quantized](https://en.wikipedia.org/wiki/Standard_score) before loading.

Architecture: `4 -> 8 -> 8 -> 3` with ReLU activations and MSE loss.

| | f32 | i32 |
|:-|-----:|-----:|
|Test accuracy | 90% | 90% |
| Epochs | 500 | 5000 |
| `lr_shift` | 7 | 3 |
| `momentum_shift` | 1 | 0 |
| Batch size | 32 | 32 |
| Grad. Clip value | - | 512 |

Both runs reach the same final accuracy. The integer model gets there, but needs 100x more epochs to do it.

The hyperparameters also diverge significantly:

f32 runs comfortably with samall learning rate (`lr_shift: 7` $\approx \frac{1}{128}$) and light momentum,
while i32 needs a much larger effective learning rate (`lr_shift: 3` $\approx \frac{1}{8}$) and stronger momentum to make progress.
This points to a noisier, coarser update signal in the integer path, each weight step is quantized to a power-of-two
granularity, so small gradient signals that would nudge a float weight by a tiny amount either round to zero or overshoot.

That i32 converges at all on Iris is encouraging.
That it needs this much more iteration to do so is the first concrete measurement of what integer training costs.

## MNIST
The [MNIST dataset](https://huggingface.co/datasets/ylecun/mnist) has 60000 training samples and 10000 test samples, with 784 pixel features per image.
Features are z-score quantized.

Architecture: `784 -> 128 -> 128 -> 10` with ReLU activations, MSE loss, and early stopping at 95% test accuracy.

| | f32 | i32 |
|:-|-----:|-----:|
| Test accuracy | 95.89% | ~20% |
| Epochs | 31 (early stopping) | - |
| Time per epoch | ~7.5s | increasing |
| `lr_shift` | 6 | 5 |
| `momentum_shift` | None | None |
| Batch size | 32 | 32 |

The f32 model converges cleanly, hitting the early stopping threshold at epoch 31.

The i32 model currently doesn't. Loss does decrease, the network is learning something, but test accuracy plateaus at 20%, barely above random for a 10-class problem.

There's also an unexpected symptom:

Per epoch compute time grows as training progresses, which shouldn't happen with a fixed architecture and batch size.
That points to a memory or bookkeeping issue in the integer path that needs investigation before the results can be trusted.

The honest picture after this round of experiments:

**Integer training works on small problems, and the scaling behavior on larger ones is an open question, for me.**
Getting MNIST i32 to match the f32 baseline is the central problem we will work on next.

---

## What's Next
This post is only a starting point. The subsequent posts in this series will cover:
- **i32 MNIST** What needs to be done to get to 95% accuracy for i32?
- **Shift management in depth**. The relationship between `input_shift`, `output_shift`,
    `quant_shift` and `grad_shift` deserves a full treatment. Getting this wrong is the most
    common failure mode, and the current codebase has some heuristics (auto-detecting shifts
    from weight magnitude after Xavier init) that need to be documented and justified properly.
- **Other layers**. The repo contains already an implementation of a `RNNCell` and will soon receive
    `Conv2d`. These will receive dedicated posts, too.
- **The hardware question**. What would it actually look like to run this inference (and eventually training)
    on a microcontroller of FPGA? What changes when you drop from `i32` to `i8`?


The code is open and the approach is straightforward. The point of writing
this up isn't to claim that integer training is solved, it clearly isn't,
but to document what a ground-up integer ML stack might look like, what problems it runs into, and whether
the core assumption holds: that you can train a useful neural network without ever touching a floating point number.

So far, for small problems, the answer looks like yes. [Part 2]({{ "integers-the-theory" |  postsUrl }}) will find out how far that scales.

The source code is available at [github](https://github.com/philsupertramp/integers).
