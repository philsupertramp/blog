---
tags:
 - old-wiki
 - published
title: Interpolation and approximation of functions
description: A description of numerical function approximation and interpolation. Including implementations
layout: mylayout.njk
author: Philipp
date: 2021-05-13
---

In the field of numeric mathematics several methods exist to approximate and/or interpolate a function based on 
support values.  
Together the <span>\\(n+1\\)</span> *support* values 
<span>$$\hat{x_i} = \begin{pmatrix}x, y\end{pmatrix}, \quad \forall i = 0, ..., n$$</span>
describe the function to approximate.  
Those support values will be transformed into interpolation conditions according to the base we want the function to be displayed in.

In the following paragraph we will learn that there are different ways to describe a polynomial function, yet all resulting
polynomials are essentially the same underlying base polynomials just converted into different bases.

### Monom-Base
**Transformation**  
To display a polynomial function in the monom base one creates <span>\(n+1\)</span> equations, the interpolation conditions
<span>
$$
y_i = p(x_i) = a_0 + a_1x_i + ... + a_nx_i^n, \quad \forall i = 0, \dots, n
$$
These equations can be displayed as a linear system of equations
$$
Va=y
$$
with 
$$
y = (y_0, \dots, y_n)^T
$$
 and V* the *Vandermonde-Matrix*.  
This matrix holds a determinant
$$
\det(V) = \prod_{0\leq x_j<x_k\leq n} (x_j - x_k)
$$
which is always
$$
\det(V) \neq 0
$$
for pair-wise unique support values, hence the interpolation problem has always __one__ solution.

**Evaluation**
To evaluate a polynomials in the monom base one can use [Horner's method](https://en.wikipedia.org/wiki/Horner%27s_method)
$$
p(x) = a_0 + x(a_1 + x(a_2 + \dots + x(a_{n-1} + xa_n)))
$$

#### Python implementation
```python
import numpy as np

def polMonom(a, x):
    """ Evaluates y = a[0] + a[1]*x + ... + a[n]*x^p """
    y = np.ones(x.shape) * a[0]
    for j in range(1, len(a)):
        y += a[j]*(x**j)   # later: use Horner scheme
    return y
```
### Lagrange-Base
**Transformation**  
Another base is the Lagrange base.  
Given \\( n+1 \\) pair-wise unique support values \\( x_0, ..., x_n\\)
$$
L_i(x) = \prod_{j=0, j\neq i}^{n} \frac{x-x_j}{x_i-x_j}, \quad \forall i=0, \dots, n
$$
are called Lagrange-fundamental polynomials or Lagrange-Base-Polynomials.  
Not all of them need to be computed, tho.  

$$
\text{if } k=i \quad
L_i(x) = 1
$$
$$
\text{if } k\neq i \quad
L_i(x) = 0
$$
**Evaluation**  
$$
\Rightarrow p(x) = \sum_{i}^{n}y_iL_i(x) \in \Pi_n
$$
Which meets all of the interpolation requirements
$$
p(x_k) = \sum_{i}^{n}y_iL_i(x_k) = y_k, \forall k = 0, ..., n
$$

#### Python implementation
```python
import numpy as np


def L(xk: float, x: np.array, i: int) -> float:
    out: float = 1.0
    for j in range(x.shape[0]):
        if i == j: continue

        out *= (xk - x[j])/(x[i]-x[j])
    return out

def lagrange(xk: np.array, x: np.array, y: np.array) -> np.array:
    out: np.array = np.zeros(xk.shape)
    for k in range(xk.shape[0]):
        for i in range(y.shape[0]):
            if i == k:
                out[k] += y[i]
            else:
                out[k] += y[i] * L(xk[k], x, i)
    return out
```

### Newton-Base
**Transformation**  
For \\(n+1\\) support values \\((x_0, \dots x_n)\\):

$$
     \omega_0(x) = 1
$$
$$
     \omega_i(x) = \prod_{j=0}^{i-1} (x - x_j), \quad i = 1, \dots n 
$$
Representation:
$$
    p(x) = \sum_{i=0}^{n} b_i \omega_i(x)
$$
$$
    b_i = \frac{f_{[x_{r+1}, ..., x_s]} - f_{[x_r, ..., x_{s-1}]}}{x_s - x_r}
$$
#### Python implementation
```python
import numpy as np

def koeffNewtonBasis(xk, yk):
    """ recursive schema of div. differences - iterativ implemented """
    m = len(xk)
    F = np.zeros((m,m))
    F[:,0] = yk   
    for j in range(1, m):     # j-te dividierte Diffenzen
        for i in range(j, m):
            F[i, j] = (F[i, j-1] - F[i-1, j-1])/(x[i] - x[i-j])
            #print(f'F[{i},{j}] = (F[{i},{j-1}] - F[{i-1},{j-1}])/(x[{i}]-x[{i-j}])')        # for debugging
    return np.diag(F)
```
**Evaluation**  
Using Horner's Method

#### Python implementation
```python
import numpy as np
def polNewtonHorner(b, xk, x):
    """ y = b[0] + b[1]*(x - xk[0]) + ... + b[n]*(x - x[0])* ... *(x - x[n-1]), using Horner's-Method """
    y = np.ones(x.shape) * b[-1]
    for j in range(len(b)-2, -1, -1):
        y =  b[j] + (x - xk[j])*y
    return y
```
