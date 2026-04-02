# Week 05 - 더미 센서 (DummySensor) 구현

## 과제 배경

화성 기지의 미션 컴퓨터를 복구하기 위해 기지 환경 데이터를 읽고 출력하는 기능이 필요하다.
실제 센서 연결 전, 테스트용 더미 센서를 먼저 구현하여 데이터 흐름을 검증한다.

---

## 파일 구성

| 파일 | 설명 |
|------|------|
| `mars_mission_computer.py` | DummySensor 클래스 구현 |
| `mars_mission_computer.log` | get_env() 호출 시 자동 생성되는 로그 파일 |

---

## 클래스 구조

```
DummySensor
├── env_values (dict)         # 환경 데이터 저장 딕셔너리
├── _lcg_state / _lcg_a / _lcg_c / _lcg_m  # LCG 파라미터
│
├── __init__()                # 초기화
├── _next_lcg()               # LCG 난수 생성 (내부 전용)
├── _rand_range(lo, hi)       # 범위 내 난수 생성 (내부 전용)
├── _get_now_str()            # 현재 날짜시간 문자열 반환 (내부 전용)
├── set_env()                 # 환경값 랜덤 설정 (공개)
└── get_env()                 # 환경값 반환 + 로그 기록 (공개)
```

---

## 코드 설명

### 1. `__init__()` — 초기화

```python
self.env_values = {
    'mars_base_internal_temperature': 0,
    'mars_base_external_temperature': 0,
    'mars_base_internal_humidity': 0,
    'mars_base_external_illuminance': 0,
    'mars_base_internal_co2': 0,
    'mars_base_internal_oxygen': 0
}
self._lcg_state = id(object())
self._lcg_a = 1664525
self._lcg_c = 1013904223
self._lcg_m = 2 ** 32
```

- 과제에서 요구한 6개의 환경 변수를 `env_values` 딕셔너리로 정의하고 초기값 0으로 설정한다.
- LCG 난수 생성기의 초기 시드는 `id(object())`를 사용한다.
  - `id(object())`는 임시 객체의 메모리 주소를 반환하므로, 실행할 때마다 다른 값이 나와 시드로 활용한다.
- LCG 파라미터 `a`, `c`, `m`은 Numerical Recipes에서 검증된 값을 사용한다.

---

### 2. `_next_lcg()` — LCG 난수 생성기

```python
def _next_lcg(self):
    self._lcg_state = (
        self._lcg_a * self._lcg_state + self._lcg_c
    ) % self._lcg_m
    return self._lcg_state / self._lcg_m
```

LCG(Linear Congruential Generator) 알고리즘은 다음 점화식으로 난수를 생성한다.

```
X(n+1) = (a * X(n) + c) mod m
```

| 파라미터 | 값 | 역할 |
|----------|----|------|
| `a` (multiplier) | 1664525 | 현재 상태에 곱하는 값 |
| `c` (increment) | 1013904223 | 더하는 상수 |
| `m` (modulus) | 2³² | 결과값의 최대 범위 |

생성된 정수를 `m`으로 나눠 **0 이상 1 미만**의 실수로 정규화한다.

`random` 라이브러리 없이 표준 라이브러리만으로 균일한 난수를 얻기 위해 직접 구현하였다.

---

### 3. `_rand_range(lo, hi)` — 범위 내 난수 생성

```python
def _rand_range(self, lo, hi):
    return round(lo + self._next_lcg() * (hi - lo), 2)
```

0~1 사이 난수를 원하는 범위 `[lo, hi]`로 선형 변환한다.

```
결과 = lo + 난수(0~1) × (hi - lo)
```

`round(..., 2)`로 소수점 2자리까지만 반환한다.

---

### 4. `set_env()` — 환경값 설정

```python
def set_env(self):
    self.env_values['mars_base_internal_temperature'] = self._rand_range(18, 30)
    self.env_values['mars_base_external_temperature'] = self._rand_range(0, 21)
    self.env_values['mars_base_internal_humidity']    = self._rand_range(50, 60)
    self.env_values['mars_base_external_illuminance'] = self._rand_range(500, 715)
    self.env_values['mars_base_internal_co2']         = self._rand_range(0.02, 0.1)
    self.env_values['mars_base_internal_oxygen']      = self._rand_range(4, 7)
```

과제에서 명시한 범위에 맞춰 각 센서값을 난수로 채운다.

| 항목 | 범위 | 단위 |
|------|------|------|
| 내부 온도 | 18 ~ 30 | °C |
| 외부 온도 | 0 ~ 21 | °C |
| 내부 습도 | 50 ~ 60 | % |
| 외부 광량 | 500 ~ 715 | W/m² |
| 내부 CO₂ | 0.02 ~ 0.1 | % |
| 내부 산소 | 4 ~ 7 | % |

---

### 5. `_get_now_str()` — 현재 날짜시간 반환

```python
def _get_now_str(self):
    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S')
```

로그 기록에 사용할 현재 날짜시간을 `YYYY-MM-DD HH:MM:SS` 형식의 문자열로 반환한다.

---

### 6. `get_env()` — 환경값 반환 및 로그 기록 (보너스)

```python
def get_env(self):
    log_line = '{},{},{},{},{},{},{}\n'.format(
        self._get_now_str(),
        self.env_values['mars_base_internal_temperature'],
        ...
    )
    try:
        with open('mars_mission_computer.log', 'a', encoding='utf-8') as f:
            f.write(log_line)
    except FileNotFoundError as e:
        print('로그 파일을 찾을 수 없습니다:', e)
    except PermissionError as e:
        print('로그 파일 쓰기 권한이 없습니다:', e)
    except OSError as e:
        print('로그 파일 처리 중 OS 오류:', e)

    return self.env_values
```

- `env_values`를 반환하는 것이 기본 역할이다.
- 보너스 과제로, 반환 전에 로그 파일(`mars_mission_computer.log`)에 CSV 형식으로 한 줄을 추가(append) 기록한다.
- 파일 열기 모드 `'a'`는 파일이 없으면 자동 생성하고, 있으면 이어 쓴다.
- 파일 I/O에서 발생 가능한 예외를 종류별로 나누어 처리한다.

**로그 파일 포맷 예시:**
```
2026-04-02 14:23:05,22.08,20.12,56.03,537.20,0.06,4.73
```

---

### 7. 진입점 (`__name__ == '__main__'`)

```python
if __name__ == '__main__':
    ds = DummySensor()
    ds.set_env()
    print(ds.get_env())
```

- `DummySensor`를 `ds`라는 이름으로 인스턴스화한다.
- `set_env()`로 랜덤값을 채운 뒤, `get_env()`로 값을 반환·출력하고 로그를 기록한다.
- `if __name__ == '__main__'` 블록은 이 파일을 직접 실행할 때만 동작하며, 다른 파일에서 import할 경우에는 실행되지 않는다.

---

## 실행 결과 예시

```
{
  'mars_base_internal_temperature': 22.08,
  'mars_base_external_temperature': 20.12,
  'mars_base_internal_humidity': 56.03,
  'mars_base_external_illuminance': 537.2,
  'mars_base_internal_co2': 0.06,
  'mars_base_internal_oxygen': 4.73
}
```
