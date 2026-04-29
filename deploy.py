from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import pandas as pd
import numpy as np
import joblib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#  Load model 
try:
    model = joblib.load("fraud_model.pkl")
    logger.info(" Model loaded successfully")
except FileNotFoundError:
    logger.error(" fraud_model.pkl not found!")
    model = None

app = FastAPI(
    title="FraudShield AI API",
    description="Real-time fraud detection powered by ML",
    version="2.0.0"
)

# Allow Streamlit to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#  Input schema 
class Transaction(BaseModel):
    amount: float
    isflaggedfraud: int = 0
    large_txn_flag: int = 0
    high_risk_type_flag: int = 0
    odd_hour_flag: int = 0
    frequent_txn_flag: int = 0
    new_sender_flag: int = 0
    type_cash_out: int = 0
    type_transfer: int = 0
    type_payment: int = 0
    type_cash_in: int = 0
    type_debit: int = 0

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v < 0:
            raise ValueError("Amount must be non-negative")
        return v

# Health check
@app.get("/")
def root():
    return {
        "status": "online",
        "service": "FraudShield AI API",
        "version": "2.0.0",
        "model_loaded": model is not None,
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "model_ready": model is not None}

#  Predict endpoint 
@app.post("/predict")
def predict(txn: Transaction):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Check fraud_model.pkl exists.")

    # Build DataFrame
    df = pd.DataFrame([txn.model_dump()])

    # Log-transform amount (matches training)
    df["amount_log"] = np.log1p(df["amount"])

    # Align features to what the model expects
    expected_features = model.feature_names_in_
    for col in expected_features:
        if col not in df.columns:
            df[col] = 0
    df = df[expected_features]

    # Predict
    model_probability = model.predict_proba(df)[0][1]

    # Threshold: 0.3 = aggressive detection
    THRESHOLD = 0.3
    prediction = 1 if model_probability >= THRESHOLD else 0
    rule_triggered = None

    # Rule-based safety overrides (business guardrails)
    if txn.amount > 10_000_000:
        prediction = 1
        rule_triggered = "HARD_LIMIT_AMOUNT"
    elif txn.amount > 1_000_000 and txn.odd_hour_flag == 1 and txn.new_sender_flag == 1:
        prediction = 1
        rule_triggered = "HIGH_AMOUNT_ODD_HOUR_NEW_SENDER"
    elif txn.isflaggedfraud == 1 and txn.high_risk_type_flag == 1:
        prediction = 1
        rule_triggered = "SYSTEM_FLAG_PLUS_HIGH_RISK_TYPE"

    # Align displayed probability with hard-rule verdicts so UI is consistent.
    # Keep raw model score for transparency in a separate field.
    rule_probability_floor = {
        "HARD_LIMIT_AMOUNT": 0.98,
        "HIGH_AMOUNT_ODD_HOUR_NEW_SENDER": 0.85,
        "SYSTEM_FLAG_PLUS_HIGH_RISK_TYPE": 0.70,
    }
    effective_probability = max(model_probability, rule_probability_floor.get(rule_triggered, 0.0))

    # Risk level
    if effective_probability > 0.7:
        risk_level = "High"
    elif effective_probability > 0.3:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Recommendation
    if prediction == 1:
        if rule_triggered == "HARD_LIMIT_AMOUNT":
            recommendation = "IMMEDIATE BLOCK - Amount exceeds hard safety limit"
        elif rule_triggered == "HIGH_AMOUNT_ODD_HOUR_NEW_SENDER":
            recommendation = "BLOCK & REVIEW - High amount at odd hour from new sender"
        elif rule_triggered == "SYSTEM_FLAG_PLUS_HIGH_RISK_TYPE":
            recommendation = "BLOCK & REVIEW - System flag combined with high-risk transaction type"
        elif effective_probability > 0.7:
            recommendation = "IMMEDIATE BLOCK - High confidence fraud"
        else:
            recommendation = "BLOCK & REVIEW - Suspicious activity detected"
    else:
        recommendation = "Approve Transaction"

    logger.info(
        f"Prediction: {'FRAUD' if prediction else 'LEGIT'} | "
        f"ModelProb: {model_probability:.4f} | EffectiveProb: {effective_probability:.4f} | "
        f"Amount: ${txn.amount:,.2f}"
    )

    return {
        "verdict": "FRAUD DETECTED" if prediction == 1 else "Legitimate",
        "is_fraud": prediction,
        "fraud_probability": round(float(effective_probability), 4),
        "model_probability": round(float(model_probability), 4),
        "risk_level": risk_level,
        "recommendation": recommendation,
        "threshold_used": THRESHOLD,
        "rule_triggered": rule_triggered,
    }