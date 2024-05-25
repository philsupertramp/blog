---
tags:
 - old-wiki
 - published
title: Orthogonal Linear Regression
description: Orthogonal Linear Regression implemented in Python
layout: mylayout.njk
author: Philipp
date: 2021-10-20
---
>In statistics, linear regression is a linear approach for modelling the relationship between a scalar response and one or more explanatory variables (also known as dependent and independent variables). The case of one explanatory variable is called simple linear regression; for more than one, the process is called multiple linear regression. This term is distinct from multivariate linear regression, where multiple correlated dependent variables are predicted, rather than a single scalar variable. [^1](https://wikipedia.org/wiki/Linear_regression)

Essentially generate a model which approximates a set of given points \\(a = \\{(x_i, y_i) \\in R | i = 1, ..., k \\}\\) we calculate
$$
Y_i = \\beta_0 + \\beta_1 x_i + \\epsilon_i
$$

if we assume \\(\\epsilon_i = 0\\) we get the formula for orthogonal regression
$$
Y_i = \\beta_0 + \\beta_1 x_i
$$
which can be calculated using the following Python implementation
```python
import numpy as np
from matplotlib import pyplot as plt


def calc_line(a: np.array) -> np.array:
    """
    Calculate 2D orthogonal regression line
    A_i(i|y_i) for all i = 1, ..., k

    :param a: Array of y-values
    :returns: x-values of orthogonal regression line for the k given y-values
    """
    size = a.size
    u1 = np.linspace(1, size, size)
    u2 = np.ones([size, ])
    right = np.array([a.T.dot(u1), a.T.dot(u2)])
    left = np.array([[u1.T.dot(u1), u1.T.dot(u2)], [u1.T.dot(u2), u2.T.dot(u2)]])
    beta_1, beta_0 = np.linalg.solve(left, right)
    return beta_0 + u1 * beta_1
```

![Figure_1](https://user-images.githubusercontent.com/43775635/118839646-f3e77600-b8c6-11eb-87e4-e0d88a1745d5.png)


[^1]: [wikipedia](https://en.wikipedia.org/wiki/Linear_regression)
