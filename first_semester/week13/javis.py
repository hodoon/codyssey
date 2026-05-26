"""Week13 Javis: STT transcription and CSV export.

This script lists audio files in '../week12', transcribes them (using
the optional `speech_recognition` library when available) in fixed-length
chunks, and writes per-file CSV transcripts with timestamps.

Usage:
  python3 week13/javis.py --transcribe
  python3 week13/javis.py --search 키워드

Notes:
  - Only the STT part may use an external library; the rest uses the
    Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import List, Tuple


def list_audio_files(directory: str) -> List[str]:
    """Return list of audio file paths in `directory`.

    Recognized extensions: .wav, .mp3, .m4a, .flac
    """
    exts = {'.wav', '.mp3', '.m4a', '.flac'}
    files: List[str] = []
    try:
        for entry in os.listdir(directory):
            path = os.path.join(directory, entry)
            if os.path.isfile(path):
                _, ext = os.path.splitext(entry)
                if ext.lower() in exts:
                    files.append(path)
    except FileNotFoundError:
        print('디렉터리를 찾을 수 없습니다:', directory, file=sys.stderr)
    return sorted(files)


def _format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm.

    Always show hours (two digits), minutes, seconds and milliseconds.
    """
    total_millis = int(round(seconds * 1000))
    millis = total_millis % 1000
    s = total_millis // 1000
    hrs = s // 3600
    mins = (s % 3600) // 60
    secs = s % 60
    return f'{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}'


def transcribe_file(path: str, chunk_length: int = 10) -> List[Tuple[float, str]]:
    """Transcribe `path` audio into chunks of `chunk_length` seconds.

    Returns list of (start_time_seconds, text).
    Falls back gracefully when `speech_recognition` is not installed.
    """
    try:
        import speech_recognition as sr
    except Exception:
        return [(0.0, 'STT 라이브러리(speech_recognition)가 설치되어 있지 않습니다.')]

    recognizer = sr.Recognizer()
    results: List[Tuple[float, str]] = []
    offset = 0.0
    # Keep reading until no more frames
    with sr.AudioFile(path) as source:
        while True:
            try:
                audio = recognizer.record(source, duration=chunk_length, offset=offset)
            except Exception:
                break
            if not getattr(audio, 'frame_data', b''):
                break
            try:
                text = recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                text = ''
            except sr.RequestError as exc:
                text = f'ERROR: {exc}'
            results.append((offset, text))
            offset += chunk_length
    return results


def save_transcript_csv(audio_path: str, rows: List[Tuple[float, str]], chunk_length: int) -> str:
    """Save `rows` to CSV next to `audio_path` with start/end times.

    CSV columns: start_time, end_time, text. Returns CSV path.
    """
    base, _ = os.path.splitext(audio_path)
    csv_path = base + '.CSV'
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow(['start_time', 'end_time', 'text'])
            for start, text in rows:
                end = start + float(chunk_length)
                writer.writerow([_format_time(start), _format_time(end), text])
    except OSError as exc:
        print('CSV 저장 실패:', exc, file=sys.stderr)
    return csv_path


def transcribe_all(directory: str, chunk_length: int = 10) -> None:
    files = list_audio_files(directory)
    if not files:
        print('오디오 파일을 찾을 수 없습니다:', directory)
        return
    for path in files:
        print('처리중:', path)
        rows = transcribe_file(path, chunk_length=chunk_length)
        csv_path = save_transcript_csv(path, rows, chunk_length=chunk_length)
        print('저장됨 ->', csv_path)


def search_keyword(directory: str, keyword: str) -> None:
    """Search CSV files in `directory` for `keyword` and print matches."""
    found = 0
    for entry in os.listdir(directory):
        if not entry.lower().endswith('.csv') and not entry.endswith('.CSV'):
            continue
        csv_path = os.path.join(directory, entry)
        try:
            with open(csv_path, 'r', encoding='utf-8') as fh:
                reader = csv.reader(fh)
                header = next(reader, None)
                for row in reader:
                        if len(row) < 3:
                            continue
                        time_str, end_time, text = row[0], row[1], row[2]
                        if keyword.lower() in text.lower():
                            print(f'{csv_path} | {time_str} - {end_time} | {text}')
                            found += 1
        except Exception:
            continue
    if not found:
        print('검색 결과 없음:', keyword)


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Javis STT transcriber')
    sub = parser.add_mutually_exclusive_group()
    sub.add_argument('--transcribe', action='store_true', help='Transcribe all audio in week12')
    sub.add_argument('--search', metavar='키워드', help='Search saved CSV transcripts')
    parser.add_argument('--dir', default=os.path.join('..', 'week12'), help='Audio/CSV directory')
    parser.add_argument('--chunk', type=int, default=10, help='Chunk length in seconds')
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    if args.transcribe:
        transcribe_all(args.dir, chunk_length=args.chunk)
        return 0
    if args.search:
        search_keyword(args.dir, args.search)
        return 0
    print('명령을 지정하세요. 예: --transcribe 또는 --search 키워드')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
