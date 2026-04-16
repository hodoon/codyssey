# Mars Mission Computer - Week 07

## 개요

화성 기지 미션 컴퓨터의 시스템 상태를 모니터링하는 프로그램입니다.
운영체계 정보, CPU/메모리 실시간 부하를 JSON 형식으로 출력합니다.

---

## 파일 구조

```
week07/
├── mars_mission_computer.py   # 메인 소스 파일
└── setting.txt                # 출력 항목 설정 파일 (보너스)
```

---

## 클래스 및 함수 설명

### `load_settings()`

`setting.txt` 파일을 읽어 출력할 항목 목록을 반환하는 전역 함수입니다.

- 파일이 없으면 모든 항목을 기본값으로 반환
- 유효하지 않은 키는 무시
- `FileNotFoundError`, `PermissionError`, `OSError` 예외 처리

---

### `DummySensor` 클래스

LCG(선형 합동 생성기) 알고리즘으로 화성 기지 환경 데이터를 생성하는 더미 센서입니다.

| 메소드 | 설명 |
|--------|------|
| `__init__()` | env_values 초기화, LCG 파라미터 설정, 로그 파일명 생성 |
| `_next_lcg()` | LCG 알고리즘으로 0~1 사이 랜덤 실수 반환 |
| `_rand_range(lo, hi)` | lo~hi 범위의 랜덤 실수 생성 (소수점 2자리) |
| `set_env()` | 각 환경 값을 랜덤으로 갱신 |
| `get_env()` | env_values 반환 및 로그 파일(CSV)에 기록 |

**생성되는 환경 데이터:**

| 항목 | 범위 |
|------|------|
| 내부 온도 | 18 ~ 30 |
| 외부 온도 | 0 ~ 21 |
| 내부 습도 | 50 ~ 60 |
| 외부 조도 | 500 ~ 715 |
| 내부 CO2 | 0.02 ~ 0.1 |
| 내부 산소 | 4 ~ 7 |

---

### `MissionComputer` 클래스

미션 컴퓨터의 핵심 클래스입니다. 센서 데이터 수집, 시스템 정보 조회, 부하 모니터링 기능을 담당합니다.

#### `get_mission_computer_info()`

미션 컴퓨터의 시스템 정보를 JSON 형식으로 출력합니다.

| 키 | 항목 | 사용 모듈 |
|----|------|-----------|
| `os` | 운영체계 | `platform.system()` |
| `os_version` | 운영체계 버전 | `platform.version()` |
| `cpu_type` | CPU 타입 | `platform.processor()` |
| `cpu_cores` | CPU 코어 수 | `os.cpu_count()` |
| `memory_size` | 메모리 크기 (GB) | `psutil.virtual_memory().total` |

**출력 예시:**
```json
{
    "os": "Darwin",
    "os_version": "Darwin Kernel Version 25.4.0 ...",
    "cpu_type": "arm",
    "cpu_cores": 10,
    "memory_size": "16.00 GB"
}
```

---

#### `get_mission_computer_load()`

미션 컴퓨터의 실시간 부하 정보를 JSON 형식으로 출력합니다.
`cpu_percent(interval=1)` 호출로 1초간 측정 후 출력됩니다.

| 키 | 항목 | 사용 모듈 |
|----|------|-----------|
| `cpu_usage` | CPU 실시간 사용량 (%) | `psutil.cpu_percent(interval=1)` |
| `memory_usage` | 메모리 실시간 사용량 (%) | `psutil.virtual_memory().percent` |

**출력 예시:**
```json
{
    "cpu_usage": "14.4%",
    "memory_usage": "76.6%"
}
```

---

#### `get_sensor_data()`

5초 간격으로 환경 센서 데이터를 수집하여 JSON으로 출력합니다.

- 엔터 키 입력 시 루프 종료 후 `System stoped....` 출력
- 5분마다 수집된 데이터의 평균값을 별도 출력
- 입력 대기는 별도 스레드(`_wait_for_stop`)로 처리

---

## setting.txt (보너스)

출력할 항목을 한 줄씩 지정합니다. 파일이 없으면 전체 항목이 출력됩니다.

**사용 가능한 키:**

```
os
os_version
cpu_type
cpu_cores
memory_size
cpu_usage
memory_usage
```

**예시 - 일부 항목만 출력:**

```
os
cpu_cores
cpu_usage
```

---

## 실행 방법

```bash
cd first_semester/week07
python3 mars_mission_computer.py
```

---

## 의존 라이브러리

| 라이브러리 | 용도 | 종류 |
|-----------|------|------|
| `platform` | OS 및 CPU 정보 조회 | 표준 라이브러리 |
| `os` | CPU 코어 수 조회 | 표준 라이브러리 |
| `json` | JSON 형식 출력 | 표준 라이브러리 |
| `time`, `threading`, `datetime` | 센서 루프 제어 | 표준 라이브러리 |
| `psutil` | 메모리/CPU 사용량 조회 | 외부 라이브러리 (시스템 정보용) |

> `psutil`이 설치되어 있지 않아도 실행 가능하며, 해당 항목은 `'psutil 미설치로 조회 불가'`로 출력됩니다.

---

## 예외 처리

모든 시스템 정보 수집 항목은 개별 `try/except` 블록으로 처리되어, 특정 항목 조회 실패 시에도 나머지 항목은 정상 출력됩니다.
