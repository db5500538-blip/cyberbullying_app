from transformers import pipeline

_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        try:
            _classifier = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                top_k=None
            )
        except Exception:
            _classifier = pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                top_k=None
            )
    return _classifier

KEYWORDS = [
    "kill yourself", "kys", "die", "ugly", "fat", "loser", "idiot",
    "stupid", "dumb", "hate you", "nobody likes you", "worthless",
    "pathetic", "retard", "moron", "trash", "shut up",
]

def analyze_text(text: str) -> dict:
    if not text or not text.strip():
        return {"is_harmful": False, "confidence": 0.0,
                "label": "clean", "flagged_keywords": [], "action": "allow"}

    text_lower = text.lower()
    keywords_found = [kw for kw in KEYWORDS if kw in text_lower]
    kw_flagged = len(keywords_found) > 0

    try:
        clf = get_classifier()
        results = clf(text[:512])
        scores = {}
        if isinstance(results[0], list):
            for item in results[0]:
                scores[item["label"].lower()] = item["score"]
        else:
            for item in results:
                scores[item["label"].lower()] = item["score"]

        toxic_labels = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
        max_score = max((scores.get(l, 0) for l in toxic_labels), default=0)

        if "negative" in scores and not any(l in scores for l in toxic_labels):
            max_score = scores.get("negative", 0)

        is_harmful = max_score > 0.6 or kw_flagged
        confidence = round(max(max_score, 0.9 if kw_flagged else 0), 4)

        if max_score > 0.85 or (kw_flagged and max_score > 0.5):
            action, label = "block", "cyberbullying"
        elif max_score > 0.6 or kw_flagged:
            action, label = "warn", "potentially harmful"
        else:
            action, label = "allow", "clean"

        return {"is_harmful": is_harmful, "confidence": confidence,
                "label": label, "flagged_keywords": keywords_found, "action": action}

    except Exception as e:
        is_harmful = kw_flagged
        return {"is_harmful": is_harmful,
                "confidence": 0.9 if is_harmful else 0.1,
                "label": "cyberbullying" if is_harmful else "clean",
                "flagged_keywords": keywords_found,
                "action": "block" if is_harmful else "allow"}