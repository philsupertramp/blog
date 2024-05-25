---
tags:
 - old-wiki
 - published
title: Principle Component Analysis using singular value decomposition
description: A brief description how to use SVD to create a PCA
layout: mylayout.njk
author: Philipp
date: 2022-09-25
---

# Principle Component Analysis
## What is PCA and why should I use it?
> > Pincipal component analysis (PCA) is the process of computing the principal components and using them to perform a change of basis on the data, sometimes using only the first few principal components and ignoring the rest.
>The principal components of a collection of points in a real coordinate space are a sequence of \\(p\\) unit vectors, where the \\(i\\)-th vector is the direction of a line that best fits the data while being orthogonal to the first \\(i\\)-1 vectors. Here, a best-fitting line is defined as one that minimizes the average squared distance from the points to the line. These directions constitute an orthonormal basis in which different individual dimensions of the data are linearly uncorrelated.

## So what? 
Right? Just build a correlation matrix and drop those with too small values.
Well.. yes and no. Building the correlation matrix is just one part of your analysis,
but you will also need to look through each feature individually and make an educated
guess which one to drop and which to keep. Well, not with PCA. It'll do the ordering for you
and even tells you how much a dataset is going into the trend of a priciple component of your dataset.

# Theorie
To analyse the priciple components of a given set of data
$$
\bar{X}
$$
the initial data first needs to be transformed.
So we calculate the mean value of each row of records
$$
\bar{x} = \frac{1}{n} \sum x(i)
$$
then multiply the resulting \\(1 \times n\\) vector with a vector of ones with the size \\(n\\)
$$
\tilde{X} =\left[1 \right] \cdot \bar{x}
$$
Subtract the result from the input dataset
$$
B = \bar{X} - \tilde{X}
$$
and finally normalize the data
$$
B = \frac{1}{\sqrt{n}} B
$$
This gives us the input matrix for the singular value decomposition, short SVD which can (in most languages) simply be imported via a library.
The SVD gives us
$$
 B = U \cdot \Sigma \cdot V^T
$$
which we can now use to perform our priciple component analysis.

The priciple components are 
$$
T = U \cdot \Sigma
$$
and \\(V\\) contains the so called "loading" of each record's load towards the corresponding component in the dataset.

So let's say \\(V(0, 4) = 0.5\\). This stands for the first dataset having a load of \\(0.5\\) for the 5th principle component.

Therefor according to the load of components we can decide to keep, or discard them. 

# Example
All of the things above seem simple enough to give them a try, right?

For simplification we imagine a gaussian normal distributed set of data.
It may look like this:

![image](https://user-images.githubusercontent.com/9550040/135756049-d380b5c1-c7ea-46f6-9b36-99425aa98aa6.png)

To make it a bit harder we perform regular transformations to the dataset,
rotate and stretch it, into

![image](https://user-images.githubusercontent.com/9550040/135756037-93eeaf91-ec6a-4687-928a-7d40acc1ad28.png)

Where left is the original data and on the right side the transformed dataset.

Then after performing above described PCA we achive the result

![image](https://user-images.githubusercontent.com/9550040/135756032-6e726f5f-e209-4d55-9a67-2c9ff11f231c.png)

For an implementation of the example in C++ see [github.com/philsupertramp/game-math](https://github.com/philsupertramp/game-math/blob/release/tests/numerics/lin_alg/TestSVD.cpp#L27)
