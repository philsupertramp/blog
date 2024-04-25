---
tags:
 - post
 - published
title: Solution driven Named Entity Recognition (NER) for helpful assistants
layout: mylayout.njk
author: Philipp
description: Named Entity Recognition (NER) is a powerful tool to extract structured information from unstructured text. This note discusses how NER can be used to build helpful assistants.
date: 2024-04-25
---
In my work, I often have to deal with unstructured text data. This data can come in many forms, such as emails, chat messages, or documents. Extracting structured information from this data is a challenging task. Named Entity Recognition (NER) is a powerful tool that can help with this task.

For more details around NER, I recommend the following:
- Advanced Article: [Chapter 7 of the NLTK book](https://www.nltk.org/book/ch07.html)
- Introductory Video: [SPACY'S ENTITY RECOGNITION MODEL](https://www.youtube.com/watch?v=sqDHBH9IjRU)

Today, I would like to describe the pipeline I use to build a solution-driven NER system.
This system is designed to extract structured information from unstructured text data and use it to build helpful assistants.
It is based on Spacy's NER model and uses a combination of data collection, data augmentation, and model training to achieve its goals.

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

Keep in mind to also translate your data points to other languages in case you want to support multiple languages.

## Data Augmentation
In this section I will give you some insights into the data augmentation process used in my pipeline.

### Prompt Augmentation
In my pipeline, I differentiate between two types of data augmentation. Augmentation of prompts, and augmentation of data points/samples.

First, I will explain the augmentation of prompts.

One seemingly popular way to augment text data is translating it to other languages, then translating it back to the original language.
If you're doing this process for a few iterations, you will end up with a more diverse data set. Yet, the quality of your data set might decrease from this approach.

Another way to augment text data is by using synonyms for certain words. But this requires a great understanding of the language you're dealing with to understand which words to replace as well as a big dictionary of synonyms. So I opted against this approach too.

Instead, I decided to collect a big set of templates and data points and then make them more robust against the human nature.

See, the main issue when we deal with human input is that humans constantly make mistakes. Instead of improving the variety of samples in our data set. We generate a wide variety of misspelled, faulty samples.

<u>We're not trying to generate coherent text, we're trying to find information in a mess.</u>

To do that, I used the following techniques that I will explain and show in details below.

1. Removal of punctuations
2. Reduction and substitution of words
3. Lowercasing
4. Prefixing
5. Typos

For each augmentation step, I assigned a probability, you can find my default setting here
```python
punctuation_prob = 10
reduction_prob = 10
substitute_prob = 10
lowercase_prob = 10
prefix_prob = 5
typo_prob = 10
```
which totals to 55% of the final data set being augmented and 45% being the original data set.

#### Removal of punctuations

Code:
```python
import random

# your prompts
prompts = [
  'What movies are playing at the theater in [LOCATION]?',
  ...
]
# punctuation characters to consider
puncuation = ['.', ',', '!', '?', ';', ':']
# filter prompts that contain punctuation
punctuated_prompts = list(filter(
  lambda x: any([p in x for p in puncuation]),
  prompts
))
# select N random prompts to remove punctuation
punctuated_prompts = random.sample(
  punctuated_prompts, 
  int((len(punctuated_prompts) * punctuation_prob) // 100)
)
# remove punctuation from selected prompts
no_punctuated_prompts = []
for prompt in punctuated_prompts:
    p = prompt
    for punc in puncuation:
        p = p.replace(punc, '')
    no_punctuated_prompts.append(p)
```

#### Reduction and substitution of words
The reduction part removes words from the prompt, while the substitution part replaces words with a random other word in the prompt.

To select a random element from a list of objects, I used the following function:
```python
def rng_elem(objs, exclude=None):
    excluded_elems = [exclude, '[', ' ']
    rn = random.choice(objs)
    while rn in excluded_elems or '[' in rn or len(rn) < 2:
        rn = random.choice(objs)
    return rn
```
Here's the code for the reduction and substitution part:
```python
prompt_backup = prompts.copy()
reduced_prompts = []
substitute_prompts = []

for prompt in prompt_backup:
    split_prompt = prompt.split(' ')
    if len(split_prompt) < 3:
        continue

    rn1 = rng_elem(split_prompt)
    rn2 = rng_elem(split_prompt, rn1)

    reduced_prompts.append(' '.join([i for i in split_prompt if i != rn1]))
    replaced_prompt = prompt.replace(rn2, '[[[REPLACEME]]]')
    replaced_prompt = replaced_prompt.replace(rn1, rn2)
    replaced_prompt = replaced_prompt.replace('[[[REPLACEME]]]', rn1)
    substitute_prompts.append(replaced_prompt)
```

#### Lowercasing
This one is straight forward, some prompts will be converted to only lowercase.

Code:
```python
import re

prompt_backup = prompts.copy()
lower_cased_prompts = []
for prompt in prompt_backup:
    results = re.findall(r'(\[[A-Za-z_1]+\])', prompt)
    new_prompt = prompt.lower()
    # replace lowercase tags with original tags
    for tag in results:
        new_prompt = new_prompt.replace(tag.lower(), tag)
    lower_cased_prompts.append(new_prompt)
```

#### Prefixing
Prefixing is a technique where we add a randomly selected phrase to the beginning of the prompt.

This introduces a new _tag_ into the prompt, which will later be replaced when the base data set gets generated.
If no set of prefixes is available, the final code will discard the tag and remove it from prompts.

Code:
```python
prefixed_prompts = []
prefix_token = '[PREFIX]'

for prompt in prompt_backup:
    new_prompt = f'{prefix_token} {prompt}'
    results = re.findall(r'(\[[A-Za-z_1]+\])', new_prompt)
    for tag in results:
        new_prompt = new_prompt.replace(tag.lower(), tag)
    prefixed_prompts.append(new_prompt)
```

#### Typos
Last but not least, we introduce typos into the prompts.

For this, I use the following method to generate typos:
```python
def introduce_typos(text, typo_prob=10):
    """
    Introduce typos into the input text with a given probability.
    
    Parameters:
        text (str): The input text.
        typo_prob (float): Probability of introducing a typo. [0-100%]
    
    Returns:
        str: Text with introduced typos.
    """
    # Define a dictionary of common typos
    typos = {
        'a': ['q', 's', 'z'],
        'b': ['v', 'g', 'h', 'n'],
        'c': ['x', 'v', 'f'],
        'd': ['s', 'e', 'f', 'c'],
        'e': ['w', 's', 'd', 'r'],
        'f': ['d', 'r', 'g', 'v'],
        'g': ['f', 't', 'h', 'b'],
        'h': ['g', 'y', 'j', 'n'],
        'i': ['u', 'o', 'k', 'j'],
        'j': ['h', 'u', 'k', 'm'],
        'k': ['j', 'i', 'l', 'o'],
        'l': ['k', 'o', 'p'],
        'm': ['n', 'j', 'k'],
        'n': ['b', 'h', 'j', 'm'],
        'o': ['i', 'p', 'l', 'k'],
        'p': ['o', 'l'],
        'q': ['w', 'a'],
        'r': ['e', 't', 'f', 'd'],
        's': ['a', 'w', 'd', 'x'],
        't': ['r', 'y', 'g', 'f'],
        'u': ['y', 'i', 'j', 'h'],
        'v': ['c', 'f', 'g', 'b'],
        'w': ['q', 's', 'e'],
        'x': ['z', 'c', 'd', 's'],
        'y': ['t', 'u', 'h', 'g'],
        'z': ['a', 'x', 's'],
        ' ': [' ']
    }
    
    # Convert text to lowercase for simplicity
    text = text.lower()
    
    # Introduce typos with given probability
    typo_text = ''
    for char in text:
        if random.random() < typo_prob and char in typos:
            char = random.choice(typos[char])
        typo_text += char
    
    return typo_text
```

The augmentation code is quite simple and can be found in the following snippet:
```python
typo_prompts = []
for prompt in prompt_backup:
    typo_prompts.append(introduce_typos(prompt, typo_prob))
```

This concludes the prompt augmentation part of the data augmentation process.

### Data Point Augmentation
The augmentation of data points uses a similar approach, but is not yet that flexible for configuration as the template augmentation.

The process is quite simple, we take each data point and apply the following techniques:
1. clean sample
2. create lemmatized version of sample
3. create stemmed version of sample
4. create randomly shuffled version by shuffling words in sample
5. create randomly removed version by removing a random word from the sample
6. add lowercase version of the sample with 50% probability

We're using `nltk` to stem and lemmatize each sample.

Don't forget to run
```python
import nltk

nltk.download('wordnet')
nltk.download('punkt')
```
at the beginning of your script.

Apart from this we use the following method in the augmentation process to clean samples, i.e. removing emojis
```python
import re


RE_EMOJI = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)


def clean_element(elem):
    if isinstance(elem, list):
        elem_out = []
        for record in elem:
            record = RE_EMOJI.sub('', record)
            elem_out.append(record.strip())
        return elem_out
    else:
        elem = RE_EMOJI.sub('', elem)
        return [elem.strip()]


def clean_elements(dataset):
    out = set()
    for elem in filter(bool, dataset):
        out |= set(clean_element(elem))
    return list(out)

```
`clean_element` can be easily extended to remove other unwanted characters or symbols, e.g. HTML tags.

With this in place, we can now augment the samples.

Code:
```python
import random
from nltk.stem import PorterStemmer, WordNetLemmatizer

def augment_samples(
        internal_datasets: list[list[str]],
        samples_per_dataset: int
    ):
    stemmer = PorterStemmer()
    lemmatizer = WordNetLemmatizer()

    datasets = internal_datasets.copy()
    augmented_datasets = []
    for samples in datasets:
        augmented_samples = []
        cleaned_samples = clean_elements(samples)
        for sample in cleaned_samples:
            # lemmatize the sample
            toks = nltk.word_tokenize(sample)
            lemmatized = ' '.join([lemmatizer.lemmatize(t) for t in toks])
            augmented_samples.append(lemmatized)
            # stem the sample
            stemmed = ' '.join([stemmer.stem(t) for t in toks])
            augmented_samples.append(stemmed)

            # Randomly shuffle the words in the sentence
            s = sample.split(' ')
            s = random.choices(s, k=len(s) - 1)
            augmented_samples.append(' '.join(s))
            # Randomly remove a word from the sentence
            s = sample.split()
            e = random.choice(list(range(len(s))))
            augmented_samples.append(''.join(s[:e]) + ' '.join(s[e+1:]))
            # add lowercase version of the sentence with 50% probability
            if random.random() * 100 > 0.5:
                augmented_samples.append(sample.lower())
        ds = augmented_samples + samples
        random.shuffle(ds)
        augmented_datasets.append(ds)

    return [s[:samples_per_dataset] for s in augmented_datasets]
```

This concludes all augmentation techniques used in my pipeline.

## Data set generation
The final step to generate the data set is to combine the augmented prompts with the augmented data points.

For this we basically iterate over the prompts and data points and replace the tags in the prompts with the data points.

To make use of this process, we need to define a structure in which the final data set will be stored.

Each of the generated samples in the final data set looks like this:
```json
[
  [
    "I'm looking for cinemas in New York that play \"The Matrix\" tonight. Any leads?",
    {
      "entities": [
        [
          48,
          57,
          "MOVIE_TITLE"
        ],
        [
          27,
          34,
          "LOCATION"
        ]
      ]
    }
  ]
]
```
A tuple of the final sample string and the entities that are present in it. Each entity is a 3-element-tuple of `START`, `END` and `TOKEN` where `START` denotes the starting index of the named entity of type `TOKEN` in the sample and `END` the ending index of the named entity.


I leave the implementation of this step to you, as it is quite straight forward and basically just string search/replacement.

Finally, we can save the generated data set to a file, e.g. `train.spacy` and `dev.spacy`.
We do that by using spaCy's `DocBin` class.

Unfortunately, this results in some samples being discarded due to the nature of the data set generation process.

These samples are usually useless anyway, as they contain errors or are not properly formatted, e.g. all whitespaces are missing.

```python
import spacy
from spacy.tokens import DocBin


nlp = spacy.blank('en')

def create_training(TRAIN_DATA, name):
    db = DocBin()
    skipped = 0
    total = 0
    for text, annotation in TRAIN_DATA:
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in annotation['entities']:
            span = doc.char_span(start, end, label=label, alignment_mode='expand')
            if span is None:
                skipped += 1
            else:
                ents.append(span)
        total += len(annotation['entities'])
        try:
            doc.ents = ents
        except ValueError:
            skipped += 1
        db.add(doc)
    print(f'Skipped {skipped}/{total} entities')
    return db
```
Assuming we have a list of samples `TRAIN_DATA` in the format mentioned above, we can now generate the final data set.

```python
# train/validation split of the data set, for simplicity we use 80/20
train_set = TRAIN_DATA[:int(len(TRAIN_DATA) * 0.8)]
valid_set = TRAIN_DATA[int(len(TRAIN_DATA) * 0.8):]

dataset = create_training(train_set, 'train')
dataset.to_disk('train.spacy')

dataset = create_training(valid_set, 'dev')
dataset.to_disk('dev.spacy')
```


## Model Training
As initially mentioned, the whole pipeline is based on the SpaCy library.
Hence the final training data set is conform to the SpaCy format and allows to use the spacy cli for the training process.

To select a configuration, we can head over to the SpaCy documentation and look for the [NER training](https://spacy.io/usage/training#ner) section.

In the Quickstart section you can find a widget to generate a configuration file for your training process.

I usually select **English** as the language, **ner** as component, **CPU** under hardware and as optimization target **accuracy**.

This generates a base configuration file that we can further tweak to our needs.

Let's assume we saved it as `base_config.cfg`. And from our data set generation process we have two files `train.spacy` and `dev.spacy`.

Following the SpaCy documentation, we can now train our model with the following commands:
```bash
# generate final config file
python -m spacy init fill-config base_config.cfg config.cfg

# train the model
python -m spacy train config.cfg --output ./output --paths.train ./train.spacy --paths.dev ./dev.spacy
```

After some time, the model will be trained and saved in the `output` directory.

Great, now we have a model that can extract named entities from text data!

## Conclusion
SpaCy is amazing and a great library to use and build NER models.

There's quite a lot of work that can be done on the data augmentation side to improve the variety of the data set further.

Sample augmentation is less developed and should be the first point to tackle.

I invite you to experiment with the pipeline and see how it can be improved. It should be a robust starting point for future endeavours.

