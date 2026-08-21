---
title: AI for Everyone — Week 1: What is Machine Learning?
url: https://www.coursera.org/learn/ai-for-everyone/home/week/1
category: tutorial
source: DeepLearning.AI - AI for Everyone
tags: AI, Andrew Ng, machine learning, supervised learning, supervised learning
---
author: Andrew Ng

# Week 1 — What Is Machine Learning?

> Course: **AI for Everyone** by Andrew Ng (DeepLearning.AI / Coursera)
> Week: **1 — What Is AI** · Lesson: **What is Machine Learning?**
> Study notes (original summary, not verbatim transcript).

## Core Idea
Machine learning (ML) is the technology driving most of today's AI value. The key concept to understand is **learning A to B** (input → output) mapping, dominated by **supervised learning**.

## Key Points
- **Definition in one phrase**: Machine learning is a field that gives computers the ability to **learn from data** rather than being explicitly programmed for every case.
- **The "A to B" mental model**:
  - Every AI task can be thought of as: given input **A**, produce output **B**.
  - Examples: email → spam/not spam; image → cat/dog; audio → transcript; English → Chinese (translation); ad + user → click/won't click (online ads, one of the most lucrative uses); photo → defect? (visual inspection); image + sensor → car positions (self-driving).
- **Supervised learning (most valuable today)**:
  - Learns a mapping from input A to output B using many labeled examples.
  - Requires large amounts of labeled training data.
  - Powers a huge share of the value AI creates in the economy.
- **Why it "took off now"**: neural networks / deep learning keep improving as you feed them **more data + larger networks** (and GPUs), unlike traditional AI methods that plateau. This scaling is why modern ML succeeded.
- **Other categories mentioned**: unsupervised learning (finding structure without labels), and reinforcement learning (learning through rewards) are less central to this course.

## Takeaways
- When thinking about an AI application, first ask: **can it be framed as an A→B input-output task?**
- The A→B framing is the foundation for understanding what ML can and cannot do, and for evaluating AI opportunities in any organization.
