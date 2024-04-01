---
tags:
- post
- draft
permalink: false
title: Yet Another Explanation of Machine Learning
layout: mylayout.njk
author: Philipp
---

The purpose of this Multi-Part article is to introduce a novel approach for AI automation assistants as well as give an introduction to general machine learning to allow a broader audience to harvest this approach.

Part 1 will introduce the reader to the subject matter, part 2 explain a novel approach.

## Introduction
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

Since late 2021 and the [introduction of ChatGPT](https://openai.com/blog/chatgpt) there is a general rush towards building enormous, closed source, machine learning models to solve all sorts of tasks at the same time.

Closed source means here that these algorithms aren't available to the public as source code/some sort of program code, but can be used by external parties via API (abstract programming interface), mostly in form of some web based technology.

These algorithms/models supposedly can translate, summarise, restructure, rephrase or explain content or can come up with complete new stuff by themselves. Apart from that they can write program code, solve math problems generate music and can generate all sorts of [other computer formats](https://arxiv.org/abs/2303.08774).
Recently (September 2023) in the case of ChatGPT, OpenAI announced that their algorithm is able to process and understand not only natural language but [also images and audio data](https://openai.com/blog/chatgpt-can-now-see-hear-and-speak).

Now don't get me wrong, this sounds exciting! And in the same time futuristic, a little bit unbelievable.

But before we get deeper into this, let's define some terms and quickly review some prerequisites before we get deeper into the topic.

### What are LLMs?
Large Language Models (LLMs) are a form of machine learning models that are used to perform different tasks using natural language.
The "Large" part in the model is aimed at it's internal size, the number of _parameters_ a model contains.
In my opinion the definition of the cut between "normal" sized models and "large" models is pretty vague.
Similarily to the term _deep_ in deep learning introduced by [Yann LeCun et. al](https://doi.org/10.1038/nature14539).
As a rule of thumb I consider anything beyond $10^8$ (100M) parameters "large".

The more or less origin of this type of language models is the **Transformer** architecture, introduced 2017 by the famous paper "_Attention Is All You Need_" by [Vasvani et. al](https://arxiv.org/abs/1706.03762).
Transformers have been applied to all sorts of tasks and seem to be state of the art (SotA) for a vast amount of use cases, e.g. computer vision (["_An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale_"](https://arxiv.org/abs/2010.11929)).
But they originated from the attempt of improving older architectures of machine translation models, while _trying out "translation excercises that learning English in my middle school invoved"_[[^1]](https://www.youtube.com/watch?v=XfpMkf4rD6E&t=1116s) with Recurrent Neural Networks (RNNs).

### What's an ML Model?
> **A quick note upfront. I will try to keep the math as low as possible. But there's no way around it. So buckle up and let's do this!**


There's by far not enough time now to cover this topic thoroughly.
Generally speaking, a Machine Learning model is described through a (mostly) very very complex mathematic function that produces a desired output, let's call it $f$ for now.
$f$ expects a certain kind of input, just like any other mathematical function.
Recall for instance the pythagorean theorem from your time in school
$$
a^2 + b^2 = c^2
$$
or
$$
\sqrt{a^2+b^2} = c
$$
we could rewrite this formula as
$$
\text{pytagorean}(a, b) = \sqrt{a^2 + b^2}
$$
This makes it obvious that $a$ and $b$ are the **inputs** of the pythagorean theorem.

Internally a model contains a specific amount of _parameters_.
These parameters are combined using simple as well as complex mathematical operations, for example addition or multiplication.
Recall for instance from your geometry lessons the formula of a straight line through the center/origin of a 2D coordinate system
$$
y(x) = a \cdot x
$$
here $y$ accepts the single input $x$ and has the parameter $a$ that must be determined before we can use $y(x)$.

Let's look at the possible outcomes of this and adjust the value of $a$ as visualized here
![parameterized line]({{ '/_includes/assets/parameterized-line.gif' | url }})

You can probably tell by this visualization that there are **many**, theoretically infinite, variations of this straight line.

Next we look at a mathematically more complex example, the parabola. We begin with a simpler form, then add step by step more parameters to it.

First we examine the simplified fomula for a parabola centered in the origin $(0, 0)$ of a coordinate system.
$$
y(x) = a\cdot x^2
$$
Here $a$ is a fixed _parameter_ of the function $y$ and $x$ an **input**. Similar to the line example.

Again, a different value of $a$ will yield (in most of the cases) different results for the same input $x$.
Like for all rules, there are some exceptions, but those aren't important now.

We can change the value of $a$ as visualized here

![parameterized line]({{ '/_includes/assets/parameterized-parabola.gif' | url }})


To some extent, we can say that this is one of the most simplistic mathematical models, same applies to the first example of the straight line.

One way of Machine Learning algorithms to "learn" is to use an input and the expected/desired output for it to determine the set of required parameters.

This is something that most of you probably did in math lessons during your time in school.

Back in school a common task was to determine $a$ given a combination of $x$ and $y$.
In this example we can do that "easily" manual.

Let's say we got $x= 2$ and $y=1$ then this form of the formula can be solved for $a$ like the following. Meaning we insert the provided values of $x$ and $y$, then move parts of the left and right side of the equation around until we get a solution for $a$,
$$
\begin{align}
1 &= a \cdot 2^2\\\\
1 &= a \cdot 4\\\\
\frac{1}{4} &= a
\end{align}
$$
Great, so for this it's required to solve a small equation to get the correct value of $b$.



Another form of the parabola formula is
$$
y(x) = ax^2 + c
$$
in the above example we used $c=0$.
But $c$ is an important parameter to be able to describe a way bigger group of parabolas, because $c$ allows a shift of the center along the $y$-axis.
You can see this in the following animation.

ANIMATION 

This makes two parameters that must be determined and set into the formula before we can use the resulting function to calculate some results.
You can probably see that suddenly we have an even bigger range of possibilities.

In this example we wouldn't be able to determined the correct values of $a$ and $c$ with just a single pair of example input and output, but let's look into an example to manifest this.
Let $x=2$ and $y=1$ be the first given pair.
One approach could be to use this to solve for instance for $b$
$$
\begin{align}
1 &= a2^2 + c\\\\
1 &= a\cdot 4 +c\\\\
c &= -4a + 1
\end{align}
$$
Now inserting $c$ into the original formula
$$
\begin{align}
1 &= 4a + (-4a + 1)\\\\
1 &= 1
\end{align}
$$
Well, now we have a valid statement, but it didn't yield the desired parameter value. 
It's a correct statement, but apart from that not very informative.

No, the only way we can solve an equation with two unknown variables, i.e. $a$ and $c$, is to have two examples.

Let $x_1=2$, $y_1= 2$, $x_2=3$ and $y_2=3.25 = \frac{13}{4}$ this yields two equations from the original formula
$$
\begin{align}
I:&\\; y_1 = a\cdot x_1^2 + c \\\\
II:&\\; y_2 = a\cdot x_2^2 + c
\end{align}
$$
with the values inserted
$$
\begin{align}
I:&\\; 2 = a\cdot 2^2 +c = a\cdot 4 + c\\\\
II:&\\; 3.25 = a\cdot 3^3 + c = a\cdot 9 + c
\end{align}
$$
A common approach to solve this is using the Gaussian algorithm.
First we subtract the first equation from the second
$$
\begin{align}
III = I - II:&\\; 2-3.25 = -5a \\\\
\Leftrightarrow&\\; -1.25 = -5a
\end{align}
$$
Now we divide the left side by $-5$ to get the value of $a$
$$
\begin{align}
IV = III \cdot \left(\frac{-1}{5}\right):&\\; \frac{-1.25}{-5} = a \\\\
\Leftrightarrow&\\; a = 0.25 = \frac{1}{4}
\end{align}
$$
Finally we insert the value of $a$ into the first equation to get the value of $c$
$$
\begin{align}
V = I(a):&\\; 2 = \frac{1}{4} \cdot 4 + c \\\\
\Leftrightarrow&\\; 2 = 1 + c\\\\
\Rightarrow&\\; c = 1
\end{align}
$$
Great, so the parameters $a=0.25$ and $c=1$ are determined and we can use the formula to calculate the value of $y$ for any given $x$.

As you can imagine, this is a very simplified example of how a machine learning model learns.
And with increasing amount of parameters and complexity of the model, the more examples are required to determine the correct values of these parameters.

For closure, the full formula for the parabola is
$$
y(x) = ax^2 + bx +c
$$
but $b$ doesn't add too much visual value, so $c$ was better to make a point.
Yet $b$ is another component to express an even wider range of functions.
For instance straight lines by setting $a=0$.

Overall the variety of options of combinations that we can chose for $a,b$ and $c$ is literally endless.

Now consider the case of Large Language Models.
Like earlier explained, these models const of millions or billions of parameters.
These parameters are combined with way more advanced operations as simple additions and multiplications.

Similar to the difference between the very simplified version of this parabola formula and the other two more complex variants is the increased complexity in the expression as well as the computational amount of work required to determine the best fitting parameters.

This brings up the question of how to determine the correct values of these parameters, how to combine them and how to use them to get the desired output.

To motivate this a little bit more, let's look at another aspect of machine learning, statistics.

## How decisions are made
Statistics is a field of mathematics that is used to determine the probability of certain events to happen.
Due to the fact that Machine Learning models are mathematical representations of a certain problem which uses mathematical operations to determine the correct values of the parameters, statistics is a very important part of this field.
Especially when it comes to makeing decisions.

These decisions can be as simple as determining the correct value of a parameter, like in the parabola example, or as complex as determining the correct output of a model given a certain input.
Overall, the goal of machine learning models is to make correct decisions based on the input data and it does so by using the parameters that were determined during the learning phase.

Similar to the human nature, we can build models that are able to learn from examples and make decisions based on these examples.


Let's say we want for instance to build a language model that is able to predict new words while typing a text.
Basically an auto-completion feature for a text editor.

If you type "`How is the wea`" the model should be able to predict the next word, which in this case is "`weather`".

We can achieve this, by using a very simple model that is able to predict the next word based on the previous words.
For this we introduce the concept of _Probability_, more specific the [_Conditional Probability_](https://en.wikipedia.org/wiki/Conditional_probability).

The regular probability of an event $A$ is defined as
$$
P(A) = \frac{\text{number of times } A \text{ occured}}{\text{number of all events}}
$$

So for instance the probability of a dice showing a 6 (or any other number) is
$$
P(6) = \frac{1}{6}
$$

The conditional probability of an event $A$ occuring given an event $B$ occured already is defined as
$$
P(A|B) = \frac{P(A \cap B)}{P(B)}
$$
$P(A \cap B)$ is the probability of both events $A$ and $B$ occuring at the same time, basically the probability of $A$ multiplied by the probability of $B$.

As an example, let's say we roll a dice twice and we want to know the probability of the second roll showing a 6 given the first roll showed a 6
$$
P(6|6) = \frac{P(6 \cap 6)}{P(6)} = \frac{1/36}{1/6} = \frac{1}{6}
$$
And the result makes sense, because the probability of a dice showing a 6 is always $\frac{1}{6}$, no matter how many times we roll the dice. The results of the rolls are more or less independent.

Language on the other hand is a little bit different.
Words are not independent of each other and don't appear randomly.
There are certain rules and structures that define how words are used in a sentence.
And this is where the Conditional Probability comes into play.
We can use the Conditional Probability to determine the probability of a word occuring given the previous words.

For instance, let's say we have the sentence "`How is the weather`".
The probability of the word "`weather`" occuring given the previous word "`the`" is
$$
\begin{align}
P(\text{weather}|\text{the}) &= \frac{P(\text{weather} \cap \text{the})}{P(\text{the})}\\\\
&= \frac{\frac{1}{4} \cdot \frac{1}{4}}{\frac{1}{4}} = \frac{1}{4}
\end{align}
$$
Ok, so in this case the probability of the word "`weather`" occuring given the previous word "`the`" is $0.25$, but so is the probability for all other words to occur.
This is due to the fact that `the` and `weather` are always used together in this sentence.
So we must look at a bigger context to determine the correct probability.
Consider the extended example with the following sentences
```text
How is the weather
Where is the bookshop
Who are you
```
Now we can determine the probability of the word "`weather`" occuring given the previous word "`the`" as
$$
\begin{align}
P(\text{weather}|\text{the}) &= \frac{P(\text{weather} \cap \text{the})}{P(\text{the})}\\\\
&= \frac{\frac{1}{11} \cdot \frac{2}{11}}{\frac{2}{11}} = \frac{1}{11}
\end{align}
$$


## General idea

## Original approach

## Next iteration

## Validation

## Future/Conclusion
