from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for
from yt_dlp import YoutubeDL

from script import transcribe_audio

BASE_DIR = Path(__file__).parent.resolve()
DOWNLOAD_DIR = BASE_DIR / "downloads"
PROCESSED_DIR = BASE_DIR / "processed"

for directory in (DOWNLOAD_DIR, PROCESSED_DIR):
    directory.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")


class TranscriptionError(Exception):
    pass


def _download_audio(url: str) -> Path:
    """
    Download the audio track of the provided YouTube URL and return the path to
    the downloaded file.
    """

    temp_name = uuid.uuid4().hex
    outtmpl = str(DOWNLOAD_DIR / f"{temp_name}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=True)

    # yt-dlp chooses the extension; find the downloaded file
    downloaded = next(DOWNLOAD_DIR.glob(f"{temp_name}.*"), None)
    if not downloaded:
        raise TranscriptionError("Unable to locate downloaded audio file.")

    return downloaded


def _convert_to_wav(source_file: Path) -> Path:
    """
    Convert the downloaded audio file to WAV via ffmpeg.
    """

    wav_path = PROCESSED_DIR / f"{source_file.stem}.wav"

    ffmpeg_binary = os.getenv("FFMPEG_BINARY", "ffmpeg")
    command = [
        ffmpeg_binary,
        "-y",
        "-i",
        str(source_file),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(wav_path),
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise TranscriptionError(f"ffmpeg failed: {exc.stderr.decode(errors='ignore')}") from exc

    return wav_path


def _clean_temp_files(*paths: Path) -> None:
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


@app.route("/", methods=["GET", "POST"])
def index():
    transcript_text = None
    transcript_segments = None

    if request.method == "POST":
        video_url = request.form.get("video_url", "").strip()

        if not video_url:
            flash("Please paste a YouTube URL.", "danger")
            return redirect(url_for("index"))

        downloaded_path = None
        wav_path = None

        try:
            downloaded_path = _download_audio(video_url)
            wav_path = _convert_to_wav(downloaded_path)
            transcription = transcribe_audio(wav_path)
            transcript_text = transcription.get("text")
            segments = transcription.get("segments") or []
            transcript_segments = [
                {
                    "start": round(segment.get("start", 0), 2),
                    "end": round(segment.get("end", 0), 2),
                    "text": segment.get("text", "").strip(),
                }
                for segment in segments
                if segment.get("text")
            ]
        except Exception as exc:  # pylint: disable=broad-except
            flash(str(exc), "danger")
        finally:
            _clean_temp_files(*(p for p in [downloaded_path, wav_path] if p))

    return render_template(
        "index.html",
        transcript_text=transcript_text,
        transcript_segments=transcript_segments,
    )


if __name__ == "__main__":
    app.run(debug=True)

