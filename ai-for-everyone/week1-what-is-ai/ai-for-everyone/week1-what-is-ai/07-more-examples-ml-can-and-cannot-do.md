---
title: AI for Everyone — Week 1: More Examples of What ML Can and Cannot Do
url: https://www.coursera.org/learn/ai-for-everyone/home/week/1
category: tutorial
source: DeepLearning.AI - AI for Everyone
tags: AI, Andrew Ng, machine learning, examples, feasibility
---
author: Andrew Ng

# Week 1 — More Examples of What Machine Learning Can and Cannot Do

> Course: **AI for Everyone** by Andrew Ng (DeepLearning.AI / Coursera)
> Week: **1 — What Is AI** · Lesson: **More examples of what machine learning can and cannot do**
> Study notes (original summary, not verbatim transcript).

## Core Idea
A series of concrete examples that sharpen the judgment about which tasks are feasible for ML — reinforcing the principle that tasks learnable "in a second" with enough data are candidates, while reasoning-heavy tasks are not.

## Key Points
- **More "can do" examples**:
  - Recognizing whether a chest X-ray shows pneumonia (with a large labeled dataset).
  - **Self-driving perception**: image + radar/lidar → positions of other cars (lots of data + good algorithms).
  - Detecting defects in manufacturing (images of good vs. defective parts).
  - Classifying news articles into categories.
  - Predicting a user's next purchase or likelihood of churn from historical records.
- **More "cannot easily do" examples**:
  - **Self-driving**: a video of a human gesturing → the person's *intention* (stop / go / turn). The variety of gestures is enormous, data is hard to collect, and it is safety-critical.
  - Diagnosing pneumonia from ~10 textbook images + a few paragraphs (too little data, unclear A/B).
  - Determining whether a loan should be approved **and explaining all the reasons** (explainability is hard).
  - Deciding whether a person is a good fit for a job — a task humans don't reliably do in 1 second and where the "label" is noisy.
  - Analyzing cause-and-effect (e.g., "did this ad cause the sale?").
  - Predicting complex, long-horizon outcomes that depend on many unobserved factors.
- **The unifying lens (feasibility rule)**: ML works well with a **simple concept + lots of data** (for both A and B); it works poorly with a **complex concept and/or small data**.
- **A key under-appreciated weakness — poor generalization**: an AI trained on high-quality X-rays performs poorly on X-rays from a **different hospital** (angled patients, artifacts). Humans adapt to new data much better than AI; AI is far less robust to new data distributions.
- **The boundary is genuinely fuzzy**: even experienced practitioners need weeks of technical diligence to judge feasibility.

## Takeaways
- Practice classifying candidate projects as "ML-feasible" vs. "not yet."
- Beware **explainability and causality** — two areas where ML is often over-sold.
- A realistic screen of many examples sharpens your instinct for what to green-light.
