# Week 03 - 화성 기지 인화성 물질 분류

## 개요

화성 기지 폭발 사고 이후 기지 내 적재 물질 목록(`Mars_Base_Inventory_List.csv`)을 분석하여
인화성 위험 물질을 분류하고 격리 우선순위를 산정하는 프로그램 개발.

---

## 파일 구조

```
week03/
├── main.py                          # 메인 실행 파일
├── Mars_Base_Inventory_List.csv     # 원본 화물 목록
├── Mars_Base_Inventory_danger.csv   # 인화성 0.7 이상 위험 물질 목록 (생성)
└── Mars_Base_Inventory_List.bin     # 정렬된 전체 목록 이진 파일 (생성)
```

---

## CSV 데이터 구조

| 컬럼 | 설명 | 비고 |
|------|------|------|
| Substance | 물질명 | 문자열 |
| Weight (g/cm³) | 밀도 | 숫자 또는 `Various` |
| Specific Gravity | 비중 | 숫자 또는 `Various` |
| Strength | 강도 | 문자열 |
| Flammability | 인화성 지수 | 0.0 ~ 1.0 float |
| Danger Score | 복합 위험도 | 계산값 (프로그램에서 추가) |

> `Various`는 물질의 상태나 형태에 따라 값이 달라지는 경우에 사용된 표기.

---

## 핵심 로직

### 1. CSV 읽기 및 파싱 — `read_csv()`

```python
def read_csv(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader) + ['Danger Score']  # 헤더에 열 추가
        for row in reader:
            row[4] = float(row[4])                # Flammability → float 변환
            sg = parse_number(row[2])             # Specific Gravity 파싱 시도
            row.append(compute_danger_score(...)) # Danger Score 계산 후 추가
```

- 표준 라이브러리 `csv` 모듈 사용
- `Flammability` 변환 실패 시 해당 행 스킵 (`ValueError` 처리)
- 빈 행 자동 제거
- 헤더에 `Danger Score` 열을 추가해 반환

---

### 2. 숫자 파싱 — `parse_number()`

```python
def parse_number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
```

- `"Various"` → `None` 반환
- `"1.88"` → `1.88` 반환

---

### 3. 복합 위험도 계산 — `compute_danger_score()`

```python
def compute_danger_score(flammability, specific_gravity):
    sg = specific_gravity if specific_gravity is not None else 1.0
    return round(flammability * sg, 4)
```

**공식:** `Danger Score = Flammability × Specific Gravity`

| 조건 | 처리 |
|------|------|
| 비중이 숫자인 경우 | 인화성 × 비중 |
| 비중이 `Various`인 경우 | 인화성 × 1.0 (중립값) |

**의미:** 인화성이 같아도 밀도(비중)가 높을수록 단위 부피당 연료량이 많으므로 더 위험하다고 판단.

---

### 4. 정렬 — `sort_by_danger_score()`

```python
def sort_by_danger_score(data):
    return sorted(data, key=lambda x: x[5], reverse=True)
```

- `x[5]` = Danger Score (인덱스 5번째 열)
- `reverse=True` → 내림차순 (위험도 높은 순)
- `sorted()` 는 원본을 변경하지 않고 새 리스트 반환

---

### 5. 위험 물질 필터링 — `filter_danger()`

```python
def filter_danger(data, threshold=0.7):
    return [row for row in data if row[4] >= threshold]
```

- 리스트 컴프리헨션으로 간결하게 필터링
- `row[4]` = Flammability
- 기준값 `threshold=0.7` 은 파라미터로 분리해 변경 용이

---

### 6. CSV 저장 — `save_csv()`

```python
def save_csv(filename, header, data):
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)
```

- `newline=''` : Windows 환경에서 줄바꿈 중복 방지
- `writer.writerows()` : 리스트 전체를 한 번에 기록

---

## 보너스: 이진 파일 저장/읽기

### `save_bin()` / `load_bin()`

```python
import pickle

# 저장
with open(filename, 'wb') as f:
    pickle.dump(data, f)

# 읽기
with open(filename, 'rb') as f:
    data = pickle.load(f)
```

- `pickle` : Python 객체를 그대로 직렬화(serialize)하는 표준 라이브러리
- `'wb'` / `'rb'` : binary write / binary read 모드

---

## 텍스트 파일 vs 이진 파일

| 항목 | 텍스트 파일 (`.csv`) | 이진 파일 (`.bin`) |
|------|------|------|
| 가독성 | 사람이 직접 읽기 가능 | 읽을 수 없음 (바이트 나열) |
| 호환성 | 어느 언어/도구에서도 사용 가능 | Python + pickle에서만 복원 가능 |
| 파일 크기 | 상대적으로 큼 | 상대적으로 작음 |
| 저장 속도 | 느림 (인코딩 필요) | 빠름 (변환 없이 직렬화) |
| 데이터 타입 | 모두 문자열로 저장됨 | Python 타입 그대로 보존 (float, list 등) |
| 용도 | 데이터 공유, 장기 보관 | 동일 프로그램 내 빠른 임시 저장 |

> **결론:** CSV는 범용 공유에, `.bin`은 Python 프로그램 간 빠른 데이터 교환에 적합.

---

## 예외 처리 구조

모든 파일 I/O 함수에 아래 예외를 처리:

```python
except FileNotFoundError:
    print(f'오류: 파일을 찾을 수 없습니다 - {filename}')
except PermissionError:
    print(f'오류: 파일 접근 권한이 없습니다 - {filename}')
```

- `read_csv()` 추가: `ValueError` (Flammability 변환 실패 시 행 스킵)
- 예외 발생 시 `None` 반환 → `main()`에서 `if data is None: return` 으로 조기 종료

---

## 실행 결과 요약

### 위험 물질 상위 5개 (Danger Score 기준)

| 물질 | Flammability | Specific Gravity | Danger Score |
|------|------|------|------|
| Uranium | 0.92 | 19.05 | **17.526** |
| Tungsten | 0.14 | 19.25 | 2.695 |
| Propane | 0.78 | 1.88 | 1.4664 |
| Hydrogen Peroxide | 0.98 | 1.45 | 1.421 |
| Chloroform | 0.92 | 1.483 | 1.3644 |

> Uranium은 인화성 자체는 0.92로 최고가 아니지만, 비중 19.05로 인해 압도적인 위험도를 보임.
> 반면 Acetylene(인화성 0.95)은 기체라 비중이 0.0011으로 낮아 Danger Score는 0.001에 불과.
