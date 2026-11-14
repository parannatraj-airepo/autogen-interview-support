# 💼 AI Multi-Agent Interview Support System

An interactive mock interview platform built with **Microsoft AutoGen** and **Streamlit**. Upload a candidate's PDF resume to trigger a multi-agent workflow that analyzes the profile, conducts a tailored technical and behavioral interview, evaluates answers in real time, and generates a final scorecard.

---

## 🏗️ Multi-Agent Architecture

The application coordinates three specialized AutoGen `AssistantAgent` instances via a `UserProxyAgent`:

1. **Resume Analyst (`Resume_Analyst`)**
   * Extracts raw text from the uploaded PDF resume.
   * Identifies primary technical/soft skills, gauges overall seniority level, and outlines 3–4 key focus areas for the interview.
2. **Interviewer (`Interviewer`)**
   * Reviews the structured profile summary.
   * Generates 4 targeted questions covering core technical verification, system design/problem solving, practical project experience, and behavioral strategy.
3. **Evaluator (`Evaluator`)**
   * Grades each candidate response on a scale of `0–100` for accuracy, clarity, and completeness.
   * Outputs structured feedback highlighting key strengths and actionable areas for improvement.

---

## ✨ Features

* **PDF Resume Parsing:** Automatic text extraction using `pypdf`.
* **Dynamic Question Generation:** Tailored questions derived directly from candidate experience rather than static question banks.
* **Step-by-Step Interview UI:** Progress tracking, clean response areas, and stateful session management in Streamlit.
* **Comprehensive Scorecard:** Aggregated performance metrics, hire-recommendation verdicts, and expandable question-by-question breakdowns.

---

## 🛠️ Tech Stack

* **Framework:** Microsoft AutoGen (`pyautogen`)
* **Frontend / UI:** Streamlit
* **LLM Provider:** OpenAI (`gpt-4o`)
* **PDF Processing:** `pypdf`

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/autogen-interview-support.git](https://github.com/your-username/autogen-interview-support.git)
cd autogen-interview-support