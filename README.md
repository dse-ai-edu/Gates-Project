# Auto Feedback Generation System - Gates Project

## Overview

This system generates personalized, context-aware feedback for student responses using AI. It combines configurable feedback structures with large language models to provide instructors with an efficient way to deliver consistent, high-quality feedback at scale while accommodating personalized teaching approaches.

## What It Does

The system takes student answers to academic questions and generates tailored feedback based on instructor preferences. Instead of writing feedback manually for each student, instructors define their feedback approach once (style, structure, tone) and then apply it automatically to any number of student responses.

## Input

- Instructor feedback preferences (teaching style, structural templates, pedagogical keywords)
- Student answers (text responses to questions)


## Workflow

1. **Setup**: Instructor configures feedback system (2 steps)
2. **Review**: Preview and adjust configuration settings
3. **Generate**: Submit student answers and receive feedback

Instructors can retrieve previous configurations by entering the transaction ID, enabling consistent feedback across multiple sessions or semesters.

## Installation & Usage

### Requirements
- Python 3.8+
- MongoDB Atlas account
- OpenAI API key(s)

### Configuration

Create a `.env` file in the project root directory with:

```dotenv
MONGODB_URI=mongodb+srv://-xxxxx
OPENAI_API_KEY1=sk-proj-xxxxx
OPENAI_API_KEY2=sk-proj-xxxxx
OPENAI_API_KEY3=sk-proj-xxxxx
```

Additional keys (up to 3 total) are optional for distributing API calls across multiple quotas.

### Running the Application

```bash
python run.py --port 5001
```


## Database Storage

All configurations and feedback are persisted in MongoDB, providing long-term storage and enabling retrieval of previous settings and feedback history.