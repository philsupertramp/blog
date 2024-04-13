---
tags:
 - note
 - published
title: The Wet Dream of a LoRA Explorer
layout: mylayout.njk
author: Philipp
description: My journey with text-to-image generation models continues. This week I tried to generate images using the IP-Adapter.
date: 2024-04-13
---

This week I started off with training yet another LoRA model for another based model, [segmind/SSD-1B](https://huggingface.co/segmind/SSD-1B). 
I was excited to see how the model would perform, considering it is based on SDXL, not as tiny-sd and small-sd based on the older SD-1.5.  
My experience with SDXL has been quite positive so far, so I was looking forward to seeing how the model would perform.

Here you can see some images generated with SDXL, generated with one of my telegram bots

> Prompt: `Newton running down an endless staircase`

![Newton running down an endless staircase]({{ '/_includes/assets/newton.jpg' | url }})


And some more examples without prompt

![generated image collage]({{ '/_includes/assets/collage.jpg' | url }})


Now with this experience in mind, I started training the LoRA model. I used the same settings as before, just using a different base model.

The result was actually quite good. This time I trained it based on 50 images of my cat

![used cat images]({{ '/_includes/assets/collage-cat.jpg' | url }})

The final LoRA model is available [here](https://huggingface.co/philipp-zettl/ssd-butters-lora) you can use it with the inference API.

But I would recommend to not use the inference UI, as this model heavily requires a negative prompt to generate good images.

Here are some examples:


From that point on I knew I will have to do some serious prompt engineering to make things work and to produce better images.

The next big thing on my mental To-do list for image generation was [ControlNet](https://github.com/lllyasviel/ControlNet) a rather novel approach to control diffusion models.  But before I took a deep dive I wanted to explore one more thing, similar to ControlNet.  
I'm talking about [IP-Adapter](https://ip-adapter.github.io/).

## The last LoRA?
Well, well, well... I don't know where to start.

So after setting up everything, which means installing dependencies, downloading some dubious binaries from a huggingface 🤗 repo and patching all things together, I got pretty shocking results.

> Prompt: `...`

Input image:

...

Generated output

[ ... TODO add Margot Robbie in red dress IMG ]

## The Setup
I ran some more experiments, this time with the face of a non-existing person from [thispersondoesnotexist.com](https://thispersondoesnotexist.com/).

Here I will explain it in a step-by-step guide.

For a simplified usage head over to my repo [philipp-zettl/factory](Https://GitHub.com/philipp-zettl/factory) where you will find a web-api that handles the most common use cases.

## Throwbacks
Due to the nature of the [IP-Adapter](https://github.com/tencent-ailab/IP-Adapter) library I wasn't able to run SDXL in this experiment.

Most of the time I'm using `DiffusionPipeline` when running SDXL. And I can only do that on my limited hardware using `DiffusionModel.snable_model_cpu_offload()`.  
Unfortunately, IP-Adapter doesn't support this and throws errors because some embeddings are on different devices.
Now one way to fix this is to implement this feature upstream and post a PR to the repository. Let's see...