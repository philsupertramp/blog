---
tags:
 - note
 - published
title: Solution driven Named Entity Recognition (NER) for helpful assistants
layout: mylayout.njk
author: Philipp
description: Named Entity Recognition (NER) is a powerful tool to extract structured information from unstructured text. This note discusses how NER can be used to build helpful assistants.
date: 2024-04-21
---
In my work, I often have to deal with unstructured text data. This data can come in many forms, such as emails, chat messages, or documents. Extracting structured information from this data is a challenging task. Named Entity Recognition (NER) is a powerful tool that can help with this task.

For more details around NER, I recommend the following:
- Advanced Article: [Chapter 7 of the NLTK book](https://www.nltk.org/book/ch07.html)
- Introductory Video: [SPACY'S ENTITY RECOGNITION MODEL](https://www.youtube.com/watch?v=sqDHBH9IjRU)

Today, I would like to describe the pipeline I use to build a solution-driven NER system.
This system is designed to extract structured information from unstructured text data and use it to build helpful assistants.

Mainly, the pipeline consists of the following steps:
1. Data Collection: Combine multiple sources of structured text data into a single dataset used for training (and evaluating) the NER model.
2. Training: Train a custom NER model using the combined dataset.

## Data Collection
The data collection pipeline is more or less straight forward.

To create a data set, we combine a set of text templates with a set of potential entities.
The text templates are used to generate synthetic text data, while the entities are used to annotate the text data.

Let's say we want to build an assistant for movies that can look up information about movies and find theaters nearby that play it.

For this we would need to extract two types of entities: movie titles and locations.
So a potential request by a user could look like this:
```text
What movies are playing at the theater in New York?
```
In this case, the entities would be:
```text
MOVIE_TITLE = null
LOCATION = New York
```
and the text template would be:
```text
What movies are playing at the theater in [LOCATION]?
```

Another example could be:
```text
Is "The Matrix" playing at the theater in San Francisco?
```
here we have
```text
MOVIE_TITLE = The Matrix
LOCATION = San Francisco
```
and the template
```text
Is "[MOVIE_TITLE]" playing at the theater in [LOCATION]?
```

And last but not least, we could have a request like this:
```text
Tell me more about "The Matrix".
```
with the entities
```text
MOVIE_TITLE = The Matrix
LOCATION = null
```
and the template
```text
Tell me more about "[MOVIE_TITLE]".
```
After spending some time on collecting these examples, we will end up having three data sets.

For my pipeline I organized them in individual `.csv` files, where each row represents a single example.

Continuing with the example above, the data sets would look like this:

`movie_titles.csv`
```csv
MOVIE_TITLE
The Matrix
Pulp Fiction
Parasite
...
```
`locations.csv`
```csv
LOCATION
New York
San Francisco
Los Angeles
Mexico City
Barcelona
...
```
and `movie_requests.csv`
```csv
TEMPLATE
What movies are playing at the theater in [LOCATION]?
Is "[MOVIE_TITLE]" playing at the theater in [LOCATION]?
Tell me more about "[MOVIE_TITLE]".
Do you have any information about "[MOVIE_TITLE]"?
Any movies playing in [LOCATION]?
What's playing at the theater in [LOCATION]?
...
```

Amazing, now we have our base data set, that we will continue to work with in the future section.

But hold on a minute, we missed something quite important along the way.

> How do we generate a good amount of these data points?

That's a good question! One way how we will make the data more diverse is by using data augmentation techniques in the future section.

> But what's a good base for data augmentation?

I noticed through personal experiments that the bigger the base data set, the better the results will be.
In other words, spend more time engineering these templates and entities, and you will be rewarded with a better performing model.

One way to get started is prompting one of the freely available LLMs like ChatGPT or GPT-3 with a few examples and let it generate more examples for you.

They're also quite good at translating and creating multi-lingual data sets.

In terms of data points such as movie titles and locations, you can use APIs like the [OMDb API](http://www.omdbapi.com/) or [dr5hn/countries-states-cities-database](https://github.com/dr5hn/countries-states-cities-database) to get a good starting point.

## Data Augmentation

