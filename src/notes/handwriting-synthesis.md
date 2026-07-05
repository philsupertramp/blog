---
tags:
 - note
 - published
title: "Synthesis of handwritten text"
layout: mylayout.njk
author: Philipp
description: 
date: 2025-12-25
---

![Turkish Handwriting sample]({{ '/_includes/assets/2025-12-25/sample.png' | url }})

%TODO: Add related work

Handwritten Text Recognition (HTR)  is not a novel task, and plenty of research has been done on it over the past decades.
Yet, it is an important research area with many practical applications. While there has been a lot of progress in HTR for different languages, Turkish still presents challenges due to (a) limited data and (b) its unique linguistic traits, like agglutinative morphology (suffixes are added to words to express grammatical relation) and special characters (such as "ç", "ğ", "ı", "ö", "ş", and "ü"). These factors make word segmentation and character recognition more difficult. 

However, research has shown promising results using techniques like [transfer learning](https://dergipark.org.tr/tr/download/article-file/2145261), synthetic data generation, and [specialized models like Gated-CNN](https://turcomat.org/index.php/turkbilmat/article/view/5661). To push HTR for Turkish even further, continued work on dataset creation and model development is crucial.

The goal of this is to be able to extract all handwritten content from images like the one above.

To achieve that we must train a machine learning model to detect single or multiple character and recreate the written words `Bu türkçe bir metindir` and `bu daha çok Türkçe metin`.



Unfortunately as stated earlier, the data for handwritten Turkish is sparse and we didn’t find a publicly dataset containing images of handwritten notes along with their transcribed text for the modern Turkish language.
There are some for Ottoman texts, but modern Turkish is basically a complete different language.


Instead, we found a dataset of Turkish, Hungarian and English characters, called [“THE-dataset”](https://github.com/bartosgaye/thedataset/).


With this in mind our idea was the following:

**Use the THE dataset, combined with [MNIST](https://huggingface.co/datasets/ylecun/mnist) and [EMNIST](https://arxiv.org/pdf/1702.05373v1), to create a synthetic dataset of images, based on text extracted from wikipedia pages in Turkish.**



We implemented this idea and came up with a algorithm that renders handwritten text based on a provided input string, which resulted in many, many images like the following

<div class="img-list">

![2;Turkish Handwriting sample]({{ '/_includes/assets/2025-12-25/auto-generated-text.png' | url }})

![Turkish Handwriting sample]({{ '/_includes/assets/2025-12-25/auto-generated-text-2.png' | url }})

</div>

Now this posed some issues that you can probably see visually already. The right render contains a lot of visual fragments when characters are close to each other. Apart from that we can also see that the spelling itself isn’t consistent at all. We went as far and stated that there is no “character” in the spelling.



As a professional data scientist I obviously ignored these indicators, because I already committed to this approach, and continued the journey.



The next step in the project was to train a model to detect those handwritten notes.

For this we made plans how to solve things if they don’t work out as intended.

The first approach was a single model that detects all characters and classifies them within one pass over the full image.



First we selected YOLOv5 for experiments.

Trained a model using the synthetic dataset.

Results were really really bad, even for the very clean synthetic data.

<u>We stopped and pivoted to a two-stage approach.</u>


1. extract lines of text from images
2. extract text from cropped sub-image that contains a single line of text

Of course we chose for this the next big granularity and trained the model to restore full words from the lines of text.

The first stage here worked very well, we managed to train a model that is capable of detecting ~99% of all lines - here are some samples

 
<div class="img-list">

![labelled input data]({{ '/_includes/assets/2025-12-25/labeled-sample-1.jpg' | url }})

![detected lines by model]({{ '/_includes/assets/2025-12-25/labeled-sample-2.jpg' | url }})

</div>

For the second stage we cropped the detected lines (with a little padding around) and fed them again into YOLOv5 for word detection.
The dataset for this sub-task was easy to retrieve, we adjusted the dataset generation script to generate bounding boxes on a word level in addition to the line level bounding boxes of the first stage.

Together with those bounding boxes, we set labels for the containing words.

After recreating the dataset with new labels, we ran first experiments. Unfortunately they revealed that this was a too high goal to reach.



Clearly this task requires multiple magnitudes more data for the model to learn accurate word boundaries COMBINED WITH their word representation.

To cover the full Turkish language (~316.000 words), we would need to create a dataset that has many examples of each of them, resulting in millions of examples.

We know from the most recent findings of [large language models](https://arxiv.org/pdf/1702.05373v1) that language understanding requires a HUGE amount of data (~100M text samples).

But we’re not training an NLU model, rather just an image detection model.



So instead, we opted for the smaller set of different labels, a character level detection model.

For this we introduced a third stage, changing the pipeline to

1. detect lines of text → crop out line
2. detect words → crop out word
3. detect characters from words → restore word strings

This is illustrated in this small example

![a labelled sample (left) with it’s original counter part (right)]({{ '/_includes/assets/2025-12-25/labeled-sample-vs-original.png' | url }})



The three colors of bounding boxes mean the following:

- <span style="color: #9d9d00;">yellow</span>: character bounding boxes
- <span style="color: blue;">blue</span>: word bounding boxes
- <span style="color: red">red</span>: line bounding boxes

Training the model resulted in rather sobering results, as displayed below.

With these results it became imparable that we need to pivot to something else.

![a labelled sample (left) with it’s original counter part (right)]({{ '/_includes/assets/2025-12-25/predicted-samples-0.jpg' | url }})


### Introducing synthetic handwriting.

While researching datasets we also stumbled upon the amazing 2013 paper [“Generating Sequences With Recurrent Neural Networks”](https://arxiv.org/abs/1308.0850) by Alex Graves.

Here I want to point the reader to the section 5. “Handwriting Synthesis”.

Graves shows that when using their LSTM based architecture on a dataset of sequences of pen strokes the model can learn a conditioned representation of handwritten text **and** hence can be used to generate convincingly good handwriting.



#TODO: handwriting gif



Back in 2013, when the paper was published, no one cared about pytorch, yet. The ML landscape was filled with C/C++, Java, Matlab and some implementations in Python using Tensorflow (TF).
Some people might remember the gravitation of the API changes from TF v1 to v2 which happened in September 2019. To state it nicely this time was a pain in the ass for me.

The main pain here was the compatibility and that v2 introduced some breaking changes.



Now you can take some time and try to guess what we found when we were looking for implementations of Alex Graves' algorithms.

Obviously, we took some time and researched existing implementations and we found an amazingly documented TF project [sjvasquez/handwriting-synthesis](https://github.com/sjvasquez/handwriting-synthesis).

Unfortunately, their license is too permissive for our commercial use case (see [gh-issue](https://github.com/sjvasquez/handwriting-synthesis/issues/42)).

So we looked further and discovered more implementations based on pytorch and tensorflow

- [badhandas/handwriting_synthesis](https://github.com/badhandas/handwriting_synthesis/tree/main)
- [X-rayLaser/pytorch-handwriting-synthesis-toolkit](https://github.com/X-rayLaser/pytorch-handwriting-synthesis-toolkit)
- [adeboissiere/Handwriting-Prediction-and-Synthesis](https://github.com/adeboissiere/Handwriting-Prediction-and-Synthesis)
- [hardmaru/write-rnn-tensorflow](https://github.com/hardmaru/write-rnn-tensorflow/)


Now sadly, only the final repository ([hardmaru/write-rnn-tensorflow](https://github.com/hardmaru/write-rnn-tensorflow/)) has a license mentioned (MIT), that allows us to directly use the repository.



While browsing the repositories we also found some more sources on how to implement this paper, namely Sam Greydanus' blog on github: [https://greydanus.github.io/2016/08/21/handwriting/](https://greydanus.github.io/2016/08/21/handwriting/)

This was literally a gold mine for this task. The description of the architecture couldn’t be better and more detailed. It provided the perfect groundwork to bootstrap the project.



With that being said we combined several bits and pieces from all the repositories mentioned above to recreate the full pipeline for biased synthesis of handwritten text.

Below you can see some generations of our model from the training phase. It’s fascinating to watch the model start understanding the complex combinations of pen strokes that create language  

![After 1 training iteration]({{ '/_includes/assets/2025-12-25/stroke-it-1.png' | url }})

This gave us the first consistent pen stroke  

Next in line was visual differentiation of strokes, which worked great, too

![Stroke visualization]({{ '/_includes/assets/2025-12-25/stroke-2.png' | url }})


One we had visual feedback mechanisms in place, we started the training process with the same hyperparameters that were mentioned in Graves' paper.

 
![Final stroke training result]({{ '/_includes/assets/2025-12-25/stroke-final.png' | url }})

And... tada   

We managed to recreate the results from the paper  


After this we came up with the idea that we can use this approach for all kinds of things that are constructed from pen strokes.



The first obvious idea was to train a model on a small set of new created data, see https://huggingface.co/datasets/easybits/random_numbers, to demonstrate it’s flexibility.



To collect this data we built an app #TODO: write about alphabet https://easybits-ai.atlassian.net/wiki/spaces/easybits/pages/962789377/Alphabet 



The first version contained 461 samples of random numbers ranging from 0 to 100.000.000, some are padded with 0 to 9 digit numbers.

And it’s really really convincingly close to my own handwriting!

On the left you see training samples and on the right an example out of the training data

<div class="img-list">

![Samples for numbers]({{ '/_includes/assets/2025-12-25/number-samples.png' | url }})

![Prediction for "42069"]({{ '/_includes/assets/2025-12-25/numbers-prediction.png' | url }})

</div>


Especially pay attention to the 4 and 9 here, they really look like mine!



Good, with that being laid out we wanted to go further and started collecting samples with handwritten German language.

The German language contains a few additional characters, compared to the English alphabet, namely ß, ä, ö, and ü.
That increases the difficulty a bit. We continued the process and injected the new data into the training pipeline.
The dataset was published under [easybits/tschoermen](https://huggingface.co/datasets/easybits/tschoermen).


![Prediction for "allerdings"]({{ '/_includes/assets/2025-12-25/german-sample.png' | url }})


