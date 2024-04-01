---
tags:
 - note
 - published
title: Zero-Shot-Classification
layout: mylayout.njk
author: Philipp
date: 2024-04-01
---
Zero-shot-classification is a task in the realm of Natural Language Processing (NLP) that aims to classify text into predefined categories without any training data.
This is achieved by using a pre-trained language model that has been trained on a large corpus of text data and has learned to understand the semantics of the language.
By providing the model with a description of the categories and the text to be classified, it can infer the category that best fits the text based on its understanding of the language.
Zero-shot-classification is a powerful tool for tasks where training data is scarce or unavailable, and can be used in a wide range of applications, such as sentiment analysis, topic classification, and spam detection.

Zero-, single- and few-shot learning are all examples of transfer learning.
The feature emerges once models reach the space of +100M parameters.
And it seems like the more parameters the better the performance.

An example for zero-shot classification can be seen here
```text
Classify the following input text into one of the following three categories: [positive, negative, neutral]

Input Text: Hugging Face is awesome for making all of these state of the art models available!
Sentiment: positive
```

The original idea of zero-shot classification/learning was introduced 2008 at [AAAI](https://aaai.org/) ["_Importance of Semantic Representation: Dataless Classification_"](https://citeseerx.ist.psu.edu/document?doi=ee0a332b4fc1e82a9999acd6cebceb165dc8645b) by M.W Chang et al. in the field of NLP and at the same conference by H. Larochelle et. al in ["_Zero-data Learning of New Tasks"](https://cdn.aaai.org/AAAI/2008/AAAI08-103.pdf) in the field of Computer Vision.
The term _zero-shot_ learning was introduced later.

The plan for a NLP zero-shot classification model is as follows:
1. Pre-train a language model on a large corpus of text data.
2. Fine-tune the language model on a zero-shot classification task by providing it with descriptions of the categories and the text to be classified.
3. Evaluate the performance of the model on the zero-shot classification task and fine-tune further if necessary.

It's as simple as that, just like any other machine learning model, the more data the better the performance.
## Pre-training a language model
Almost all language models nowadays are trained using the same approach.
The magic word here is _masked language modeling_.
The idea is to mask a random token in the input text and train the model to predict the masked token based on the context provided by the surrounding tokens.
If we do this for a large enough corpus of text data, the model will learn to understand the semantics of the language and be able to generate text that is coherent and meaningful.

And by saying large enough, I really mean large enough.
We're talking about terabytes of text data here.
The better the quality of the text data, the better the performance of the resulting model.
But if we train the same model on an even larger corpus of text data, the performance will improve even further.

Alright, but let's assume we have a large enough corpus of text data and we want to pre-train a language model on it.

For now, we'll use the famous [IMDB dataset](https://www.imdb.com/interfaces/) as an example.
Just consider it as a placeholder for a large corpus of text data.

To pre-train a language model, we can implement a transformer model using the [Hugging Face Transformers](https://huggingface.co/transformers/) library in Python.

```python
import torch
import copy
import random
from transformers import BertTokenizer, BertForMaskedLM
from torch.utils.data import DataLoader
from datasets import load_dataset
from torch.nn import functional as F


model_name = 'bert-base-uncased'
model = BertForMaskedLM.from_pretrained(model_name)
tokenizer = BertTokenizer.from_pretrained(model_name)

dataset = load_dataset('imdb')
data_loader = DataLoader(dataset, batch_size=32)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)
batched_data = data_loader.dataset['train']

mask_token = tokenizer.mask_token_id

with tqdm(batched_data, total=len(batched_data), desc='Training') as pbar:
  for batch in pbar:
      inputs = tokenizer(batch['text'], return_tensors='pt', padding=True, truncation=True)
      
      masked  = copy.deepcopy(inputs['input_ids'])
      # set random token to [MASK]
      masked[0][random.randint(0, len(masked[0]))] = mask_token
      for t in range(len(masked[0])):
        if masked[0][t] != mask_token:
          masked[0][t] = -100
      labels = inputs["input_ids"].clone()
      
      output = model(**inputs, labels=masked)

      loss = output.loss
      logits = output.logits
      loss = F.cross_entropy(logits.view(-1, tokenizer.vocab_size), labels.view(-1))
      loss.backward()
      optimizer.step()
      optimizer.zero_grad()
      pbar.set_postfix({'loss': loss.item()})

model.save_pretrained('imdb-bert-mlm')
tokenizer.save_pretrained('imdb-bert-mlm-tokenizer')
```
**Note:** This code snippet trains a BERT model on the IMDB dataset using masked language modeling (MLM) as the pre-training task.
The system requirement is around **7.5GB** of RAM. The training process can take several hours to complete, on a colab without GPU support this would take around 30h to finish.

Cool, the model is now pre-trained on the IMDB dataset using masked language modeling.
I have to stress here that even if we train this model on the whole data set and maybe even repeat this process for every single token inside it, we will still not be able to reproduce the quality of a larger scale operation.

## Fine-tuning the model on a zero-shot classification task

The next step is to fine-tune the model on a zero-shot classification task.
Actually, we don't really train for zero-shot classification, we just fine-tune the model on a classification task.
The zero-shot part comes from the fact that we don't provide any training data for the classification task, we just provide descriptions of the categories and the text to be classified.

In this example, we'll use the [MultiNLI dataset](https://www.nyu.edu/projects/bowman/multinli/) as the classification task, similar to [facebook/bart-large-mnli](https://huggingface.co/facebook/bart-large-mnli).
In this dataset, the task is to classify a sentence pair into one of three categories: entailment, contradiction, or neutral.

```python
import torch
import copy
import torch.nn as nn
import torch.nn.functional as F
from datasets import load_dataset
from torch.utils.data import DataLoader

class ClassificationModel(nn.Module):
  def __init__(self, model_name, num_labels):
    super().__init__()
    self.model = BertForMaskedLM.from_pretrained(model_name)
    self.tokenizer = BertTokenizer.from_pretrained(model_name + '-tokenizer')
    self.classifier = nn.Linear(self.model.config.hidden_size, num_labels)

  def forward(self, inputs, labels):
    inputs = self.tokenizer(inputs, return_tensors='pt', padding=True, truncation=True)
    outputs = self.model(**inputs)
    logits = self.classifier(outputs.last_hidden_state[:, 0, :])
    loss = F.cross_entropy(logits, labels)
    return loss

model_name = './imdb-bert-mlm'

model = ClassificationModel(model_name, num_labels=3)

dataset = load_dataset('multi_nli')
data_loader = DataLoader(dataset, batch_size=32)

optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)

batched_data = data_loader.dataset['train']
b_data = iter(batched_data.shuffle())
batched_data = [next(b_data) for _ in range(3)]

for epoch in range(3):
  with tqdm(batched_data, total=len(batched_data), desc=f'Epoch {epoch+1}') as pbar:
    for batch in pbar:
      inputs = batch['premise']
      labels = torch.tensor([batch['label']])
      loss = model(inputs, labels)
      loss.backward()
      optimizer.step()
      optimizer.zero_grad()
      pbar.set_postfix({'loss': loss.item()})

torch.save(model.state_dict(), 'bert-classification_nli-3-samples')
```
**Note:** This code snippet fine-tunes the pre-trained BERT model on the MultiNLI dataset for the zero-shot classification task. It is using 3 samples and trains on them over 3 epochs. It consumes **~3.7GB** of RAM and takes a few seconds to execute.

After fine-tuning the model on the classification task, we can cut the classifier head and use the model for zero-shot classification tasks.

```python
import numpy as np


class ZeroShotModel(nn.Module):
  def __init__(self, model):
    super().__init__()
    self.model = model

  def forward(self, inputs, labels=None):
    sample_logits, _ = self.model(inputs)
    label_logits, _ = self.model(labels)
    return torch.nn.functional.cosine_similarity(
        F.normalize(sample_logits),
        F.normalize(label_logits)
      )


model = ClassificationModel(model_name, num_labels=3)
model.load_state_dict(torch.load('bert-zero-shot-multi_nli-3-samples'))

zero_shot_model = ZeroShotModel(model)

samples = [
  'Natural Language Processing is a field of artificial intelligence that focuses on the interaction between computers and humans using natural language.'
]
labels = [
  'science',
  'technology',
  'politics',
  'sports',
  'entertainment'
]

def show_results(samples, labels):
  for sample in samples:
    o = zero_shot_model(sample, labels)
    ls = np.array(labels)[o.argsort(descending=True)]
    o = o[o.argsort(descending=True)]
    print(sample)
    for idl, label in enumerate(ls):
      print(f'{label}: {o[idl]}')
    print('#' * 50)

show_results(samples, labels)
```
**Note:** This code snippet defines a zero-shot classification model that uses the pre-trained BERT model fine-tuned on the MultiNLI dataset for the classification task. It then classifies the input text into one of the predefined categories using the cosine similarity between the input text and the category descriptions. The system requirement is around **2.2GB** of RAM and can be executed in less then a second.

The output of this code snippet will be:
```text
Natural Language Processing is a field of artificial intelligence that focuses on the interaction between computers and humans using natural language.
politics: 0.9016547799110413
science: 0.8136591911315918
entertainment: 0.09693698585033417
sports: -0.022199686616659164
technology: -0.138173907995224
##################################################
```

Obviosly, the performance of the model is not great and the results are not very accurate.
But this is just a simple example to demonstrate the concept of zero-shot classification.

## Using the Hugging Face Transformers library for zero-shot classification

Now, let's see how we can use the Hugging Face Transformers library to perform zero-shot classification tasks without having to train the model from scratch.

One of the most popular models for zero-shot classification tasks is  one by the team of Facebook AI Research (FAIR) that trained the BERT model on a corpus of [433k sentence pairs](https://huggingface.co/datasets/nyu-mll/multi_nli). Their model is called [`facebook/bart-larg-mnli`](https://huggingface.co/facebook/bart-large-mnli).
It uses a BERT-like architecture and has been fine-tuned on the MultiNLI dataset for the zero-shot classification task.

Thankfully, we don't need to implement the whole model ourselves, we can just use the Hugging Face Transformers library to load the model and perform zero-shot classification tasks using the `pipeline` module.

```python
from transformers import pipeline

model_name = 'facebook/bart-large-mnli'
model = pipeline(
  'zero-shot-classification',
  model=model_name,
  return_all_scores=True
)

def show_results(samples, labels):
  outputs = model(samples, labels)
  for ido, o in enumerate(outputs):
    print(samples[ido])
    for idl, l in enumerate(o['scores']):
      print(f'{labels[idl]}: {l}')
    print('#' * 50)

samples = [
    'Natural Language Processing is a field of artificial intelligence that focuses on the interaction between computers and humans using natural language.'
]
labels = [
  'science',
  'technology',
  'politics',
  'sports',
  'entertainment'
]

show_results(samples, labels)
```
This will output the following results:
```text
Natural Language Processing is a field of artificial intelligence that focuses on the interaction between computers and humans using natural language.
science: 0.9367563724517822
technology: 0.02281026728451252
politics: 0.01624997705221176
sports: 0.016005270183086395
entertainment: 0.008178026415407658
##################################################
```
**Note:** This requires around **3.25GB** of RAM and can be executed in a few seconds.

## Improving the zero-shot classification model
One way to improve this model is to include a prompt template that provides additional context to the model.

This approach is simple and effective, but it has some limitations.
I first got introduced to the idea described in the NLI improvement in the great blog post by Joe Davison ["_Zero-Shot Learning in Modern NLP_"](https://joeddav.github.io/blog/2020/05/29/ZSL.html).

The results of the previous example are already pretty good, we will use a different example that shows a bigger improvement.

For instance consider the task of classifying autors of quotes for a predefined set of authors.
Using the same model as before we can add more context to the classification task using the template "`This is a quote by {}.`".
This can be achieve by using the `hypothesis_template` argument of the pipeline call.
We will compare the performance with the adjusted template to the default case to see the improvement.
```python
template = 'This is a quote by {}.'

samples = [
    'An eye for eye only ends up making the whole world blind.\nby Gandhi'
]
labels = [
  'ghandi',
  'galileo',
  'sokrates',
  'newton',
]
def show_results(samples, labels, template='This example is {}.'):
  outputs = model(samples, labels, hypothesis_template=template)
  for ido, o in enumerate(outputs):
    print(samples[ido])
    for idl, l in enumerate(o['scores']):
      print(f'{labels[idl]}: {l}')
    print('#' * 50)

print('Default template:')
show_results(samples, labels)
print('Adjusted template:')
show_results(samples, labels, template)
```
This will output the following results:
```text
Default template:
An eye for eye only ends up making the whole world blind.
by Gandhi
ghandi: 0.8371322154998779
galileo: 0.0707320049405098
sokrates: 0.060743119567632675
newton: 0.03139260783791542
##################################################
Adjusted template:
An eye for eye only ends up making the whole world blind.
by Gandhi
ghandi: 0.9961664080619812
galileo: 0.0015960732707753778
sokrates: 0.0014651468954980373
newton: 0.0007723282324150205
##################################################
```
Amazing, 99.6% accuracy with the adjusted template compared to 83.7% with the default template is a great improvement.

Of course this is just a simple toy example, but it demonstrates the power of zero-shot classification and how it can be used to solve a wide range of tasks without the need for training data.

## Conclusion
Zero-shot classification is a powerful tool in the realm of Natural Language Processing that allows us to classify text into predefined categories without any training data.

I will continue to explore the possibilities of zero-shot classification and how it can be used to solve a wide range of tasks in the future.
We will probably see more notes/posts on this topic in the future.
The next little project will be to curate a mask language dataset and train a model on it.
As well as to explore the possibilities of the here used model on a larger scale.

I have an unused NVIDIA GPU (RTX 20xx with 6GB VRAM) and I'm thinking about using it for training a model on a larger scale.
Maybe even to look into distributed training and how it can be used to train models on even larger datasets by using my desktop computer together with my laptop (RTX 4070 with 8GB VRAM)

## References
- [AAAI](https://aaai.org/)
- [Joe Davison: Zero-Shot Learning in Modern NLP](https://joeddav.github.io/blog/2020/05/29/ZSL.html)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [Hugging Face Zero-Shot-Classification](https://huggingface.co/tasks/zero-shot)
- [Paper: Zero-Shot Learning - A Comprehensive Evaluation of the Good, the Bad and the Ugly](https://arxiv.org/pdf/1707.00600.pdf)

