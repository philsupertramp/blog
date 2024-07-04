---
tags:
 - note
 - published
title: "Faster, Better, Smaller"
layout: mylayout.njk
author: Philipp
description: A collection of notes and a small story how we merged most of our classification models into a new one.
date: 2024-07-04
---

It's independance day today, in the US. I'm not from the US, but I like the idea of independance. It's a good day to write about our recent project. 
We've been working on a new classification model for a while now.
It's a big project, and it's been a lot of work. But it's been worth it.
We've managed to merge most of our classification models into a new one.
It's faster, better, and smaller than any of the models we had before.
It's a big step forward for us, and I'm proud of what we've achieved.

This post will introduce you to the core ideas behind the new model and how we managed to merge all the old models into this new _frankensteinian_ "Multi-Head" Text Classification Model.

## Where we started
Since some time we're working on a project called ["easybits"](https://easybits.tech).
It's a platform that helps developers and non-developers to build and deploy different use-case driven Machine Learning Applications into internal and external communication tools.
Originally, we started off with Telegram (B2C) and Slack (B2B), but the platform isn't tightly coupled to any specific communication channel anymore.
Nowadays, we even offer embedded chat solutions with a variety of protocols to use, e.g. WebSockets or webhooks.

But enough advertising, let's get back to the topic.

One of the key features of the platform is the ability to classify incoming messages from the user.
For this we developed a set of classification models, each tailored to a specific use-case.

For example, we have a model that classifies messages into different sentiments, like "positive", "negative", or "neutral".
Another model could classify messages into different intents, like "greeting", "goodbye", or "question".

Now, the problem with this approach is that we ended up with a lot of different models.
To achieve a certain level of accuracy, all these models had to be trained on a lot of data and had to be quite complex.

We know that complex models are slow and require a lot of resources.

This is the main problem we want to address with the new model.

## The Problem
As initially mentioned, the classification models we created so far are quite slow and required a lot of resources.

Because we're using SOTA models, like BERT, RoBERTa, or DistilBERT, the models are quite large and require a lot of computational power to run.

Over time, it became industry standard to use these big pre-trained foundation models and fine-tune them for specific tasks.

Libraries like Huggingface's `transformers`, or `sentence-transformers` make it easy to use these models and fine-tune them for specific tasks.

Both libraries ship with a variety of pre-trained models as well as a lot of abstracted code to fine-tune these models.

