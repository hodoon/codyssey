# 카이사르 암호 해독기

## 카이사르 암호란?

카이사르 암호(Caesar Cipher)는 기원전 1세기 율리우스 카이사르(Julius Caesar)가 군사 통신에 사용한 암호화 기법이다.  
원리는 단순하다. 알파벳을 일정한 수(shift)만큼 밀어서 다른 글자로 바꾸는 것이다.

```
평문:  A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
shift=3:
암호:  D E F G H I J K L M N O P Q R S T U V W X Y Z A B C
```

예를 들어 shift=3이면 `A → D`, `B → E`, `Z → C`처럼 치환된다.  
해독은 반대로 암호문에서 shift만큼 앞으로 돌리면 원문이 나온다.

```
암호문: D E F  →  평문: A B C  (shift=3으로 역방향)
```

알파벳은 26자이므로 가능한 shift 값은 1~26이고, shift=26은 원문과 동일하다.

---

## 이 미션에서 풀어야 했던 암호

```
암호문: B ehox Ftkl
```

shift를 1부터 26까지 대입해 보면 shift=19일 때 의미 있는 문장이 나온다.

| shift | 결과 |
|------:|------|
| 1 | A dgnw Esjk |
| 7 | U xahq Ymde |
| 19 | **I love Mars** |
| 26 | B ehox Ftkl |

**정답: shift 19 → `I love Mars`**

---

## 코드 구조

```
week11/
├── main.py           # 메인 프로그램
├── dictionary.txt    # 사전 단어 목록
└── result.txt        # 해독 결과 저장 파일
```

---

## 함수 설명

### `load_dictionary(file_path)`

`dictionary.txt` 파일을 읽어 단어를 `set`으로 반환한다.

```python
words = {line.strip().lower() for line in f if line.strip()}
```

- 각 줄을 소문자로 정규화해서 저장
- `set`을 사용하므로 단어 수가 많아도 `O(1)` 탐색 속도 유지
- 파일이 없어도 빈 `set`을 반환해 프로그램이 중단되지 않음

---

### `read_password_file(file_path)`

`password.txt`를 읽어 암호문 문자열을 반환한다.

- `FileNotFoundError`, `PermissionError`, `OSError`를 각각 구분해 처리
- 읽기 실패 시 `None` 반환

---

### `caesar_cipher_decode(target_text, shift)`

카이사르 암호 해독의 핵심 함수다.

```python
decoded = chr((ord(char) - base - shift) % 26 + base)
```

**동작 원리:**

1. `ord(char) - base` → 문자를 0~25 사이의 숫자로 변환  
   (A=0, B=1, ... Z=25 / a=0, b=1, ... z=25)
2. `- shift` → shift만큼 앞으로 이동 (해독 방향)
3. `% 26` → 음수가 되면 Z 쪽으로 순환 (예: -1 → 25 = Z)
4. `+ base` → 다시 ASCII 코드로 변환 후 `chr()`로 문자 복원

알파벳이 아닌 문자(공백, 숫자 등)는 그대로 유지한다.

**예시 (shift=19, 문자 `B`):**

```
ord('B') = 66
base     = 65  (대문자 기준)
(66 - 65 - 19) % 26 = (-18) % 26 = 8
chr(8 + 65) = chr(73) = 'I'
```

---

### `contains_dictionary_word(text, dictionary)`

해독된 텍스트의 단어가 사전에 있는지 확인한다.

```python
if len(word) >= 3 and word in dictionary:
```

- 3글자 미만 단어(`a`, `i` 등)는 제외해 오탐을 줄임
- 사전에 일치하는 단어가 있으면 `True` 반환 → 반복 자동 중단

---

### `save_result(text, file_path)`

해독된 최종 결과를 `result.txt`에 저장한다.

---

### `main()`

전체 흐름을 제어한다.

```
1. password.txt 읽기
2. dictionary.txt 읽기
3. shift 1~26 반복:
   a. caesar_cipher_decode()로 해독
   b. 결과 출력
   c. 사전 단어 탐지되면 → 자동 저장 후 중단
4. 사전 탐지 실패 시 → 사용자가 shift 번호 직접 입력 → 저장
```

---

## 보너스 과제: 사전 기반 자동 탐지

### 아이디어

카이사르 암호의 약점은 가능한 경우의 수가 1~26으로 매우 적다는 점이다.  
모든 경우를 출력해 눈으로 확인하는 것도 가능하지만, 의미 있는 영어 단어가 나왔을 때 자동으로 멈추게 하면 더 효율적이다.

이 아이디어를 구현한 것이 **사전 기반 자동 탐지**다.

---

### dictionary.txt

사전 단어를 코드 안에 하드코딩하는 대신 외부 파일로 분리했다.

```
week11/dictionary.txt
─────────────────────
the
love
mars
hello
world
space
mission
...
```

- 단어를 추가하거나 삭제할 때 코드를 수정하지 않아도 된다.
- 도메인에 맞는 단어(화성, 우주 관련)를 자유롭게 확장할 수 있다.

---

### `load_dictionary(file_path)`

파일을 읽어 `set`으로 반환하는 이유는 탐색 속도 때문이다.

| 자료구조 | 탐색 시간 복잡도 |
|:--------:|:----------------:|
| `list`   | O(n) — 단어 수에 비례 |
| `set`    | O(1) — 단어 수 무관 |

단어 수천 개짜리 사전을 써도 탐색 속도가 느려지지 않는다.

---

### `contains_dictionary_word(text, dictionary)`

해독된 텍스트를 공백 기준으로 단어로 분리한 뒤, 각 단어가 사전에 있는지 확인한다.

```python
def contains_dictionary_word(text, dictionary):
    lower_text = text.lower()
    words = lower_text.split()
    for word in words:
        if len(word) >= 3 and word in dictionary:
            return True
    return False
```

**3글자 미만을 제외하는 이유:**

shift 1만 적용해도 암호문 속 `B`가 `A`로 바뀌는데, `a`, `i` 같은 단일 문자도 사전에 올라있으면 오탐이 발생한다.  
3글자 이상 단어만 비교하면 `love`, `mars`처럼 의미 있는 단어가 나왔을 때만 탐지된다.

---

### 자동 탐지 흐름

```
shift  1 해독 → 사전 확인 → 없음 → 계속
shift  2 해독 → 사전 확인 → 없음 → 계속
...
shift 19 해독 → "I love Mars" → 'love', 'mars' 발견 → 중단 → result.txt 저장
```

사전 탐지에 성공하면 사용자 입력 없이 자동으로 저장된다.  
26번을 모두 돌아도 탐지 실패 시에는 사용자가 직접 shift 번호를 입력한다.

---

## 실행 결과

```
암호문: B ehox Ftkl
----------------------------------------
shift  1: A dgnw Esjk
shift  2: Z cfmv Drij
...
shift 19: I love Mars
  --> 사전 단어 발견! shift 19에서 자동 탐지됨
----------------------------------------
자동 탐지된 암호 해독 결과 (shift 19): I love Mars
결과가 저장되었습니다: result.txt
```
