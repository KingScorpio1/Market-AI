#sentiment.py

from transformers import pipeline
import numpy as np
from textblob import TextBlob # Add to requirements.txt

# Load model once to save resources
sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Keywords that move markets
MARKET_MOVERS = ["TRUMP", "FED", "POWELL", "SEC", "BAN", "RATE HIKE", "INFLATION", "CRASH"]

def analyze_sentiment(texts):
    if not texts:
        return 0.0
    
    results = sentiment_model(texts)
    scores = []
    
    for i, res in enumerate(results):
        score = res["score"]
        label = res["label"]
        text_content = texts[i].upper()
        
        # 1. Base Score
        final_score = score if label == "POSITIVE" else -score
        
        # 2. "Narrative" Weighting
        # If a headline mentions a market mover, double its weight
        for keyword in MARKET_MOVERS:
            if keyword in text_content:
                final_score *= 2.0 # Amplify impact
                break
        
        scores.append(final_score)
            
    # Clip result between -1 and 1
    avg_score = np.mean(scores)
    return max(min(avg_score, 1.0), -1.0)