Great examples for this are the [`Trainer`](https://huggingface.co/docs/transformers/main/en/main_classes/trainer#trainer) class in `transformers` or the [`SentenceTransformerTrainer`](https://sbert.net/examples/applications/retrieve_rerank/README.html) class in `sentence-transformers`.

Of course we follow this industry standard and trained our classification models on top of these pre-trained models.

This resulted in **all** of our classification models being based on the same pre-trained model, we literally just fine-tuned different heads to solve different tasks.

Hence, the only logic outcome of this situation is to enfore the models to share the same base model and only have different heads for the different tasks.

## The Solution
We basically provided the solution for this problem already in the previous section when introducing the problem.

This time, rather than solving a complex data science problem, we need to solve a software engineering problem.

To achieve the smallest memory foodprint for our classification models, we decided to develop a new model architecture that allows to run outputs of the base-model through specific classification-heads.
This can be on demand, so we can have a model that can classify messages into different sentiments, intents, and entities, or in bulk, i.e. running through all heads in sequence.

To make this difference more clear, let's have a look at the following diagrams.

First, we will look at the old model architecture.

![General Classification Models]({{ '/_includes/assets/2024-07-04/single-head-classifier.png' | url }})

You can see, the original input string gets passed through the base model and then through the classification head. This happens for every classification-head in sequence.

In this example this translates to 3 different models, each with its own base model and classification head.

<u>This is not only slow but also requires a lot of memory.</u>

To overcome this, we present the new model architecture or multi-head classification models.

![Multi-Head Classification Model]({{ '/_includes/assets/2024-07-04/multi-head-classifier.png' | url }})
The implementation of this model is quite simple.
## Implementation
To allow a certain level of flexibility, we decided to implement the model in a way that allows to provide any backbone model as well as any arbitrary amount of classification-heads.

For convenience, we implemented several helper methods to load individual components of the joint model.
Apart from that we also implemented methods to be able to dispable gradient accumulation for individual components, to simplify the training process.

The joint architecture and model implementation can be found on my [Huggingface profile](https://huggingface.co/philipp-zettl/multi-head-sequence-classification-model). 
**It's published under MIT license, so feel free to use it in your projects!**

The accompanying code to train the model can be found in the files section in `model.py`.

We will discuss here the most important parts of the architecture implementation.

The model is implemented in PyTorch, using the `transformers` library and is utilizing the `AutoModel` class to load the backbone model.

For training, we use a custom `Trainer` class that allows to train an individual head of the model joint model.

This trainer also freezes and unfreezes required parts of the model, to allow for a more efficient training process.

To optimize the training process, we use the `accelerate` library to distribute the training process on (potentially) multiple GPUs.
Apart from that it's also a quality-of-life improvement, as it allows to use the same code for single-GPU and multi-GPU training. And it actually helps a lot to prevent the beloved

```python
RuntimeError: CUDA error: out of memory
```

Alright, so you can find the code for the `Trainer` class in the HF-repo.

Let's look into the implementation of the model architecture.

To keep the code listing short, we will only show the most important parts of the model implementation and ignore most helper methods here.

```python
class MultiHeadSequenceClassification(nn.Module):
  def __init__(self, backbone, head_config, dropout=0.1, l2_reg=0.01):
    super().__init__()
    self.backbone = backbone
    self.heads = nn.ModuleDict({
        name: nn.Linear(backbone.config.hidden_size, num_classes)
        for name, num_classes in head_config.items()
    })
    self.do = nn.Dropout(dropout)
    self.l2_reg = l2_reg

  def forward(self, x, head_names=None):
    x = self.backbone(
      **x, return_dict=True, output_hidden_states=True
    ).last_hidden_state[:, 0, :]
    x = self.do(x)
    if head_names is None:
      return {name: head(x) for name, head in self.heads.items()}}
    return {name: self.heads[name](x) for name in head_names}
```
As you can see, the model is quite simple.
We use the `torch.nn.ModuleDict` entity to store the classification heads, which was the only way to store the heads in a way that allows to access them by name, while being able to use `model.parameters()` to retrieve all parameters of the model.

Otherwise, it would be nearly impossible, or require a lot of additional work to keep track and update the parameters of the model.

For optimization reasons, we also provide the option to set a dropout rate and a L2 regularization factor for the training process.
Of course, those values can be adjusted when training individual heads.

If you compare this architecture with the one from the diagram, you can see that the implementation is quite close to the diagram.

The `forward` method implements the forward pass of the model.

It receives the output of a tokenizer, which is a dictionary containing the input IDs, attention mask, and token type IDs.

You can produce this dictionary by using the `tokenizer` object from the `transformers` library. We will look closer at this in the final section of this post.

For now, it should be enough for you to know that you can get this input using
```python
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

model_input = tokenizer(
  ["Hello World!"],
  return_tensors="pt",
  padding=True,
  truncation=True
)
```

We pass this `model_input` into the backbone model - note that we unpack the tokenizer's output here - and then pass this output through our dropout layer.
Afterwards the final "embedding output" is passed individually through the classification heads.

This is exactly what we wanted to achieve with the new model architecture!

## Application Pipeline
To finalize this project, we wrapped the `MultiHeadSequenceClassification` into a `Pipeline` class that allows to easily load the model and tokenizer and classify messages.

```python
class MultiHeadSequenceClassificationPipeline:
  def __init__(self, model_conf, label_maps):
    self.model_conf = deepcopy(model_conf)
    self.label_maps = deepcopy(label_maps)
    model_conf.pop("tokenizer", None)
    self.classifier = MultiHeadSequenceClassification.from_pretrained(
      **model_conf
    ).to(torch.float16)
    self.classifier.freeze_all()
    self.tokenizer = AutoTokenizer.from_pretrained(
      self.model_conf.get('tokenizer'),
      model_max_length=128
    )

  def predict(self, texts, head_names=None):
    inputs = self.tokenizer(
      texts, return_tensors="pt", padding=True, truncation=True
    )
    outputs = self.classifier(inputs, head_names=head_names)
    return {
      name: self.label_maps[name][torch.argmax(output).item()]
      for name, output in outputs.items()
    }

  def __getattr__(self, item):
    if item.startswith("predict_"):
      head_name = item.split("_")[-1]
      return lambda texts: self.predict(texts, head_names=[head_name])
    return super().__getattr__(item)
```
The `predict` method is the main method of the pipeline. It takes a list of texts, tokenizes them, and passes them through the model. This is straight-forward.

For convenience reasons we also implemented a `__getattr__` method that allows to access individual heads of the model by calling `predict_{head_name}`, e.g. `predict_sentiment`.

**Note**: When using the `__getattr__` method, **only the labels of the desired head are computed**. Apart from that the head names have to be provided in the `label_maps` dictionary.

This pipeline then can be used for instance like this:

```python
>>> model_conf = {
...    'model_conf': {
...     'model_name': 'philipp-zettl/multi-head-sequence-classification-model',
...     'head_config': {'GGU': 3, 'sentiment': 3},
...     'tokenizer': 'BAAI/bge-m3',
...     'revision': '79c7b3954c6348d33c2af1a99818b7b9e748d5f3'
...   },
...   'label_maps': {
...     'GGU': {0: 'greeting', 1: 'gratitude', 2: 'unknown'},
...     'sentiment': {0: 'positive', 1: 'negative', 2: 'neutral'}
...   }
... }
>>> pipe = MultiHeadSequenceClassificationPipeline(**model_conf)
>>> # joint prediction
>>> print(pipe.predict("Hello World!"))
{'GGU': ['greeting'], 'sentiment': ['neutral']}
>>> # individual predictions: GGU
>>> print(pipe.predict_GGU("Hello World!"))
['greeting']
>>> # individual predictions: sentiment
>>> print(pipe.predict_sentiment("Hello World!"))
['neutral']
```

## Conclusion
We know that this architecture is not a novel approach and others probably use it in a similar way.

But overall that's quite amazing, right? We can now classify messages into different categories using a single model!

This is a big step forward for us and we're excited to see how this new model will perform in production.

We might come back to this topic in the future and provide some insights on how the model performs in production.
Until then, we're happy with what we've achieved and are looking forward to the next challenges that lie ahead.
