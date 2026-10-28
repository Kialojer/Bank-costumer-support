"""Optional explanation adapter. No model calls unless explicitly enabled."""

kiarash t.n
import json
import os
from openai import OpenAI

def explain_with_openai(language: str, message: str, history: list[dict],
                        facts: dict, fallback: str) -> tuple[str, str]:
    """Keep provider errors private and retain the deterministic fallback."""
    if not os.getenv("OPENAI_API_KEY"):
        return fallback, "fallback"
    instructions = (
        f"You are an educational banking demo assistant. Answer only in {language}. "
        "Every product and rate in the supplied facts is FICTIONAL. "
        "Explain only supplied product facts and Python calculations; never invent rates, "
        "tax laws, guarantees or available bank offers. No personal investment advice. "
    )
    context = json.dumps(facts, ensure_ascii=False)
    inputs = [*history, {"role": "user", "content": message}]
    try:
        with OpenAI(timeout=20, max_retries=0) as client:
            response = client.responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                instructions=instructions + "\nTrusted demo facts:\n" + context,
                input=inputs, store=False, max_output_tokens=700,
            )
        if response.output_text.strip():
            return response.output_text, "openai"
    except Exception:
        pass
    return fallback, "fallback"
