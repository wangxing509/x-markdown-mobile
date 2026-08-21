---
title: AI for Everyone — Week 3: Case Study: Smart Speaker
url: https://www.coursera.org/learn/ai-for-everyone/home/week/3
category: tutorial
source: DeepLearning.AI - AI for Everyone
tags: AI, Andrew Ng, smart speaker, pipeline, case study
---
author: Andrew Ng

# Week 3 — Case Study: Smart Speaker

> Course: **AI for Everyone** by Andrew Ng (DeepLearning.AI / Coursera)
> Week: **3 — Building AI in Your Company** · Lesson: **Case study: Smart speaker**
> Study notes (original summary, not verbatim transcript).

## Core Idea
A smart speaker (like Amazon Echo) illustrates how a seemingly simple product is actually a **pipeline of several AI components** working together — and how an "AI product" is often really several A→B tasks chained.

## Key Points
- **The 4-step AI pipeline** of a smart speaker:
  1. **Trigger word detection** — wake the device when it hears its name ("Alexa").
  2. **Speech recognition** — transcribe the spoken words to text.
  3. **Intent recognition** — figure out what the user wants (play music, set alarm, order item).
  4. **Command execution** — call the service / take the action.
- **Each step is its own A→B learning task**, trained with its own labeled data (audio → "wake/no wake"; audio → text; text → intent).
- **Why this matters**: product design becomes "chain the right models together" — the user just sees one seamless assistant.
- **Data flywheel in action**: users' voice commands and corrections generate data that improves the models over time.
- **User behavior is part of the system**: successful voice assistants also require users to speak in ways the system understands — a human+AI collaboration.

## Takeaways
- Real AI products are often **pipelines of multiple ML components**, not one model.
- Break a product into chained A→B tasks, each with its own data.
- The data flywheel continuously improves the whole pipeline.
