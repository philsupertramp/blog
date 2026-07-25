---
tags:
 - post
 - published
 - semantic search
 - ml
title: "Fine-Tuning Micro Embedding Models for Domain-Specific Semantic Search"
layout: mylayout.njk
author: Philipp
description: "A deep dive into replacing a prototype with a robust, custom-trained semantic search engine for Magic: The Gathering, deployed as a full-stack application on a local Kubernetes cluster."
published: 2026-07-25
---
<style>
/* Responsive 6-image gallery grid */
  .gallery-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    margin: 1.5rem 0;
  }

  .gallery-grid div {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .gallery-grid img {
    width: 100%;
    height: auto;
    border-radius: 6px;
    border: 1px solid #ddd;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    object-fit: cover;
  }

  .gallery-grid p {
    font-size: 0.85rem;
    color: #666;
    margin-top: 0.4rem;
    text-align: center;
  }

  /* Tablet: 2 columns x 3 rows */
  @media (min-width: 600px) {
    .gallery-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  /* Desktop: 3 columns x 2 rows */
  @media (min-width: 900px) {
    .gallery-grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }
table {border-collapse: collapse; width: 50%; overflow-y: scroll} tr,table,th,td { border: 1px solid; }
.img-box {
    display: grid;
    grid-template-columns: 1fr; /* Defaults to a single stacked column for mobile */
    gap: 1.5rem; /* Adds space between the two images */
    align-items: center; /* Vertically centers them if they are different heights */
  }

  /* Ensures the markdown images scale down and don't break out of the layout */
  .img-box img {
    width: 100%;
    max-width: 75%;
    margin: auto 12.5% auto;
    height: auto;
    border-radius: 8px; /* Optional: adds a nice curve to the charts */
  }

  /* Kicks in on tablets and desktops */
  @media (min-width: 768px) {
    .img-box {
      grid-template-columns: 1fr 1fr; /* Splits into two equal side-by-side columns */
    }
  }
</style>
Back in 2025 I was working for a company that had/has the big vision to build an AI driven automation platform for different tasks, including "simple" semantic search.

Around the same time, I got deeply into Magic: The Gathering (MTG) back again, after almost 20 years.
Originally, it started out with some booster packs, but quickly and with the financial background of a grownup I ended up accumulating a little collection of more than 3.5k cards, out of which ~1.5k (45.69% to be precise) are unique.

<details>
<summary>Raw stats for the nerds</summary>

<div style="display: flex">
<div style="width: 45%">
Overall Stats

<table border="1" style="border-collapse: collapse; width: 100%; text-align: left;">
<tr>
<td> Unique Cards in collection </td>
<td> 1559 [45.69%] </td>
</tr>
<tr>
<td>Total Cards in Collection</td>
<td>3412</td>
</tr>
</table>

</div>

<div style="width: 45%; margin-left: 5%">
Color Stats

<table border="1" style="border-collapse: collapse; width: 100%; text-align: left;">
  <thead>
    <tr style="background-color: #f2f2f2;">
      <th style="padding: 8px;">Category</th>
      <th style="padding: 8px; text-align: right;">Count</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px;">Blue</td><td style="padding: 8px; text-align: right;">195</td></tr>
    <tr><td style="padding: 8px;">Red</td><td style="padding: 8px; text-align: right;">205</td></tr>
    <tr><td style="padding: 8px;">Green</td><td style="padding: 8px; text-align: right;">212</td></tr>
    <tr><td style="padding: 8px;">Borderless</td><td style="padding: 8px; text-align: right;">12</td></tr>
    <tr><td style="padding: 8px;">Retro</td><td style="padding: 8px; text-align: right;">90</td></tr>
    <tr><td style="padding: 8px;">Eldrazi</td><td style="padding: 8px; text-align: right;">6</td></tr>
    <tr><td style="padding: 8px;">Black</td><td style="padding: 8px; text-align: right;">196</td></tr>
    <tr><td style="padding: 8px;">Artifacts</td><td style="padding: 8px; text-align: right;">91</td></tr>
    <tr><td style="padding: 8px;">White</td><td style="padding: 8px; text-align: right;">212</td></tr>
    <tr><td style="padding: 8px;">ART</td><td style="padding: 8px; text-align: right;">38</td></tr>
    <tr><td style="padding: 8px;">Mixed</td><td style="padding: 8px; text-align: right;">168</td></tr>
    <tr><td style="padding: 8px;">Lands</td><td style="padding: 8px; text-align: right;">115</td></tr>
    <tr><td style="padding: 8px;">Borderless Anime</td><td style="padding: 8px; text-align: right;">8</td></tr>
    <tr><td style="padding: 8px;">Artwork</td><td style="padding: 8px; text-align: right;">7</td></tr>
    <tr><td style="padding: 8px;">Showcase</td><td style="padding: 8px; text-align: right;">1</td></tr>
    <tr><td style="padding: 8px;">Legendary</td><td style="padding: 8px; text-align: right;">5</td></tr>
  </tbody>
</table>
</div>
</div>

<div style="overflow-x: scroll">
Set Stats

<table border="1" style="border-collapse: collapse; width: 100%; text-align: right;">
  <thead style="position: sticky; top: 0;">
    <tr style="background-color: #f2f2f2;">
      <th style="padding: 8px; text-align: left;">Set</th>
      <th style="padding: 8px;">Unique Cards Collected</th>
      <th style="padding: 8px;">Total Cards Collected</th>
      <th style="padding: 8px;">Cards Missing</th>
      <th style="padding: 8px;">Cards Missing Main Set</th>
      <th style="padding: 8px;">Cards Collectable Total</th>
      <th style="padding: 8px;">Cards Collectable Set</th>
      <th style="padding: 8px;">Duplicates</th>
      <th style="padding: 8px;">% Duplicates</th>
      <th style="padding: 8px;">% Collected</th>
      <th style="padding: 8px;">% Collected [main set]</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; text-align: left;">RVR</td><td style="padding: 8px;">289</td><td style="padding: 8px;">1043</td><td style="padding: 8px;">168</td><td style="padding: 8px;">54</td><td style="padding: 8px;">457</td><td style="padding: 8px;">291</td><td style="padding: 8px;">232</td><td style="padding: 8px;">22.24%</td><td style="padding: 8px;">63.24%</td><td style="padding: 8px;">81.44%</td></tr>
    <tr><td style="padding: 8px; text-align: left;">M10</td><td style="padding: 8px;">81</td><td style="padding: 8px;">180</td><td style="padding: 8px;">168</td><td style="padding: 8px;">168</td><td style="padding: 8px;">249</td><td style="padding: 8px;">249</td><td style="padding: 8px;">99</td><td style="padding: 8px;">55.00%</td><td style="padding: 8px;">32.53%</td><td style="padding: 8px;">32.53%</td></tr>
    <tr><td style="padding: 8px; text-align: left;">CON</td><td style="padding: 8px;">14</td><td style="padding: 8px;">14</td><td style="padding: 8px;">131</td><td style="padding: 8px;">131</td><td style="padding: 8px;">145</td><td style="padding: 8px;">145</td><td style="padding: 8px;">0</td><td style="padding: 8px;">0.00%</td><td style="padding: 8px;">9.66%</td><td style="padding: 8px;">9.66%</td></tr>
    <tr><td style="padding: 8px; text-align: left;">WWK</td><td style="padding: 8px;">7</td><td style="padding: 8px;">7</td><td style="padding: 8px;">138</td><td style="padding: 8px;">138</td><td style="padding: 8px;">145</td><td style="padding: 8px;">145</td><td style="padding: 8px;">0</td><td style="padding: 8px;">0.00%</td><td style="padding: 8px;">4.83%</td><td style="padding: 8px;">4.83%</td></tr>
    <tr><td style="padding: 8px; text-align: left;">ROE</td><td style="padding: 8px;">26</td><td style="padding: 8px;">28</td><td style="padding: 8px;">222</td><td style="padding: 8px;">222</td><td style="padding: 8px;">248</td><td style="padding: 8px;">248</td><td style="padding: 8px;">2</td><td style="padding: 8px;">7.14%</td><td style="padding: 8px;">10.48%</td><td style="padding: 8px;">10.48%</td></tr>
    <tr><td style="padding: 8px; text-align: left;">ZEN</td><td style="padding: 8px;">22</td><td style="padding: 8px;">25</td><td style="padding: 8px;">227</td><td style="padding: 8px;">227</td><td style="padding: 8px;">249</td><td style="padding: 8px;">249</td><td style="padding: 8px;">3</td><td style="padding: 8px;">12.00%</td><td style="padding: 8px;">8.84%</td><td style="padding: 8px;">8.84%</td></tr>
    <tr><td style="padding: 8px; text-align: left;">INR</td><td style="padding: 8px;">282</td><td style="padding: 8px;">572</td><td style="padding: 8px;">210</td><td style="padding: 8px;">55</td><td style="padding: 8px;">490</td><td style="padding: 8px;">287</td><td style="padding: 8px;">290</td><td style="padding: 8px;">50.70%</td><td style="padding: 8px;">57.14%</td><td style="padding: 8px;">80.84%</td></tr>
    <tr><td style="padding: 8px; text-align: left;">DSK</td><td style="padding: 8px;">220</td><td style="padding: 8px;">512</td><td style="padding: 8px;">197</td><td style="padding: 8px;">72</td><td style="padding: 8px;">417</td><td style="padding: 8px;">286</td><td style="padding: 8px;">292</td><td style="padding: 8px;">57.03%</td><td style="padding: 8px;">52.76%</td><td style="padding: 8px;">74.83%</td></tr>
    <tr><td style="padding: 8px; text-align: left;">TDM</td><td style="padding: 8px;">210</td><td style="padding: 8px;">391</td><td style="padding: 8px;">216</td><td style="padding: 8px;">78</td><td style="padding: 8px;">426</td><td style="padding: 8px;">287</td><td style="padding: 8px;">181</td><td style="padding: 8px;">46.29%</td><td style="padding: 8px;">49.30%</td><td style="padding: 8px;">72.82%</td></tr>
    <tr><td style="padding: 8px; text-align: left;">GN3</td><td style="padding: 8px;">135</td><td style="padding: 8px;">296</td><td style="padding: 8px;">0</td><td style="padding: 8px;">0</td><td style="padding: 8px;">135</td><td style="padding: 8px;">135</td><td style="padding: 8px;">161</td><td style="padding: 8px;">54.39%</td><td style="padding: 8px;">100.00%</td><td style="padding: 8px;">100.00%</td></tr>
    <tr><td style="padding: 8px; text-align: left;">NEO</td><td style="padding: 8px;">266</td><td style="padding: 8px;">342</td><td style="padding: 8px;">248</td><td style="padding: 8px;">73</td><td style="padding: 8px;">514</td><td style="padding: 8px;">302</td><td style="padding: 8px;">76</td><td style="padding: 8px;">22.22%</td><td style="padding: 8px;">51.75%</td><td style="padding: 8px;">75.83%</td></tr>
  </tbody>
</table>
</div>

And in diagrams

<div class="img-box">
  <div>
  
  ![Color Distribution]({{ '/_includes/assets/2026-07-25/color-chart.svg' | url }})
  
  </div>
  <div>
  
  ![Collected Sets]({{ '/_includes/assets/2026-07-25/sets-chart.svg' | url }})
  
  </div>
</div>

</details>

> A brief note here from my side. If you look at the set stats you can see the reason why I stopped buying boosters and cards in general. `RVR` was **the** set I planned to collect a master set of, meaning every individual card. After the second booster display, which each contains 512 cards, I still managed to only collect 63.24% of all cards. Please be aware that a single one gives you already around 50-60% (see `INR` and `DSK`). So every additional set gives me ~10-20% to my collection, if I'm lucky and don't get the same seeded box. That would converge to $n \in [5, \infty)$ if the RNG gods hate me. On top of that they release totally ridiculous serialized versions of cards that get sold for 3-4 digit prices. Not fun, if you ask me.

Regardless of the current state of WOTC or MTG in general with their Beyond Universe and ridiculous printing approach, I had a big set of cards that I wanted to make use of. (_You see I'm slightly opinionated about this topic_)

To demonstrate the feature I built for this task I planned to create a small application to manage my collection, tracking prices for individual cards and allowing to build decks using the semantic search feature.

For this I indexed the full set of cards from `https://api.scryfall.com/bulk-data/all_cards` on the company's platform.

This allowed a really quick and easy way to get the first prototype or demo out, it's relict resides under [philsupertramp.github.io/manamatrix](https://philsupertramp.github.io/manamatrix), but the backend has been shut down, so the search won't work anymore.

The setup for semantic search was simple, I just forwarded search queries and the service responded with matching cards.

![Simple Application Diagram]({{ '/_includes/assets/2026-07-25/v1-diagram.png' | url }})

The application took care of applying filters and sorting the search results.
The whole app was vibe coded with HuggingFace's [deep-site](https://deepsite.hf.co/) within minutes. Indexing took a little due to the fact that MTG contains at the time of writing more than 37.8k individual cards and ~550k individual artworks. This is a _nice_ data problem.


<details>

<summary>See Screenshots</summary>

![Companion App Landing Page]({{ '/_includes/assets/2026-07-25/companion-full-0.png' | url }})
![Companion App Search]({{ '/_includes/assets/2026-07-25/companion-full-1.png' | url }})

</details>

Regardless, version 2.0 as the page calls it uses a very "off-the-shelf" solution by literally taking [`BAAI/bge-m3`](https://hf.co/BAAI/bge-m3) off the shelf and running it as embedding model as is without any tweaking.

Surprisingly, this worked quite well, until I attempted to build my first deck.
The search quality plummeted under real life queries.
Searching for cherry-picked card names and effects was nice for demo purpose, but it ain't working.

The obvious conclusion was to go the extra mile and train or fine-tune one of these embedding models to achieve the performance that I desire. And while we're at it, let's aim our hit so low that you could run this bad boy (the model) on a smart watch or toaster. `*slaps on rooftop of car*`

But what's an embedding model, how does this "semantic search" work anyway and what is even the difference to other searches?

I will give brief answers to all these questions today with my example and hope to demystify this topic a little and enable the reader to go out and train their own embedding model for their task.

## Demystifying Semantic Search (Briefly)

This will not be yet another deep dive into semantic search, embedding models, and metric learning. If those terms are entirely new to you, I highly recommend pausing here to look them up—there are countless great resources out there—and coming back once you have a basic grasp of the concepts. 

What you essentially need to know is that machine learning algorithms all work with numerical data, they can not understand text, audio or images like we humans do.
To overcome this problem we can use smart techniques and algorithms to transform this non-numerical data into the right representation.
For instance, we can use specific machine learning algorithms, so called embedding models, to transform data into a vector representation. We can then use these vectors to search for similar data points using simple linear algebra.

Because there are many different algorithms and models there are also plenty different ways to measure the performance of these models. The MTEB ([Massive Text Embedding Benchmark](https://huggingface.co/papers/2210.07316)) is the gold standard for comparing the performance of embedding models across all kinds of text data. 

> MTEB spans 8 embedding tasks covering a total of 58 datasets and 112 languages.

That’s fantastic if you want to understand a model's capabilities in a versatile, general-purpose setting. But in our context, we have a single language (English), a single domain (Magic: The Gathering), and a highly fixed structural syntax. 

Compared to the massive models that top this benchmark, we don't need a Jack-of-all-trades. We need a laser-focused specialist.

In order to be able to understand how well a model performs on **our** task, we are building our own benchmark ([`philipp-zettl/mtg-retrieval-benchmark`](https://huggingface.co/datasets/philipp-zettl/mtg-retrieval-benchmark)).

## The Language of Magic: Where Generic Models Fail
After realising that `BAAI/bge-m3` isn't the best solution I went out and started looking for other _good_ embedding models.
One of the first candidates was the default [`sentence-transformers/all-MiniLM-L6-v2`](https://hf.co/sentence-transformers/all-MiniLM-L6-v2).
I plugged it in, indexed the data and triggered the first few queries from the demos.

My thoughts:
> _Nothing changed..._

What a great value. Obviously, this isn't measurable. We needed some metric, something tangible to actually compare those two models.

Which is the reason I built `mtg-retrieval-benchmark`.
It measures four different metrics at different ranks, i.e. the amount of relevant documents to consider.

The encoding of these names is simply `METRIC@RANK` where `RANK` is the amount of samples we consider to be ok.
The `MAP@100` is a ranking quality metric used in information retrieval and recommender systems that calculates the average precision of a model's top 100 retrieved results. It measures both whether relevant items are found and whether they are ranked near the top.

The other metrics are
- NDCG@10 (Normalized Discounted Cumulative Gain at rank 10)
- MRR@10 (Mean Reciprocal Rank at rank 10)
- Recall@10 (proportion of all relevant items captured at rank 10)

And here's how we measure it.

### Benchmark Implementation
The implementation for this task is quite simple.
We fetch the dataset, keep only unique cards, put them into a nice structure, then for every model we index them, create a set of test examples and evaluate them to compute each of our metrics.

```python
def fetch_scryfall_corpus():
    """Fetches the latest MTG Oracle Cards from Scryfall and caches them locally."""
    cache_file = "scryfall_oracle_cards.json"
    
    if os.path.exists(cache_file):
        print(f"Loading MTG corpus from local cache ({cache_file})...")
        with open(cache_file, "r", encoding="utf-8") as f:
            cards = json.load(f)
    else:
        print("Fetching latest MTG Oracle Cards from Scryfall API...")
        metadata = requests.get("https://api.scryfall.com/bulk-data/all-cards", headers={'user-agent': 'card-labeler/v1'}).json()
        cards = requests.get(metadata["download_uri"], headers={'user-agent': 'card-labeler/v1'}).json()
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cards, f)
            
    corpus = {}
    name_to_id = {}
    
    for card in cards:
        # We only care about cards with rules text
        if "oracle_text" in card and card["oracle_text"]:
            card_id = card["id"]
            # Structure the text for maximum semantic context
            doc_text = (
                f'Title: {card.get("name")}\n'
                + (f'Cost: {card.get("mana_cost")}\n' if card.get("mana_cost") else '')
                + (f'Colors: {card.get("colors")}\n' if card.get("colors") else '')
                + f'Type: {card.get("type_line")}\n'
                + f'Desc: {card.get("oracle_text")}'
            )
            corpus[card_id] = doc_text
            name_to_id[card["name"].lower()] = card_id
            
    return corpus, name_to_id

```

The benchmark samples are curated out of direct string matches within the cards corpus
```python
benchmark_queries = {
    "exile all creatures": "exile all creatures",
    "deal 3 damage to any target": "deal 3 damage to any target",
    "destroy target artifact or enchantment": "destroy target artifact or enchantment",
    "search your library for a basic land": "search your library for a basic land",
    "creatures you control get +1/+1": "creatures you control get +1/+1",
    "counter target noncreature spell": "counter target noncreature spell",
    "destroy all lands": "destroy all lands",
    "take an extra turn": "take an extra turn",
    "destroy target planeswalker": "destroy target planeswalker",
    "murder": "Murder",
    "massacre girl": "Massacre Girl"
}
# Dynamically build standard IR mappings based on the Scryfall UUIDs
queries = {}
relevant_docs = {}

for i, (query_text, search_substring) in tqdm(enumerate(benchmark_queries.items()), total=len(benchmark_queries), desc='Creating corpus'):
    q_id = f"q{i}"
    queries[q_id] = query_text
    relevant_docs[q_id] = set()
    
    # Dynamically find ALL cards in the corpus that actually satisfy this query
    for card_id, doc_text in corpus.items():
        if search_substring.lower() in doc_text.lower():
            relevant_docs[q_id].add(card_id)
            
    if len(relevant_docs[q_id]) == 0:
        print(f"⚠️ Warning: Query '{query_text}' matched 0 cards in the corpus.")
```
And then essentially evaulate our models using the `sentence-transformers` library
```python
results_data = []
MODELS_TO_EVALUATE = [
    'BAAI/bge-m3',
    'sentence-transformers/all-MiniLM-L6-v2'
]

for model_id in MODELS_TO_EVALUATE:
    print("-" * 50)
    print(f"Loading and evaluating: {model_id}...")
    try:
        model = SentenceTransformer(model_id)
        model_out_path = os.path.join(OUTPUT_DIR, model_id.replace("/", "_"))
        
        # The evaluator saves a CSV to the specified path
        model.evaluate(evaluator, output_path=model_out_path)
        
        # Extract metrics from the generated CSV
        csv_file = os.path.join(model_out_path, "Information-Retrieval_evaluation_mtg-scryfall-benchmark_results.csv")
        with open(csv_file, newline='') as f:
            reader = list(csv.DictReader(f))
            latest = reader[-1]
            
            results_data.append({
                "Model": model_id,
                "NDCG@10": float(latest.get('cosine-NDCG@10', 0)),
                "MRR@10": float(latest.get('cosine-MRR@10', 0)),
                "MAP@100": float(latest.get('cosine-MAP@100', 0)),
                "Recall@10": float(latest.get('cosine-Recall@10', 0))
            })
        print(f"✅ Finished {model_id}")
    except Exception as e:
        print(f"❌ Failed to evaluate {model_id}: {e}")
```

### Off-The-Shelf Benchmark Results
Our two models performed with the following metrics, one thing to note here is that `bge-m3` (527M Params) is significantly larger than `all-MiniLM-L6-v2` (22.7M Params) and hence requires more resources, especially indexing all cards takes noticably longer.

| Model                                  | NDCG@10              | MRR@10             | MAP@100           | Recall@10       |
| :-------:                              | :------------------: | :----------------: | :---------------: | :-------------: |
| BAAI/bge-m3                            | 0.4664               | 0.4646             | 0.5165            | 0.0195          |
| sentence-transformers/all-MiniLM-L6-v2 | 0.3820               | 0.4091             | 0.4396            | 0.0161          |

While `bge-m3` slightly edges out `all-MiniLM-L6-v2`, both models show remarkably low Recall@10 (~1.9% and ~1.6%). This clearly illustrates the wall general-purpose MTEB models hit when confronted with domain-specific domain terminology and card text. To fix this, we need to fine-tune our own model.

## Forging the Custom Model
When people hear "I trained my own embedding model," they often picture complex loss functions written from scratch, thousands of lines of PyTorch boilerplate, and melted GPUs. 

The reality was far simpler. 

Since we already built a solid corpus from Scryfall and established our benchmark evaluation pipeline using `sentence-transformers`, fine-tuning was mostly a matter of pointing the library at our MTG data and replacing the evaluation loop with a training call.
### Training Implementation
To prepare the data we also recycle the structure, but we add some samples for variety reasons
```python
def generate_training_pairs(cards):
    """
    Creates (query, document) pairs for Multiple Negatives Ranking Loss.
    We synthesize queries from different aspects of the card to simulate user searches.
    """
    train_examples = []
    
    for card in cards:
        if "oracle_text" not in card or not card["oracle_text"]:
            continue
            
        # 1. The exact document format we use in production/evaluation
        doc_text = (
            f'Title: {card.get("name", "")}\n'
            + (f'Cost: {card.get("mana_cost")}\n' if card.get("mana_cost") else '')
            + (f'Colors: {", ".join(card.get("colors", []))}\n' if card.get("colors") else '')
            + f'Type: {card.get("type_line", "")}\n'
            + f'Desc: {card.get("oracle_text", "")}'
        )
        
        # 2. Synthesize Queries (Positive Pairs)
        
        # Query Type A: Exact or partial card name
        train_examples.append(InputExample(texts=[card["name"].lower(), doc_text]))
        
        # Query Type B: Type line queries (e.g. "Legendary Creature - Goblin")
        if card.get("type_line"):
            train_examples.append(InputExample(texts=[card["type_line"].lower(), doc_text]))
            
        # Query Type C: Sentences from the Oracle text
        # This teaches the model to map specific mechanic queries to the whole card
        sentences = [s.strip() for s in card["oracle_text"].split('.') if len(s.strip()) > 10]
        for sentence in sentences:
            # Add a bit of natural variation
            query = sentence.replace("~", card["name"]).lower()
            train_examples.append(InputExample(texts=[query, doc_text]))

    # Shuffle to ensure diverse batches
    random.shuffle(train_examples)
    return train_examples
```
The rest boils down to the "training loop", which is simply
```python
model = SentenceTransformer(MODEL_NAME)

# OPTIMIZATION 1: Limit Sequence Length
# Transformer VRAM usage scales quadratically with sequence length.
# Magic cards are dense but short; 256 tokens is more than enough for almost any card.
model.max_seq_length = 256

print("Preparing training dataset...")
cards = fetch_training_data()
train_examples = generate_training_pairs(cards)
print(f"Generated {len(train_examples)} (query, document) training pairs.")

# DataLoader feeds the pairs to the model
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=BATCH_SIZE)

# Multiple Negatives Ranking Loss:
# Requires pairs of (query, document). 
# It assumes that for a given query, its paired document is positive, 
# and ALL other documents in the same batch are negatives.
train_loss = losses.MultipleNegativesRankingLoss(model=model)

print("Starting training (this might take a while depending on GPU)...")
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=EPOCHS,
    warmup_steps=1000,
    use_amp=True, # OPTIMIZATION 2: Automatic Mixed Precision (saves ~50% VRAM, trains faster)
    show_progress_bar=True,
    output_path=OUTPUT_PATH,
    save_best_model=True,
)
```
Due to limitations with hardware I chose smaller models and didn't train `bge-m3`, I bet it would excel even on this benchmark!

### Fine-Tuned Benchmark Results
Once the models were trained I ran the benchmark against them which resulted in a overall table of

<iframe
  src="https://huggingface.co/datasets/philipp-zettl/mtg-retrieval-benchmark/embed/viewer/default/train"
  frameborder="0"
  width="100%"
  height="560px"
></iframe>

My personal winner here is `bge-micro-v4-mtg-v2` with ~17.4M parameters the smallest model in the set and only performing slightly worse on MAP@100, compared to the overall winner `all-MiniLM-L6-v2-mtg-v2` (22.7M parameters). Oh yea, and don't forget that `bge-micro-v4-mtg-v2` is totally crushing it compared to 'ol `bge-m3`.

## Bringing v1 to Life
Now that I had a model that actually understood the language of Magic, it was time to move past the prototype phase and deploy a proper v1. 

The goal was complete self-reliance. No more shut-down backend services or reliance on external embedding APIs. I packaged the custom `bge-micro-v4-mtg-v2` model into a lightweight inference service and deployed it entirely locally within my own k3s Kubernetes cluster. 

To give it a solid data foundation, I used Helm charts to deploy a persistent Postgres instance directly inside the cluster, handling all the card data, pricing history, and the vector embeddings themselves. 

Because the custom model is so small (~17M parameters), the RAM footprint for the inference service is practically nonexistent compared to running an off-the-shelf LLM. It's fast, incredibly accurate, and completely under my control.

![New Application Architecture]({{ '/_includes/assets/2026-07-25/v1.0-diagram.png' | url }})

To be fully independent, I switched from the client-only implementation to the full-stack approach, including DevOps lol.
This bad boy is running now on a `k3s` cluster in my home lab that is orchestrated by a Raspberry Pi 5 (8GB), as a worker node for this application I'm running an old x240 in headless mode, because it has a broken display.

The apps run under `https://mtg.local.godesteem.de` and `https://mox-lotus.local.godesteem.de` with letsencrypt cert issuing under my domain namespace `*.local.godesteem.de` for the local cluster.

I comically called the backend `mox-lotus` and the frontend `black-opal`, after Black Lotus and Mox Opal, but I will spare you the implementation details. Eventually, you will be able to find them on my github profile.

The query process looks something like this

![Semantic Search Application]({{ '/_includes/assets/2026-07-25/semantic-search-diagram.png' | url }})

The frontend now is only to display data, filtering and sorting happens on the backend.

To keep the data set up-to-date we have two k8s `CronJob`s running. One is fetching for new cards on Scryfall, the other one is indexing un-indexed cards into qdrant.

### What's Next?
ManaMatrix v1 is officially deprecated, `mox-lotus` and `black-opal` are live in my home lab, and building decks finally feels intuitive. The search understands that if I type "creatures you control get +1/+1", I'm looking for anthem effects, not just exact string matches.

There is a lot more to cover, specifically the intricacies of configuring the persistent Postgres instance and the Helm charts for the k3s cluster, but I will save those infrastructure details for a dedicated follow-up post.

For now, if you are wrestling with generic search results on specialized data: stop fighting the big models, curate your domain data, and train a micro-model.

<details>
<summary>Here are a bunch of screenshots at the end</summary>

<div class="gallery-grid">
  <div>
    <img src="{{ '/_includes/assets/2026-07-25/companion-full-v1.0-0.png' | url }}" alt="Landing Page">
    <p><em>Landing Page</em></p>
  </div>
  <div>
    <img src="{{ '/_includes/assets/2026-07-25/companion-full-v1.0-search-0.png' | url }}" alt="Search Interface">
    <p><em>Search Interface</em></p>
  </div>
  <div>
    <img src="{{ '/_includes/assets/2026-07-25/companion-full-v1.0-collections-0.png' | url }}" alt="Collections Overview">
    <p><em>Collections Overview</em></p>
  </div>
  <div>
    <img src="{{ '/_includes/assets/2026-07-25/companion-full-v1.0-collection-0.png' | url }}" alt="Collection Detail">
    <p><em>Collection Detail</em></p>
  </div>
  <div>
    <img src="{{ '/_includes/assets/2026-07-25/companion-full-v1.0-card-0.png' | url }}" alt="Card Detail">
    <p><em>Card Detail</em></p>
  </div>
  <div>
    <img src="{{ '/_includes/assets/2026-07-25/companion-full-v1.0-login-0.png' | url }}" alt="Login">
    <p><em>Login</em></p>
  </div>
</div>


</details>

## Conclusion
The app is already a rock solid v1.0 release. Like I said it's running flawlessly in my infrastructure and it takes around 1.5h to index the full set of current cards.

I am aware of some pitfalls of my quickly sketched API design, which need to be fixed soon once we have more price data points.
The import cron is turned off until this is resolved.

Apart from this I'm not 100% happy with the search results for non-keyword features of cards, like "Landfall". Only using the standard starting line of `Landfall -- Whenever a land enters` we get the relevant cards.
This can be fixed through more work on the pre-processing of cards. But that's for v3 of the model line.

In case you're wondering what `-v1` of the models were, I had a bug in the pre-processing pipeline and the fact we were trying to build similarity with image URLs that resulted in terrible performance, that doesn't need to be mentioned =D
