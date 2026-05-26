# Javis 전사 도구 설명

## 개요
- 목적: `week12` 디렉터리(특히 `week12/records`)에 있는 오디오 파일을 텍스트로 전사하고, 각 전사 결과를 CSV로 저장하며 키워드 검색 기능을 제공한다.
- 주요 스크립트: `week13/javis.py`

## 주요 기능
- 오디오 파일 목록 조회: WAV, MP3, M4A, FLAC 등 확장자 지원
- STT 전사: `speech_recognition` 라이브러리를 사용(가상환경 권장)
- 전사 저장: 각 오디오 파일과 같은 이름의 `.CSV` 파일로 저장
  - CSV 컬럼: `start_time,end_time,text`
  - 시간 형식: `HH:MM:SS.mmm` (예: `00:01:23.045`)
- 키워드 검색: 저장된 CSV 파일들을 대상으로 키워드를 검색하여 콘솔에 결과 출력

## 파일 위치
- 스크립트: [week13/javis.py](week13/javis.py#L1)
- 예시/생성된 CSV: `week12/records/*.CSV`

## 실행/설치 방법
1. (권장) 프로젝트 루트에서 가상환경 생성 및 활성화
```bash
python3 -m venv .venv
source .venv/bin/activate
```
2. 가상환경에 필요한 패키지 설치
```bash
python -m pip install --upgrade pip
python -m pip install SpeechRecognition
```
3. 전사 실행
```bash
# week12/records 폴더의 오디오를 모두 전사
.venv/bin/python week13/javis.py --transcribe --dir week12/records --chunk 10
```
4. 키워드 검색
```bash
.venv/bin/python week13/javis.py --search 생명 --dir week12/records
```

## 구현 상세
- `list_audio_files(directory)`
  - 지정 폴더에서 허용된 오디오 확장자를 가진 파일 목록을 반환한다.
- `transcribe_file(path, chunk_length)`
  - `speech_recognition`의 `AudioFile`과 `Recognizer`를 이용해 청크 단위로 전사한다.
  - 라이브러리가 없을 경우 예외 메시지를 반환하여 CSV에 기록한다.
- `save_transcript_csv(audio_path, rows, chunk_length)`
  - 전사 결과를 `start_time,end_time,text` 형식으로 저장한다.
  - `end_time`은 `start_time + chunk_length`로 계산한다(간단한 청크 기반 방식).
- `search_keyword(directory, keyword)`
  - 디렉터리 내 CSV들을 읽고 `text` 컬럼에 대해 대소문자 무시 검색을 수행하여 콘솔에 결과를 출력한다.

## 개선/확장 포인트
- WAV 파일의 실제 길이를 읽어 마지막 청크의 `end_time`을 더 정확히 계산하도록 개선 가능(표준 라이브러리 `wave` 모듈 사용 추천).
- 전사 정확도를 높이기 위해 전처리(노이즈 제거), 샘플링 변환, 또는 다른 STT 엔진(오프라인 모델/클라우드 서비스) 연동 가능.
- 현재 전사는 청크 단위(기본 10초)로 동작하므로 문장 경계와 시차 보정 로직 추가로 품질 개선 가능.

## 주의사항
- 파이썬 표준 라이브러리만으로 모든 기능을 구현하라는 과제 제한이 있으나, STT 자체는 외부 라이브러리(`SpeechRecognition`) 사용을 허용한다.
- macOS 환경에서 `PyAudio` 등 추가 의존성이 필요할 수 있으며, 이 경우 설치 방법이 플랫폼마다 다르다.

---
문서에 추가 설명이나 예시가 필요하면 알려주세요.
