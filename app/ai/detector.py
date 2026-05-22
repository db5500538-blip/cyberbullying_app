BLOCK_KEYWORDS = [
    "kill yourself", "kys", "go die", "end your life",
    "you should die", "i will kill you", "go kill yourself",
    "nobody likes you", "i hate you", "get lost",
    "go to hell", "drop dead", "die already",
    "you are worthless", "you deserve to die",
]

WARN_KEYWORDS = [
    "ugly", "fat", "loser", "idiot", "stupid", "dumb",
    "hate you", "worthless", "pathetic", "moron", "trash",
    "shut up", "freak", "disgusting", "retard", "useless",
    "nobody cares", "you suck", "failure", "waste of space",
    "go away", "leave me alone", "you are terrible",
    "horrible person", "nobody wants you",
]


def analyze_text(text: str) -> dict:
    if not text or not text.strip():
        return {
            "is_harmful": False,
            "confidence": 0.0,
            "label": "clean",
            "flagged_keywords": [],
            "action": "allow"
        }

    text_lower = text.lower()

    # Check block keywords first
    block_found = [kw for kw in BLOCK_KEYWORDS if kw in text_lower]
    if block_found:
        return {
            "is_harmful": True,
            "confidence": 0.99,
            "label": "cyberbullying",
            "flagged_keywords": block_found,
            "action": "block"
        }

    # Check warn keywords
    warn_found = [kw for kw in WARN_KEYWORDS if kw in text_lower]
    if warn_found:
        return {
            "is_harmful": True,
            "confidence": 0.75,
            "label": "potentially harmful",
            "flagged_keywords": warn_found,
            "action": "warn"
        }

    # All clean
    return {
        "is_harmful": False,
        "confidence": 0.0,
        "label": "clean",
        "flagged_keywords": [],
        "action": "allow"
    }