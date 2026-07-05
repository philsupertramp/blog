---
tags:
 - post
 - published
title: "STENCIL: Structured Template Extraction via Non-autoregressive Constrained Inpainting Loops"
layout: mylayout.njk
author: Philipp
description: something something BERT and diffusion
date: 2025-12-05
---
Back in late October I was browsing through reddit visiting my usual [r/LocalLlama](https://www.reddit.com/r/LocalLLaMA/) subreddit and I found this

<div>
  <style>
  .card {
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    transition: 0.3s;
    width: 30rem;
    padding: 15px;
    margin-left: 15rem;
  }
  .card:hover {
    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
  }
  .card>.container {
    padding: 2px 16px;
  }
  </style>
   <div class="card">
    <div class="container">
      <h4><b><a href="https://www.reddit.com/user/Individual-Ninja-141/">u/Individual-Ninja-141</a>
  in<a href="https://www.reddit.com/r/LocalLLaMA/">LocalLLaMA</a>
</b></h4>
      <a href="https://www.reddit.com/r/LocalLLaMA/comments/1osydym/berts_that_chat_turn_any_bert_into_a_chatbot_with/">
        BERTs that chat: turn any BERT into a chatbot with dLLM
      </a><br>
    </div>
  </div>
</div>


And I thought to myself

> Huh, that's cool. I didn't think about that yet, but this feels kind of like diffusion in image generation. The model looks at a chunk of `[MASK]` tokens and then diffuses the response out of them. With every diffusion step the answer get's more "detailed" and "better".

This motivated me to look further into this idea and a quick google search directed me to the beautiful blog of [Nathan Barry](https://nathan.rs/), particularily their blog post ["BERT is just a Single Text Diffusion Step"](https://nathan.rs/posts/roberta-diffusion/). Which then led me to the original 2022 paper by He et. al. called [DiffusionBERT](https://arxiv.org/abs/2211.15029).

![RoBERTa diffusion](/_includes/assets/2025-12-05/roberta-diffusion.gif)

Funnily, before stumbling upon this paper I planned to call this algorithm DiffuBERTa due to the original idea of using RoBERTa with diffusion, just like Nathan.

But I had a different plan. What I want to produce is not a general purpose language model, no I want to be use this approach to do a specific sub task of Information Extraction, the extraction of structured output.

We have been doing structured data extraction wrong. Treating it as text generation (left-to-right) is inefficient and error-prone.
STENCIL reframes extraction as Schema-Constrained Inpainting, allowing us to utilize bidirectional context and parallel decoding to achieve sub-linear latency with mathematically guaranteed syntax.

In theory this yields the following advantages
1. **Speed:** Reducing latency from Autoregressive $\mathcal{O}(N)$ to $\mathcal{O}(K)$ (where $K$ is refinement steps, independent of $N$ number of output tokens)
2. **Reliability**: Syntax errors are impossible because the syntax is the input template, not the output prediction.
3. **Efficiency**: Achieving GPT-4 level extraction performance on consumer hardware using a BERT-sized model (ModernBERT).
