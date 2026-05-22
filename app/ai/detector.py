import requests
import os

HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_API_URL = "https://api-inference.huggingface.co/models/unitary/toxic-bert"

BLOCK_KEYWORDS = [
    "kill yourself", "kys", "go die", "end your life",
    "nobody likes you", "i will kill you", "go kill yourself",
    "you should die", "i hate you", "get lost",
]

WARN_KEYWORDS = [
    "ugly", "fat", "loser", "idiot", "stupid", "dumb",
    "hate you", "worthless", "pathetic", "moron", "trash",
    "shut up", "freak", "disgusting",
]

def keyword_check(text):
    text_lower = text.lower()
    block_found = [kw for kw in BLOCK_KEYWORDS if kw in text_lower]
    warn_found = [kw for kw in WARN_KEYWORDS if kw in text_lower]
    if block_found:
        return {"action": "block", "keywords": block_found}
    if warn_found:
        return {"action": "warn", "keywords": warn_found}
    return {"action": "allow", "keywords": []}

def analyze_with_ai(text):
    if not HF_API_KEY:
        return None
    try:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": text[:512]},
            timeout=10
        )
        if response.status_code == 200:
            results = response.json()
            if isinstance(results, list) and len(results) > 0:
                scores = {}
                items = results[0] if isinstance(results[0], list) else results
                for item in items:
                    scores[item["label"].lower()] = item["score"]
                toxic_labels = [
                    "toxic", "severe_toxic", "obscene",
                    "threat", "insult", "identity_hate"
                ]
                max_score = max(
                    (scores.get(l, 0) for l in toxic_labels),
                    default=0
                )
                return {"score": max_score}
    except Exception:
        pass
    return None

def analyze_text(text):
    if not text or not text.strip():
        return {
            "is_harmful": False,
            "confidence": 0.0,
            "label": "clean",
            "flagged_keywords": [],
            "action": "allow"
        }

    # Step 1 - keyword check
    kw = keyword_check(text)
    if kw["action"] == "block":
        return {
            "is_harmful": True,
            "confidence": 0.99,
            "label": "cyberbullying",
            "flagged_keywords": kw["keywords"],
            "action": "block"
        }

    # Step 2 - HuggingFace AI
    ai_result = analyze_with_ai(text)
    if ai_result:
        score = ai_result["score"]
        if score > 0.80:
            return {
                "is_harmful": True,
                "confidence": round(score, 4),
                "label": "cyberbullying",
                "flagged_keywords": kw["keywords"],
                "action": "block"
            }
        elif score > 0.50 or kw["action"] == "warn":
            return {
                "is_harmful": True,
                "confidence": round(score, 4),
                "label": "potentially harmful",
                "flagged_keywords": kw["keywords"],
                "action": "warn"
            }
        else:
            return {
                "is_harmful": False,
                "confidence": round(score, 4),
                "label": "clean",
                "flagged_keywords": [],
                "action": "allow"
            }

    # Step 3 - fallback keywords only
    if kw["action"] == "warn":
        return {
            "is_harmful": True,
            "confidence": 0.75,
            "label": "potentially harmful",
            "flagged_keywords": kw["keywords"],
            "action": "warn"
        }

    return {
        "is_harmful": False,
        "confidence": 0.0,
        "label": "clean",
        "flagged_keywords": [],
        "action": "allow"
    }