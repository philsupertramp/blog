---
tags:
 - old-wiki
 - published
title: Symbolic Math in code
description: Symbolic Mathematics is a modern research topic. Here I will describe my learnings.
layout: mylayout.njk
author: Philipp
date: 2021-05-13
---

In computer science a widely researched topic is to implement algorithms which act according to strict mathematical rules.  
For me the main goal is translating formulas into computer code to then be able to analyse, solve or simplify them.  
The code should also be able to process known widely functions such as  
$$
\log, \ln, \sin, \cos, \tan, \tanh, \sinh, \cosh, \sum, \prod, ... 
$$
But it should also be able to process known constants such as 
$$
\pi, \mathbf{e}, \rho
$$
Later it can be extended by a physics parser extension, but I will leave that to the reader.


## The main idea
My main idea is to write a C++(99,..., 20?) library which can parse an equation string, translate it into a fitting data structure and provide an API which allows easy usage. The first big feature will be the simplification of an equation. Afterwards we will add integrals and derivatives and a step by step solution description. 

## First things first: Disclaimer
I'm not explaining how to properly write any kind of code, this is just my idea and understanding of the topic. I'm a pre-grad university student studying Mathematics. The code might contain undiscovered bugs, the project at its current state has ~98.9% test coverage. It might sound nice but it doesn't necessarily mean I did test everything to its entirety.


## Motivation
I always wanted to understand how [Matlabs `symbolic` toolbox](https://www.mathworks.com/help/symbolic/create-symbolic-numbers-variables-and-expressions.html) works. I frequently used it's
`jacobian` implementation to bypass manual calculation.  
Another example would be [pysym](https://pythonhosted.org/pysym/) or as an application [wolframalpha.com](https://www.wolframalpha.com/).  
They're all good and each of them perfectly fits for specific cases, but for some reason there is no tool which is feature complete for my needs. And since no one will ever do that for me, I'm forced to do it myself.

## Plan
So without any further ado, here's the plan:
1. Create data structure to represent an equation
2. Create parser for equations
3. Allow predefined functions for parser
4. Allow constants for parser
5. Implement equation simplification
6. Create API for simple extension to add more functionality, like integrals, derivatives and so on


## Roadblocks
- [2021-06-08] [#47](https://github.com/philsupertramp/game-math/issues/47) 
	- support for parentheses `"(", ")"` broken
	- `pow(a, b)` shortcut `"^"` calculation broken; `2 * x^2 => (2*x)^2`, but should be `2 * x^2 => 2 * (x^2)`
