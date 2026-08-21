---
title: AI for Everyone — Week 2: Workflow of a Machine Learning Project
url: https://www.coursera.org/learn/ai-for-everyone/home/week/2
category: tutorial
source: DeepLearning.AI - AI for Everyone
tags: AI, Andrew Ng, machine learning, workflow, project
---
author: Andrew Ng

# Week 2 — Workflow of a Machine Learning Project

> Course: **AI for Everyone** by Andrew Ng (DeepLearning.AI / Coursera)
> Week: **2 — Building AI Projects** · Lesson: **Workflow of a machine learning project**
> Study notes (original summary, not verbatim transcript).

## Core Idea
An ML project is iterative and team-based. Knowing the standard workflow helps non-technical stakeholders set expectations and manage projects realistically.

## Key Points
- **The core workflow loop** (iterative, not linear):
  1. **Specify the project** — define the A→B task precisely and set a concrete, measurable target (e.g., reduce spam-detection error to X%).
  2. **Collect data** — gather and **label** examples (A,B) for training.
  3. **Train the model** — feed data to the algorithm so it learns the input→output mapping.
  4. **Deploy the model** — put the trained model into a real product/service so it serves users.
  5. **Iterate** — observe performance, collect new data, retrain, and improve continuously.
- **Data is the key ingredient**: the value of an ML system often hinges more on the data than on the algorithm, and the **longest, hardest step is frequently data collection**, not model training.
- **Data labeling is a real, ongoing cost**: high-quality labels drive accuracy; labeling effort is often underestimated.
- **Deploy + monitor**: real-world performance can drift, so ongoing monitoring matters after you ship.
- **Important reality**: this is **not a linear, one-shot process** — you almost always loop back (e.g., collect more data after deployment reveals a gap).

## Takeaways
- The 4-step skeleton (specify → data → train → iterate) is the backbone of every ML project.
- Budget for **iteration and labeling**, not just the first training run.
- A clear, measurable target at step 1 makes the whole process controllable.
