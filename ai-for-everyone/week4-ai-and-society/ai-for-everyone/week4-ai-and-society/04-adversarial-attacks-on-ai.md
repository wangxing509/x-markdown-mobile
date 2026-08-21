---
title: AI for Everyone — Week 4: Adversarial Attacks on AI
url: https://www.coursera.org/learn/ai-for-everyone/home/week/4
category: tutorial
source: DeepLearning.AI - AI for Everyone
tags: AI, Andrew Ng, adversarial attacks, security, robustness
---
author: Andrew Ng

# Week 4 — Adversarial Attacks on AI

> Course: **AI for Everyone** by Andrew Ng (DeepLearning.AI / Coursera)
> Week: **4 — AI & Society** · Lesson: **Adversarial attacks on AI**
> Study notes (original summary, not verbatim transcript).

## Core Idea
AI systems can be fooled by **small, deliberate perturbations** to their inputs that humans don't notice — a real and under-appreciated security weakness.

## Key Points
- **What an adversarial attack is**: making tiny, often imperceptible changes to an input so that a model confidently misclassifies it.
- **Examples**:
  - Adding subtle noise to an image so a model sees a **dog instead of a cat** (looks identical to a human).
  - Placing a **sticker on a stop sign** so a self-driving car fails to detect it (a safety-critical concern).
  - Subtly modifying an audio clip so a voice system "hears" **"Yes, authorized"** when the speaker actually said **"No, reject."**
- **Why it matters**: in safety-critical or high-stakes uses (self-driving, security, banking voice systems), an attacker could exploit these weaknesses.
- **Ongoing defense — an arms race**: research into **robustness** (training models to resist perturbations) is active, but defenses often have costs, and the contest between attackers and defenders can become a continuous **arms race**; adversarial inputs remain an open challenge.
- **Important distinction (vs. next lesson)**: adversarial attacks target the *input* to fool a model; **adverse uses** are about using AI *for harm* (like deepfakes). Both are security concerns but they are different.

## Takeaways
- Models can be fooled by subtle, human-invisible input changes.
- Treat adversarial robustness as a security consideration for consequential AI.
- Don't confuse "fooling the model" (attack) with "using AI to harm" (adverse use).
