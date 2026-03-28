# 🛡️ Aegis-Risk

### AI-Powered Supply Chain Risk Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![OpenAI](https://img.shields.io/badge/AI-OpenAI-black)
![ChromaDB](https://img.shields.io/badge/VectorDB-Chroma-orange)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## 🚀 Overview

**Aegis-Risk** is an end-to-end AI system that monitors global news, detects geopolitical risk signals, and explains their impact on supply chains using AI.

It combines:

- Multi-source news ingestion
- Risk scoring
- Vector search (RAG)
- AI-generated structured insights
- Interactive dashboard

---

## 🎯 Project Goal

To answer:

> **How can AI continuously monitor global news and explain supply-chain risk in real time?**

This system transforms raw news into:

- Risk scores
- Actionable insights
- AI explanations

---

## ✨ Key Features

- 🔄 Multi-source news ingestion
  - NewsAPI
  - BBC RSS
  - Al Jazeera parsing

- 🧠 Risk scoring engine (NLP + rules)

- 🔍 Semantic search (ChromaDB)

- 🤖 AI-powered explanations
  - Risk level
  - Key drivers
  - Watchpoints

- 📊 Interactive dashboard
  - Charts
  - Alerts
  - Risk breakdown

- 📚 Source-backed answers (RAG)

---

## 🧠 System Architecture

```mermaid
flowchart TD

A[User / Streamlit Dashboard] --> B[FastAPI Backend API]

B --> C1[NewsAPI]
B --> C2[BBC RSS]
B --> C3[Al Jazeera Parsing]

C1 --> D[Normalization]
C2 --> D
C3 --> D

D --> E[Deduplication + Filtering]
E --> F[Risk Scoring Engine]

F --> G[(SQLite DB)]
F --> H[(ChromaDB)]

H --> I[Semantic Search]
I --> J[OpenAI LLM]

J --> K[AI Risk Insights]

G --> L[Charts + Metrics]
K --> B
L --> B

B --> M[Dashboard UI]
M --> A
```
