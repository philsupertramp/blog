---
tags:
 - note
 - published
title: Experiments with tiny-sd
layout: mylayout.njk
author: Philipp
description: My findings after discovering segmind/tiny-sd. Including fine-tuning attempts.
date: 2024-04-07
---

## Initial attempts
After discovering the distilled diffusion models by segmind I've tried out my casual trial prompts.

Here are the first results each with the default parameters via the inference UI:

Prompt: `fluffy ball`

![0148aa78-c6d3-49ed-be15-e7adb6301954](https://github.com/philsupertramp/blog/assets/9550040/f064c240-61b3-40ae-bb55-f3f4c6e6be65)


Prompt: `a woman in a field`

![bc0a3ad0-88dd-44f4-9f61-e6c7da6a9f81](https://github.com/philsupertramp/blog/assets/9550040/1af665db-d55b-4a68-9a2f-d1f835bf6f45)


Prompt: `Super Mario sitting in private jet lounge and smoking a big joint with marijuana plants growing from his head, ultra realistic, HD, best quality, ~*~aesthetic~*~`

![d7b6cb50-737f-4924-a303-5b20495933d0](https://github.com/philsupertramp/blog/assets/9550040/993bd24e-df8d-4a46-8de3-60e44fb05b9c)


## LoRA training
After collecting 29 samples from an artist I've found a few days ago, I adjusted the [dreambooth]() script that I used for my [logo-lora]() for training of tiny-sd.

I set a learning rate of `1e-4` and trained it over 1.5k iterations.

After the training the script automatically uploads the model to the hub.
I wrapped it into a space for demo purposes.



You can try my LoRA here



<iframe
	src="https://philipp-zettl-philipp-zettl-jon-juarez-lora.hf.space"
	frameborder="0"
	width="850"
	height="450"
></iframe>










