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

