## Modern Video Transcriber

A lightweight Flask application that ingests a YouTube URL, downloads the video's audio track with `yt-dlp`, converts it to 16 kHz mono WAV via `ffmpeg`, and sends the audio to Groq's Whisper API for high-quality speech-to-text output. The UI (Bootstrap + custom CSS) displays the full transcript alongside segment-level timestamps for quick scanning.

### Features
- Paste any public YouTube link; the backend handles download, conversion, and cleanup.
- Segment timeline with start/end timestamps derived from the Whisper verbose JSON response.
- Simple Flask front end styled with Bootstrap 5 and a custom hero section.
- CLI helper (`script.py`) to transcribe arbitrary local audio files without the web UI.

### Requirements
- Python 3.10+
- `ffmpeg` available on your PATH (configurable via `FFMPEG_BINARY`).
- Groq account + API key (environment variable recommended).

### Quick Start
```bash
python -m venv .venv
.venv\Scripts\activate  # PowerShell on Windows
pip install -r requirements.txt
set FLASK_APP=app.py
set GROQ_API_KEY=your_api_key  # see note below
flask run
```
Then open `http://127.0.0.1:5000` and submit a YouTube URL.

> **Important:** The current implementation in `script.py` hardcodes an API key in `_build_client`. Replace that value with `os.environ["GROQ_API_KEY"]` (or similar) before deploying or sharing the project to keep credentials out of the codebase.

### Environment Variables
- `GROQ_API_KEY` – Groq Whisper API key (should be kept secret).
- `FLASK_SECRET_KEY` – optional Flask session secret.
- `FFMPEG_BINARY` – path to an `ffmpeg` binary when not on PATH.

### Project Structure
```
app.py            # Flask routes and yt-dlp/ffmpeg integration
script.py         # Groq Whisper helper + CLI entry point
templates/index.html
static/styles.css
downloads/        # temp input audio (auto-created)
processed/        # temp WAV output (auto-created)
```

### CLI Usage
Transcribe a local file without the Flask UI:
```bash
python script.py path/to/audio.wav --language en --temperature 0.0
```
The script prints the verbose JSON transcription to stdout.

### Troubleshooting
- Verify `ffmpeg -version` runs from the same shell; otherwise set `FFMPEG_BINARY`.
- Clean the `downloads/` and `processed/` folders if a previous run was interrupted.
- Set `FLASK_DEBUG=1` for verbose error messages during development.

### Roadmap Ideas
- Persist transcripts per user and allow downloads.
- Support direct file uploads instead of YouTube-only input.
- Swap the hardcoded Groq key for an environment-based configuration helper.

