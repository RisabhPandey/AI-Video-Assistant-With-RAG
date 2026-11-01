"""
Audio input utilities for the AI Video Assistant.

The Sarvam Batch API can process long recordings. Therefore this module
returns ONE normalized WAV path instead of splitting the audio into chunks.
"""

import os
from pathlib import Path

import yt_dlp
from pydub import AudioSegment

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    """Download the best available YouTube audio and convert it to WAV."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("Please provide a valid HTTP/HTTPS URL.")

    output_template = str(DOWNLOAD_DIR / "%(title).150B.%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "quiet": False,
        "no_warnings": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        prepared_path = Path(ydl.prepare_filename(info))
        wav_path = prepared_path.with_suffix(".wav")

    if not wav_path.exists():
        # Some yt-dlp postprocessor setups may report a different extension.
        candidates = list(DOWNLOAD_DIR.glob(f"*{info.get('id', '')}*.wav"))
        if not candidates:
            raise FileNotFoundError(
                f"yt-dlp finished, but the converted WAV was not found: {wav_path}"
            )
        wav_path = candidates[0]

    return str(wav_path)


def convert_to_wav(input_path: str) -> str:
    """
    Convert a local audio/video file to mono 16 kHz WAV.

    A separate output file is created; the original is not modified.
    """
    source_path = Path(input_path)

    if not source_path.exists():
        raise FileNotFoundError(f"Input file not found: {source_path}")

    output_path = source_path.with_name(source_path.stem + "_sarvam.wav")

    audio = AudioSegment.from_file(str(source_path))
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(str(output_path), format="wav")

    return str(output_path)


def process_input(source: str) -> str:
    """
    Accept a YouTube URL or local file and return one WAV path.

    Unlike the previous version, this function does NOT call chunk_audio().
    """
    source = source.strip()

    if source.startswith(("http://", "https://")):
        print("Detected URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting audio to WAV...")
        wav_path = convert_to_wav(source)

    print(f"Audio ready for Sarvam Batch API: {wav_path}")
    return wav_path
