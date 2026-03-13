---
tags:
 - post
 - published
title: "Integers: Improving i32 to reach f32 on MNIST"
layout: mylayout.njk
author: Philipp
description: 
date: 2026-03-12
---

- added debugging statements to IRIS test, checking runtime, overflow stats and outgoing shift of predictions
    - result: no wrapping, compute time between 2700 - 3000µs (micro seconds)
    - shifts:
        - layers:
            - l1: 3 -> 4
            - l2: 4 -> 4
            - l3: 4 -> 2
        - input:        5
        - forward out: 16  = 5 + (3 + 0) + 0 + (4 + 0) + 0 + (4 + 0) = 5 + 3 + 4 + 4 = 16
        - backward out:16  = 


A fresh set of eyes was one of the main drivers behind the solution.

But first things first.
An updated table for Iris is required

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

Reason for this success were two things
1. fixing the internal shift bookkeeping.
    1.1 `Linear<S>`'s backward pass was using `Linear::output_shift` to transform the gradient w.r.t inputs. This resulted in wrong shifts for subsequent layers
    1.2 `Linear<S>`'s backward pass did not return a reduced `s_g` (gradient shift), but rather just forwarded the incoming value
2. Drastically increase gradient clip value to allow more information bytes flowing through the network.


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


## Impact on MNIST
The change was clearly fixing a bug, otherwise our performance on Iris would not look like this.
Running quickly some epochs shows that at least the increasing compute time issue that we had in the [previous post]() is
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


## The core math
Let $V = \mathbb{Z}$ be the set of integers, and $S$ be the set of all possible shift values (e.g. $S = \mathbb{Z}$ or $S = \mathbb{N}$).

We define the universal set of scaled tuples $\dot{X}$ as the Cartesian product of $V$ and $S$:
$$
\dot{X} = V \times S = \\{(v,s) \| v\in V, s \in S \\}
$$

To avoid confusion with standard scalar arithmetic, we define the binary operation of addition $\oplus: \dot{X} \times \dot{X} \rightarrow \dot{X}$.
For any two elements $a = (v_a, s_a)\in \dot{X}$ and $b = (v_b, s_b) \in \dot{X}$, the addition is given by
$$
a \oplus b = (v_a + v_b, \max(s_a, s_b))
$$

Subtraction:
$$
a \ominus b = (v_a - v_b, \max(s_a, s_b))
$$

Similar, we define the binary operation of multiplication $\otimes: \dot{X} \times \dot{X} \rightarrow \dot{X}$.
For any two elements $a = (v_a, s_a)$ and $b = (v_b, s_b)$, the multiplication is given by
$$
a \otimes b = (v_a \cdot v_b, s_a + s_b)
$$

and division: For $v_b \neq 0$
$$
a \oslash b = \left(\left\lfloor\frac{v_a}{v_b}\right\rfloor, s_a - s_b\right)
$$

This is the current implementation and it is incorrect, at least the addition and subtraction.

A quick analogy to motivate this, imagine you have two tensors in a physical system measuring weights.
We aggree to denote milligrams with shift 0, grams with shift 2 and kilo grams with 6.

If we follow our definition $x_1 = 2 kg = (2, 0)$ and $x_2 = 6mg = (6, 6)$ and $x_1 \oplus x_2 = (8, 6)$, suddenly
we have 8 mg, instead of 2000006 mg. The same thing will happen with subtraction $(2, 0) \ominus (6, 6) = (-4, 6)$, which represents negative 4 mg. That's completely incorrect.

Instead, we should downscale (increase shift) the bigger value and then apply the operation.

### Aligning shift in addition and subtraction
When calculating $c = a \oplus b$, if we enforce $s_c = \max(s_a, s_b)$, the value with smaller shift must be down-scaled (right-shifted) to match the larger shift before the addition takes place.
Otherwise, the estimator will treat numbers of different magnitudes as if they were on the same scale, like we see above.

Using a base-2 system (where a shift $s$ represents a scaling by $2^s$), a difference in shifts means we multiply or divide by $2^{\Delta s}$.
For integer-native hardware, division by $2^{\Delta s}$ is implemented as arithmetic right shift (`>>`).

With this in mind, here's the updated formalization of the operations:

Let $\dot{X} = \mathbb{Z}\times \mathbb{Z}$ be the space of tuples $(v, s)$.

For any $a = (v_a, s_a), b = (v_b, s_b) \in \dot{X}$, we define the target shift for addition and substraction as $s_c = \max(s_a, s_b)$.
To align the values, we define the aligned values $\tilde{v}_a$ and $\tilde{v}_b$:
$$
\tilde{v}_a = \lfloor v_a \cdot 2^{s_a - s_c}\rfloor\\\\
\tilde{v}_b = \lfloor v_b \cdot 2^{s_b - s_c}\rfloor
$$
