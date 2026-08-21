---
title: AI for Everyone — Week 1: What is Data?
url: https://www.coursera.org/learn/ai-for-everyone/home/week/1
category: tutorial
source: DeepLearning.AI - AI for Everyone
tags: AI, Andrew Ng, data, machine learning, AI project
---
author: Andrew Ng

# Week 1 — What is Data?

> Course: **AI for Everyone** by Andrew Ng (DeepLearning.AI / Coursera)
> Week: **1 — What Is AI** · Lesson: **What is data?**
> Study notes (original summary, not verbatim transcript).

## Core Idea
Data is the "fuel" of modern AI. Not all data is equally valuable: the most valuable data is that which powers a specific A→B learning task. Good data is often more important than having an enormous quantity of it.

## Key Points
- **Data has value only in service of a task**: A large random dataset is worth little if it doesn't help a specific AI system (e.g., a million random photos don't help a system that needs labeled images of a specific product line).
- **You decide what is A and what is B**: given a dataset, the business case determines the mapping — e.g., size → price to price a house, vs. budget → size to pick a house. The same data can serve different tasks.
- **How data is acquired**:
  - **Manual labeling** — people label examples by hand.
  - **Observing behavior** — e.g., users' purchase history, or machine sensors (temperature/pressure).
  - **Downloading or partnering** — obtaining existing datasets from vendors or partners.
- **Two common misuses**:
  - "Collect data for 3 years first" — usually wrong; feed the AI team early so it guides what to collect.
  - "I have lots of data, so AI will make it valuable" — not guaranteed; raw volume isn't value.
- **Garbage in, garbage out**: real data is messy — wrong labels, missing values — so cleaning and labeling quality matter.
- **Structured vs. unstructured data**: structured data is spreadsheets/tables; unstructured data is images, audio, text. Supervised learning works on both.
- **Quality > quantity**: For supervised learning, **labeling** matters enormously. A smaller set of well-labeled, relevant examples often beats a huge set of messy data.

## Takeaways
- Before buying/collecting huge data, ask what specific A→B task it will support.
- Investing in **clean, labeled, task-relevant data** is usually a better bet than chasing raw volume.
