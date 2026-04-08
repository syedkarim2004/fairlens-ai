"""
FairLens AI — Gemma (Ollama) Service
-------------------------------------
Calls a local Ollama server running gemma3:4b (or similar) to provide
deeper bias analysis. Handles fallbacks safely.
"""

import logging
import requests

logger = logging.getLogger(__name__)

def get_gemma_analysis(prompt: str) -> str:
    """
    Uses local Ollama server to run Gemma model.
    No API key required.
    """
    try:
        print("Using Gemma (Ollama)...")
        logger.info("Using Gemma (Ollama) for deep analysis")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:4b",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            logger.error(f"Ollama returned status {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"Fallback triggered: Ollama Gemma error: {e}")
        logger.error(f"Ollama Gemma error: {e}")
        return None
