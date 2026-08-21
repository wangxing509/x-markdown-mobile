---
title: AI for Everyone — Week 3: Case Study: Self-driving Car
url: https://www.coursera.org/learn/ai-for-everyone/home/week/3
category: tutorial
source: DeepLearning.AI - AI for Everyone
tags: AI, Andrew Ng, self-driving, pipeline, safety, case study
---
author: Andrew Ng

# Week 3 — Case Study: Self-driving Car

> Course: **AI for Everyone** by Andrew Ng (DeepLearning.AI / Coursera)
> Week: **3 — Building AI in Your Company** · Lesson: **Case study: Self-driving car**
> Study notes (original summary, not verbatim transcript).

## Core Idea
The self-driving car is the ultimate example of a **complex AI pipeline** with many perception components plus a **planning/control** stage, and it highlights how **safety and edge cases** dominate engineering effort.

## Key Points
- **Perception components** (each an **object-detection** ML task):
  - **Car detection** — identify other vehicles in camera/radar/sensor inputs.
  - **Pedestrian detection** — locate people.
  - Optionally lane detection, sign recognition, etc.
- **Planning & control**:
  - **Motion planning** — choose a safe path/trajectory.
  - **Steering / acceleration / braking** — execute the plan.
- **A system of A→B building blocks**: the car combines several ML models (car detection, pedestrian detection, planning) that feed into each other; each block can be developed and validated separately. "AI product" here means a *system* where ML is only part of the solution.
- **Key lesson — the "last 10%" problem**: getting the pipeline to work most of the time is relatively easy; making it **safely handle rare edge cases** (unusual weather, uncommon objects, ambiguous situations) is extremely hard and is where most effort goes.
- **Safety-driven design**: decisions must be conservative and verifiable; a "close enough" detection can be unacceptable.
- **Data + simulation**: self-driving teams rely on massive real and simulated data to cover edge cases and test rare scenarios safely.

## Takeaways
- Self-driving = **perception (detect cars/pedestrians) + planning (choose path) + control (steer)**, each an ML component.
- The hard, expensive part is **edge-case robustness and safety**, not the basic pipeline.
- Complex AI products are pipelines whose risk concentrates in rare but critical cases.
