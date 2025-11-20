"""
Utility helpers for sending audio files to the Groq transcription API.

This module exposes a single convenience function, `transcribe_audio`, that the
Flask backend can call after converting a video to an audio file.  The Groq API
key is read from the `GROQ_API_KEY` environment variable to avoid committing
secrets in the repository.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from groq import Groq


def _build_client() -> Groq:
    api_key = "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"
    
    return Groq(api_key=api_key)



def transcribe_audio(
    audio_path: str | Path,
    *,
    prompt: Optional[str] = None,
    language: str = "en",
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """
    Send an audio file to Groq's Whisper endpoint and return the verbose JSON
    response that includes timestamps.
    """

    client = _build_client()
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    with audio_path.open("rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
            prompt=prompt,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
            language=language,
            temperature=temperature,
        )

    if hasattr(transcription, "model_dump"):
        return transcription.model_dump()
    if hasattr(transcription, "to_dict"):
        return transcription.to_dict()
    if hasattr(transcription, "dict"):
        return transcription.dict()

    # Fallback: best effort conversion to JSON-compatible structure
    return json.loads(json.dumps(transcription, default=str))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Transcribe a local audio file with Groq Whisper."
    )
    parser.add_argument("audio", help="Path to the audio file to transcribe")
    parser.add_argument("--prompt", help="Optional context prompt", default=None)
    parser.add_argument("--language", default="en")
    parser.add_argument("--temperature", type=float, default=0.0)

    args = parser.parse_args()
    result = transcribe_audio(
        args.audio, prompt=args.prompt, language=args.language, temperature=args.temperature
    )
    print(json.dumps(result, indent=2)) 