---
tags: post
title: Thowards relyable assistants in a world of LLMs
layout: mylayout.njk
author: Philipp
permalink: /blog/posts/{{ title | slugify }}
date: 2024-03-24
---

<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script type="text/x-mathjax-config">
MathJax.Hub.Config({
  tex2jax: {inlineMath: [['\\$','\\$'],['$$','$$'], ['\\(','\\)'], ['\\[', '\\]']]}
});
</script>
  <script id="MathJax-script" async
          src="https://cdn.jsdelivr.net/npm/mathjax@3.0.1/es5/tex-mml-chtml.js?config=TeX-AMS_CHTML">
  </script>
# Introduction
To constantly push back against novel technologies has been part of my life since many years.
While learning the skill of software development researching algorithms, libraries or programming languages, 
it is very hard to avoid being overwhelmed by the [appeal of novelty](https://en.wikipedia.org/wiki/Appeal_to_novelty) (which I personally know as _Shiny Object Syndrom_).
Now don't get me wrong, curiosity and the urge to try out something new, like using new technologies/approaches to solve problems, is what keeps us moving.
Otherwise we wouldn't be where we are, as a human race.

Unfortunately, most of the time in a professional setting one can not give in this itch, this glimps of curiosity, because one needs to be productive and yielding stable and relyable results.
But how can we be productive if we stick to the same workflow or problem solving approach?

Well, this is where it gets tricky, somewhat blurry, especially for novices.
One, and probably the easiest way to increase productivity is using more productive workflows, which mostly introduce new tools.
Of course throughout a career one gains the experience and a sense of this to decide quite confidently when to give in to new technology and when to use old-fashioned approaches.
Due to the fact that each of us is taking a different path, taking different approaches and ways to end up at same results, especially in software development, this becomes increasingly hard to handle.

We all know that. You decide to use some new piece of technology, face an issue, search for help and end up with someone telling you

> I can't help you with your actually problem, but did you ever consider to use X instead of Y to solve your issue?

Of course not. And obviously you wouldn't have asked your if you did.

This brings me to the actual topic of this article, the oh-so-brilliant all-fitting shoe called _Large Language Models_.
But before we get into this, let's define some terms and quickly review some prerequisites before we get deeper into the topic of this article.

## What are LLMs?
Large Language Models (LLMs) are a form of machine learning models that are used to perform different tasks using natural language.
The "Large" part in the model is aimed at it's internal size, the number of _parameters_ a model contains.
In my opinion the definition of the cut between "normal" sized models and "large" models is pretty vague.
Similarily to the term _deep_ in deep learning introduced by [Yann LeCun et. al](https://doi.org/10.1038/nature14539).
As a rule of thumb I consider anything beyond \\(10^8\\) (100M) parameters "large".

The more or less origin of this type of language models is the **Transformer** architecture, introduced 2017 by the famous paper "_Attention Is All You Need_" [Vasvani et. al](https://arxiv.org/abs/1706.03762).
Transformers have been applied to all sorts of tasks and seem to be state of the art (SotA) for a vast amount of use cases, e.g. computer vision (["_An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale_"](https://arxiv.org/abs/2010.11929)).
But they originated from the attempt of improving older architectures of machine translation models, while _trying out "translation excercises that learning English in my middle school invoved"_[[^1]](https://www.youtube.com/watch?v=XfpMkf4rD6E&t=1116s) with Recurrent Neural Networks (RNNs).

## What's an ML Model?
There's by far not enough time now to cover this topic thoroughly.
Generally speaking, a Machine Learning model is described through a (mostly) very very complex mathematic function that produces a desired output, let's call it \\(f\\) for now.
\\(f\\) expects a certain kind of input, just like any other mathematical function.
Recall for instance the pythagorean theorem from your time in school
\\[
a^2 + b^2 = c^2
\\]
or
\\[
\sqrt{a^2+b^2} = c
\\]
we could rewrite this formula as
\\[
\text{pytagorean}(a, b) = a^2 + b^2
\\]
This makes it obvious that \\(a\\) and \\(b\\) are the **inputs** of the pythagorean theorem.

Internally a model contains a specific amount of _parameters_.
These parameters are combined using simple as well as complex mathematical operations, for example addition or multiplication.
Recall for instance from your geometry lessons the fomula for a parabular, i.e. a simple quadratic function.
You probably got introduced to it in a similar form to
\\[
y(x) = ax^2
\\]
Here \\(a\\) is a  fixed _parameter_ of the function \\(y\\) and \\(x\\) an **input**.
A different vaslue of \\(a\\) will yield (in most of the cases) different results for the same input \\(x\\).
Like for all rules, there are some exceptions, but those aren't important now.

We can adjust the value of \\(a\\) as visualized here

![parabular](https://upload.wikimedia.org/wikipedia/commons/4/4f/Concavity_of_a_parabola.gif)




# General idea

# Original approach

# Next iteration

# Validation

# Future/Conclusion
