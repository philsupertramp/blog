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
Since over a year I'm on the hunt for lightweight architectures and models for generative AI that I can run on my mid-end consumer hardware (GTX 2060 6GB VRAM/GTX 3040 8 GB VRAM).

Now recently I've trained a LoRA for stable diffusion XL (SDXL) on a [logo dataset](https://huggingface.co/dataset/logo-wizard/modern-logo-dataset) and published it on [hugging face 🤗](https://huggingface.co/philipp-zettl/logo_LoRA).

But this LoRA requires to run [SDXL](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) as a base model.
Which is quite big and barely fits onto any of my GPUs.
The only option I have is CPU offloading.

But that comes with a great speed decrease.

So I desperately wanted to find a smaller model!

## Initial attempts
After discovering the distilled diffusion models by segmind I've tried out my casual trial prompts.

Here are the first results each with the default parameters via the inference UI:

Prompt: `fluffy ball`

![0148aa78-c6d3-49ed-be15-e7adb6301954](https://github.com/philsupertramp/blog/assets/9550040/f064c240-61b3-40ae-bb55-f3f4c6e6be65)


Prompt: `a woman in a field`

![bc0a3ad0-88dd-44f4-9f61-e6c7da6a9f81](https://github.com/philsupertramp/blog/assets/9550040/1af665db-d55b-4a68-9a2f-d1f835bf6f45)


Prompt: `Super Mario sitting in private jet lounge and smoking a big joint with marijuana plants growing from his head, ultra realistic, HD, best quality, ~*~aesthetic~*~`

![d7b6cb50-737f-4924-a303-5b20495933d0](https://github.com/philsupertramp/blog/assets/9550040/993bd24e-df8d-4a46-8de3-60e44fb05b9c)

Well, frankly apart from the fluffy ball the results are rather mediocre.
I'm wondering if we can achieve something else maybe I should just try something _easier_.

For instance cartoons and cartoon-like pictures/paintings.

Recently I found the artist [Jon Juarez](https://lama.co/harriorrihar/) through a post on mastodon.
And I really like their work!

So I wanted to try out if I can generate something similar to their work :)

Prompt: `painting with line shading of a cave`

![25f3b1a6-a68c-424f-9af5-101252f5edeb](https://github.com/philsupertramp/blog/assets/9550040/eb5d143e-c0a5-4953-a089-315520a46cd8)

That's nice! I wonder how far I can go with this.

Because of that I felt obliged to train a LoRA to maybe improve the style of generated paintings.

## LoRA training
After collecting 29 samples from an artist, I adjusted the [dreambooth](https://dreambooth.github.io/) script that I used for my logo-LoRA for training of tiny-sd.

I set a learning rate of `1e-4` and trained it over 1.5k iterations.

After the training the script automatically uploads the model to the hub.
I wrapped it into a space for demo purposes.

**Note:** you need to use the "_magic phrase_" `... by JON_JUAREZ ...` to trigger the LoRA.

Here are some results:

Prompt: `Pastel color painting with line shading by JON_JUAREZ of a dark cave`

![image (3)](https://github.com/philsupertramp/blog/assets/9550040/d2764b2d-554e-4bf2-89ff-5a383de73cfe)

Prompt: `Painting with line shading by JON_JUAREZ of a dark cave`

![image (1)](https://github.com/philsupertramp/blog/assets/9550040/b41befc7-08dc-4342-8f1f-629db83abb09)

Prompt: `Wizard`

![image(15)](https://github.com/philsupertramp/blog/assets/9550040/67b77e20-5d82-4c51-b673-b9749711c3ed)


Prompt: `Wizard by JON_JUAREZ`

![image(14)](https://github.com/philsupertramp/blog/assets/9550040/bc98d6e8-f3a1-4fa4-92fd-89d2887e5eb6)


Prompt: `Landscape`

![image(16)](https://github.com/philsupertramp/blog/assets/9550040/d505075b-7d76-422f-a970-e34bb2d872c1)



Prompt: `Landscape by JON& JUAREZ`

![image(17)](https://github.com/philsupertramp/blog/assets/9550040/b7f88629-d81f-498e-972d-888b8c6e5fd5)



You can try my LoRA here



<iframe
	src="https://philipp-zettl-philipp-zettl-jon-juarez-lora.hf.space"
	frameborder="0"
	width="850"
	height="450"
></iframe>










