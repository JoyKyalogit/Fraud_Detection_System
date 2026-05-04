# Fraud Detection System

A machine learning fraud detection project with:
- `fraud_detection.py` for model training,
- `deploy.py` for FastAPI prediction API,
- `app.py` for Streamlit dashboard UI.

The API combines model scoring with business safety rules and returns a verdict, risk level, and recommendation.

## Live Demo
https://fraud-dashboard-i71m.onrender.com

## Problem It Solves

Financial transactions happen in large volumes, and manual fraud checks are too slow and inconsistent.  
This creates two major risks:
- real fraud can be missed, causing financial loss,
- legitimate transactions can be blocked, hurting customer trust.

## Solution

This project provides a real-time fraud screening workflow:
- a trained ML model estimates fraud probability from transaction features,
- rule-based safety checks catch high-risk patterns,
- the API returns an actionable decision (approve, block, or review),
- a Streamlit dashboard makes results easy to understand and monitor.

## Why It Is Helpful

- Improves response speed by automating first-level fraud checks.
- Supports better decisions with both probability score and risk label.
- Reduces missed fraud through additional business guardrail rules.
- Makes the system practical for demos, learning, and production-style prototypes.

## Quick Setup

```bash
pip install fastapi uvicorn streamlit pydantic pandas numpy scikit-learn sqlalchemy joblib plotly psycopg2-binary xgboost
```

## Train Model

```bash
python fraud_detection.py
```

This creates `fraud_model.pkl` (required by the API).

## Run Project

Start API (Terminal 1):
```bash
python -m uvicorn deploy:app --reload
```

Start dashboard (Terminal 2):
```bash
python -m streamlit run app.py
```

## Endpoints

- `GET /` - service info
- `GET /health` - health check
- `POST /predict` - fraud prediction

## Notes

- Keep `fraud_model.pkl` in the project root.
- Update PostgreSQL connection string in `fraud_detection.py` for your environment.
- Current decision threshold is `0.30`.
