---
title: AI for Everyone — Week 1: What Machine Learning Can and Cannot Do
url: https://www.coursera.org/learn/ai-for-everyone/home/week/1
category: tutorial
source: DeepLearning.AI - AI for Everyone
tags: AI, Andrew Ng, machine learning, capabilities, limits
---
author: Andrew Ng

# Week 1 — What Machine Learning Can and Cannot Do

> Course: **AI for Everyone** by Andrew Ng (DeepLearning.AI / Coursera)
> Week: **1 — What Is AI** · Lesson: **What machine learning can and cannot do**
> Study notes (original summary, not verbatim transcript).

## Core Idea
ML can do some things remarkably well and others not at all. Having a **realistic view of both success and failure cases** prevents over-investing in infeasible projects.

## Key Points
- **Do technical diligence first**: inspect the actual input **A** and output **B** of the candidate task before committing — media and research rarely report failures, so realistic diligence is essential.
- **What ML CAN do** (things humans can do in ~1 second of thought, with enough labeled data):
  - Recognize objects in images (cat/dog, defects, faces).
  - Transcribe speech and translate text.
  - Detect spam / fraud / anomalies.
  - **Route customer emails** to categories (refund / shipping / other).
  - Predict click-through, sales, or demand from structured data.
  - The rule of thumb: **if a person can do the task in under ~1 second of mental effort, an ML system can likely be trained to do it** (given enough data).
- **What ML CANNOT easily do**:
  - Tasks that require long chains of reasoning or common sense.
  - **Generating an empathetic 2–3 paragraph reply** to a customer — with even ~1,000 examples it may just echo "Thank you for your email," or produce gibberish.
  - Tasks that need rich understanding of context or prior experience.
  - Problems where you lack enough **labeled data**.
  - Tasks that require reasoning about cause-and-effect, not just correlation.
- **Feasibility rule of thumb**: ML works when the concept is **simple + you have lots of data for both A and B**; it struggles with **complex concepts and/or small data**.
- **Data-hungry**: supervised learning typically needs many labeled examples; performance improves with more data, but hitting high accuracy is hard for "long-thought" tasks.
- **"AI winter" effect**: when people oversell AI and projects fail, investment dries up; realistic expectations sustain steady progress.

## Takeaways
- Use the **"1-second rule"** as a quick feasibility screen for a candidate ML task.
- ML is excellent at narrow, pattern-based tasks; weak at broad reasoning and tasks needing lots of context.
- Frame projects around what is genuinely learnable, not what is fashionable.
