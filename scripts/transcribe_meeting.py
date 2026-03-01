#!/usr/bin/env python3.11
"""Transcribe meeting audio using faster-whisper with domain-specific vocabulary."""

import sys
import time
from pathlib import Path
from faster_whisper import WhisperModel

sys.stdout.reconfigure(line_buffering=True)

AUDIO_PATH = Path(__file__).parent.parent / "doc" / "scrapbook" / "meeting_audio.wav"
OUTPUT_DIR = Path(__file__).parent.parent / "doc" / "artifacts"

DOMAIN_PROMPT = (
    "Cell, Cell.ai, cell platform, cell app, cell media, "
    "AI, artificial intelligence, machine learning, ML, LLM, large language model, "
    "GPT, Claude, Anthropic, OpenAI, "
    "media pipeline, media processing, content moderation, "
    "API, SDK, backend, frontend, microservices, "
    "user engagement, retention, onboarding, "
    "PRD, product requirements document, product spec, "
    "MVP, sprint, roadmap, backlog, "
    "streaming, video, audio, transcoding, CDN, "
    "social media, feed, timeline, notifications, push notifications, "
    "real-time, WebSocket, WebRTC, "
    "database, PostgreSQL, Redis, S3, cloud, AWS, GCP, "
    "authentication, OAuth, JWT, "
    "analytics, metrics, KPI, DAU, MAU, "
    "deployment, CI/CD, Docker, Kubernetes"
)


def transcribe(model_size: str = "large-v3"):
    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"Loading Whisper model '{model_size}'...", flush=True)
    print("(First run downloads ~3GB model — subsequent runs use cache)", flush=True)
    t0 = time.time()

    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
        cpu_threads=8,
    )
    print(f"Model loaded in {time.time() - t0:.1f}s", flush=True)

    print(f"\nTranscribing {AUDIO_PATH.name}...", flush=True)
    t0 = time.time()

    segments, info = model.transcribe(
        str(AUDIO_PATH),
        language="en",
        initial_prompt=DOMAIN_PROMPT,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=400,
        ),
    )

    duration = info.duration
    print(f"Audio duration: {duration/60:.1f} min | Language: {info.language} (prob: {info.language_probability:.2f})", flush=True)
    print(f"Processing segments...\n", flush=True)

    all_segments = []
    for seg in segments:
        all_segments.append(seg)
        pct = seg.end / duration * 100
        start_m, start_s = divmod(int(seg.start), 60)
        elapsed = time.time() - t0
        print(f"[{pct:5.1f}%] [{start_m:02d}:{start_s:02d}] {seg.text.strip()}", flush=True)

    elapsed = time.time() - t0
    print(f"\nTranscription complete: {len(all_segments)} segments in {elapsed:.1f}s", flush=True)

    ts_path = OUTPUT_DIR / "meeting_transcript_timestamped.txt"
    with open(ts_path, "w") as f:
        f.write("MEETING TRANSCRIPT (with timestamps)\n")
        f.write(f"Source: {AUDIO_PATH.name}\n")
        f.write(f"Duration: {duration:.0f}s ({duration/60:.1f} min)\n")
        f.write(f"Model: {model_size}\n")
        f.write("=" * 80 + "\n\n")

        for seg in all_segments:
            start_m, start_s = divmod(int(seg.start), 60)
            end_m, end_s = divmod(int(seg.end), 60)
            f.write(f"[{start_m:02d}:{start_s:02d} - {end_m:02d}:{end_s:02d}]  {seg.text.strip()}\n")

    print(f"Timestamped transcript -> {ts_path}", flush=True)

    clean_path = OUTPUT_DIR / "meeting_transcript_clean.txt"
    with open(clean_path, "w") as f:
        f.write("MEETING TRANSCRIPT\n")
        f.write(f"Source: {AUDIO_PATH.name}\n")
        f.write(f"Duration: {duration/60:.1f} min\n")
        f.write("=" * 80 + "\n\n")

        current_paragraph = []
        last_end = 0
        for seg in all_segments:
            if seg.start - last_end > 3.0 and current_paragraph:
                f.write(" ".join(current_paragraph) + "\n\n")
                current_paragraph = []
            current_paragraph.append(seg.text.strip())
            last_end = seg.end

        if current_paragraph:
            f.write(" ".join(current_paragraph) + "\n\n")

    print(f"Clean transcript     -> {clean_path}", flush=True)

    words_path = OUTPUT_DIR / "meeting_transcript_words.txt"
    with open(words_path, "w") as f:
        f.write("WORD-LEVEL TRANSCRIPT (with confidence scores)\n")
        f.write("Low-confidence words (<0.6) are marked with [?]\n")
        f.write("=" * 80 + "\n\n")

        for seg in all_segments:
            if seg.words:
                for word in seg.words:
                    marker = " [?]" if word.probability < 0.6 else ""
                    f.write(f"{word.word}{marker}")
                f.write("\n")

    print(f"Word-level detail    -> {words_path}", flush=True)
    print(f"\nAll transcripts saved to {OUTPUT_DIR}/", flush=True)


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "large-v3"
    transcribe(size)
