---
title: AI for Everyone — Week 4: Discrimination and Bias
url: https://www.coursera.org/learn/ai-for-everyone/home/week/4
category: tutorial
source: DeepLearning.AI - AI for Everyone
tags: AI, Andrew Ng, bias, discrimination, ethics, fairness
---
author: Andrew Ng

# Week 4 — Discrimination and Bias

> Course: **AI for Everyone** by Andrew Ng (DeepLearning.AI / Coursera)
> Week: **4 — AI & Society** · Lesson: **Discrimination / Bias**
> Study notes (original summary, not verbatim transcript).

## Core Idea
AI systems can reflect and amplify the **bias present in their training data**. Because bias enters through data and design choices, it can be mitigated — but only if it is addressed deliberately.

## Key Points
- **Where bias comes from**: biased, unrepresentative, or historically biased **training data** and labeling. The model simply learns the patterns in the data, including unfair ones.
- **Illustrative examples**:
  - **Word analogies**: a model trained on text can learn biased associations like *man → programmer :: woman → homemaker* (the fairer answer would be *woman → programmer*), even while neutral analogies like *king → queen* work fine.
  - **Hiring tools**: an AI recruiting system trained on a company's past hiring decisions can replicate (even worsen) its historical discrimination — one such system was so biased against women it was shut down.
  - **Facial recognition**: systems trained mostly on light-skinned faces recognize light-skinned people more accurately than dark-skinned people — a serious fairness problem in contexts like criminal investigation.
- **Why bias is dangerous**: it can scale an unfairness to millions of decisions (hiring, lending, policing, healthcare), sometimes in ways that are hard to see.
- **Mitigation approaches**:
  - Use **inclusive, representative training data**.
  - **"Zero out" / de-bias** specific attributes or associations.
  - **Audit** models systematically for disparate impact on subgroups.
  - Build **diverse teams** to surface and fix biases.
  - Note: an **adversarial attack is NOT a bias-mitigation technique** — a common conceptual confusion.
- **Practical message**: bias is a solvable engineering and governance problem when teams are aware of it and committed to fairness metrics.

## Takeaways
- Bias enters via **training data and design**; it is not inherent magic.
- Fairness requires **diverse data, de-biasing, auditing, and diverse teams**.
- Leaders should insist on bias checks before deploying consequential AI.
