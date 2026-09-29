"""Thin wrapper around Groq. Handles retries, model fallback and JSON parsing."""
import json
import re
import time

import config

_client = None


def get_client():
    global _client
    if _client is None:
        from groq import Groq  # imported here so the file loads even before pip install
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def _clean(text: str) -> str:
    # Qwen models may add <think>...</think>; remove it. Also strip ``` fences.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return text.strip()


def parse_json(text: str):
    text = _clean(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def chat(system: str, user: str, json_mode: bool = False, temperature: float = 0.2) -> str:
    """Call the LLM. Tries the primary model, then the fallback. Retries on errors."""
    last_error = None
    for model in (config.PRIMARY_MODEL, config.FALLBACK_MODEL):
        for attempt in range(2):
            try:
                kwargs = dict(
                    model=model,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                response = get_client().chat.completions.create(**kwargs)
                return _clean(response.choices[0].message.content or "")
            except Exception as e:  # function-calling / JSON-mode errors land here
                last_error = e
                time.sleep(1.5)
    raise RuntimeError(f"LLM call failed after retries: {last_error}")


def chat_json(system: str, user: str):
    """Ask for JSON and return a Python dict. Retries once without JSON mode."""
    prompt = user + "\n\nReturn ONLY valid JSON. No explanation, no markdown."
    raw = chat(system, prompt, json_mode=True)
    try:
        return parse_json(raw)
    except Exception:
        raw = chat(system, prompt, json_mode=False)
        return parse_json(raw)
