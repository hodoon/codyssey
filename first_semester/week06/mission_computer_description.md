# mars_mission_computer.py 코드 설명

## 개요

화성 기지의 환경 데이터를 5초마다 수집하여 JSON 형식으로 출력하는 미션 컴퓨터 프로그램입니다.
`DummySensor` 클래스가 LCG 알고리즘으로 가상의 센서 데이터를 생성하고,
`MissionComputer` 클래스가 이를 수집·출력·기록합니다.

---

## 사용 라이브러리

| 라이브러리 | 용도 |
|---|---|
| `json` | env_values를 JSON 형식으로 출력 |
| `time` | 5초 주기 반복 및 5분 평균 타이머 |
| `threading` | 키 입력 감지를 별도 스레드로 처리 |
| `datetime` | 로그 타임스탬프 및 파일명 생성 |

---

## 클래스 구조

### DummySensor

화성 기지 환경 데이터를 LCG(선형 합동 생성기) 알고리즘으로 생성하는 더미 센서 클래스입니다.

#### 속성

| 속성 | 설명 |
|---|---|
| `env_values` | 6가지 환경 데이터를 담는 딕셔너리 |
| `log_filename` | 실행 시각 기반 고유 로그 파일명 (`mars_mission_computer_YYYYMMDD_HHMMSS.log`) |
| `_lcg_state` | LCG 현재 상태값 (seed) |
| `_lcg_a`, `_lcg_c`, `_lcg_m` | LCG 파라미터 |

#### env_values 항목

| 키 | 설명 | 범위 |
|---|---|---|
| `mars_base_internal_temperature` | 기지 내부 온도 (°C) | 18 ~ 30 |
| `mars_base_external_temperature` | 기지 외부 온도 (°C) | 0 ~ 21 |
| `mars_base_internal_humidity` | 기지 내부 습도 (%) | 50 ~ 60 |
| `mars_base_external_illuminance` | 기지 외부 광량 (lux) | 500 ~ 715 |
| `mars_base_internal_co2` | 기지 내부 CO₂ 농도 (%) | 0.02 ~ 0.1 |
| `mars_base_internal_oxygen` | 기지 내부 산소 농도 (%) | 4 ~ 7 |

#### 메소드

**`_next_lcg()`**
LCG 점화식으로 다음 난수 상태를 계산하고 0~1 범위의 실수로 반환합니다.

```
state = (a * state + c) % m
```

**`_rand_range(lo, hi)`**
`_next_lcg()` 결과를 `[lo, hi]` 범위로 변환하여 소수점 2자리로 반환합니다.

**`set_env()`**
`_rand_range()`를 사용해 6가지 환경 데이터를 `env_values`에 저장합니다.

**`get_env()`**
`env_values`를 반환하고, CSV 형식으로 로그 파일에 한 줄 기록합니다.
로그 형식: `YYYY-MM-DD HH:MM:SS,온도내부,온도외부,습도,광량,CO2,산소`

---

### MissionComputer

센서 데이터를 주기적으로 수집하고 출력하는 미션 컴퓨터 클래스입니다.

#### 속성

| 속성 | 설명 |
|---|---|
| `env_values` | 현재 환경 데이터 딕셔너리 |
| `ds` | DummySensor 인스턴스 |
| `_running` | 반복 실행 제어 플래그 |
| `_history` | 5분 평균 계산용 데이터 이력 |
| `_last_avg_time` | 마지막 평균 출력 시각 |

#### 메소드

**`get_sensor_data()`**
메인 실행 루프입니다.

```
1. 키 입력 감지 스레드 시작
2. while _running:
   a. ds.set_env() → 새 센서값 생성
   b. ds.get_env() → 값 읽기 + 로그 파일 기록
   c. env_values 갱신
   d. JSON 형식으로 화면 출력
   e. _history에 현재값 추가
   f. 5분 경과 시 _print_5min_avg() 호출
   g. 0.1초 × 50회 = 약 5초 대기 (중단 감지 가능)
3. 루프 종료 후 'System stoped....' 출력
```

**`_wait_for_stop()`** *(보너스)*
별도 데몬 스레드로 실행되며, 엔터 키 입력을 기다려 `_running = False`로 설정합니다.

**`_print_5min_avg()`** *(보너스)*
`_history`에 쌓인 데이터의 항목별 평균을 계산해 JSON 형식으로 출력합니다.

---

## 로그 파일 명명 규칙

실행할 때마다 고유한 파일명이 생성되어 이전 로그를 덮어쓰지 않습니다.

```
mars_mission_computer_20260409_153022.log
mars_mission_computer_20260409_161500.log
...
```

파일명은 `DummySensor.__init__()` 시점의 날짜·시각을 기준으로 합니다.

---

## 실행 흐름

```
프로그램 시작
  │
  ├─ MissionComputer 인스턴스화 (RunComputer)
  │    └─ DummySensor 인스턴스화 (ds)
  │         └─ 고유 로그 파일명 생성
  │
  └─ RunComputer.get_sensor_data() 호출
       │
       ├─ [스레드] 엔터 키 대기
       │
       └─ [메인] 5초마다 반복
            ├─ 센서값 생성 및 읽기
            ├─ JSON 출력
            ├─ 로그 파일 기록
            └─ (5분마다) 평균값 출력
```

---

## 출력 예시

### 정상 출력 (5초마다)

```json
{
    "mars_base_internal_temperature": 24.35,
    "mars_base_external_temperature": 10.82,
    "mars_base_internal_humidity": 54.71,
    "mars_base_external_illuminance": 612.40,
    "mars_base_internal_co2": 0.06,
    "mars_base_internal_oxygen": 5.23
}
```

### 5분 평균 출력

```
=== 5분 평균 환경 데이터 ===
{
    "mars_base_internal_temperature": 24.12,
    ...
}
```

### 종료 시

```
System stoped....
```

---

## 보너스 기능 요약

| 기능 | 구현 방법 |
|---|---|
| 키 입력으로 중단 | `threading.Thread`로 `input()` 대기, 엔터 입력 시 `_running = False` |
| 5분 평균 출력 | `time.time()` 차이로 300초 경과 감지, `_history` 리스트 평균 계산 |
| 로그 파일 중복 방지 | 인스턴스 생성 시각으로 고유 파일명 자동 생성 |
