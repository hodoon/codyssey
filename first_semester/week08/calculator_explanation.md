# PyQt5 아이폰 스타일 계산기 코드 분석

이 문서는 `calculator.py`에 구현된 파이썬 PyQt5 기반의 계산기 코드 동작 방식을 상세히 설명합니다. 이 계산기는 아이폰의 기본 계산기 UI를 모방하였으며, 사용자가 입력하는 연산 과정이 하단 화면에 누적되다가 `=` 버튼을 누르는 순간 상단 화면으로 이동하며 결과가 출력되는 특징을 가지고 있습니다.

## 1. 모듈 임포트 및 초기 설정

```python
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, 
    QPushButton, QLabel, QLineEdit
)
from PyQt5.QtCore import Qt
```
- **sys**: 파이썬 인터프리터와 상호작용하기 위해 사용되며, 프로그램 종료(`sys.exit`) 등에 필요합니다.
- **PyQt5.QtWidgets**: GUI 애플리케이션을 구성하는 핵심 위젯들(창, 레이아웃, 버튼, 라벨, 입력창 등)을 가져옵니다.
- **PyQt5.QtCore**: 정렬(`Qt.AlignRight` 등)과 같은 핵심 상수와 기능들을 제공합니다.

## 2. Calculator 클래스 구조

```python
class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.expression = []       # 입력된 숫자와 연산자를 순서대로 저장하는 리스트
        self.current_input = ''    # 현재 사용자가 입력 중인 숫자 (문자열)
        self.is_result = False     # 화면에 표시된 값이 최종 계산 결과인지 확인하는 플래그
        self.init_ui()             # UI 초기화 메서드 호출
```
`Calculator` 클래스는 기본 창 역할을 하는 `QWidget`을 상속받습니다. `__init__` 메서드에서는 계산 상태를 관리하기 위한 주요 변수들을 초기화하고 UI를 구성하는 `init_ui`를 호출합니다.

## 3. UI 구성 (`init_ui` 메서드)

이 메서드는 계산기의 껍데기(모양, 색상, 버튼 배치)를 만듭니다.

### 3.1 창 설정 및 레이아웃
```python
self.setWindowTitle('Calculator')
self.setStyleSheet('background-color: black;')
self.setFixedSize(350, 520)
        
layout = QVBoxLayout() # 수직으로 위젯을 쌓는 레이아웃
layout.setContentsMargins(15, 20, 15, 15)
```
배경을 검은색으로 지정하고 창 크기를 고정합니다. 메인 레이아웃으로는 위에서 아래로 요소들을 배치하는 `QVBoxLayout`을 사용합니다.

### 3.2 디스플레이 영역 (화면)
계산기 화면은 상단의 **수식 표시 영역(회색)**과 하단의 **메인 표시 영역(흰색)** 두 가지로 나뉩니다.

```python
# 상단: = 누르기 전의 전체 수식 또는 누른 후의 이전 수식을 보여주는 라벨
self.expr_display = QLabel('')
self.expr_display.setStyleSheet('color: #888888; ... font-size: 20px;')

# 하단: 현재 입력 중인 수식 또는 최종 결과값을 보여주는 텍스트 박스
self.main_display = QLineEdit('0')
self.main_display.setReadOnly(True) # 사용자 직접 타이핑 방지
self.main_display.setStyleSheet('color: white; ... font-size: 45px;')
```

### 3.3 버튼 그리드 배치
```python
grid = QGridLayout() # 격자 형태의 레이아웃
grid.setSpacing(15)
```
버튼들은 `QGridLayout`을 사용하여 엑셀 표처럼 줄과 칸을 맞추어 배치합니다.
각 버튼은 `('텍스트', 행_위치, 열_위치, 차지하는_행_수, 차지하는_열_수)` 형태의 리스트로 정의하여 반복문(`for`)을 통해 간결하게 생성합니다. (예: `0` 버튼은 가로로 2칸을 차지하도록 설정됨)

### 3.4 버튼 스타일링 및 이벤트 연결
아이폰 계산기와 유사한 색상을 주기 위해 텍스트 내용에 따라 3가지 색상(진한 회색, 주황색, 옅은 회색)으로 분기하여 CSS 스타일(`setStyleSheet`)을 입힙니다.
모든 버튼은 클릭되었을 때 `self.on_click` 메서드가 실행되도록 연결(`clicked.connect`)됩니다.

## 4. 디스플레이 업데이트 (`update_displays` 메서드)

```python
def update_displays(self):
    display_text = ' '.join(self.expression)
    if self.current_input:
        display_text += (' ' if display_text else '') + self.current_input
        
    if not display_text:
        display_text = '0'
        
    self.main_display.setText(display_text)
```
이 메서드는 `=` 버튼을 누르기 전까지, 하단 메인 화면(흰색 영역)에 `12 + 34 - 5`와 같이 현재까지 입력된 전체 수식을 누적해서 보여주는 역할을 합니다. 누적된 리스트(`self.expression`)와 현재 입력 중인 숫자(`self.current_input`)를 공백으로 이어붙여 화면에 출력합니다.

## 5. 클릭 이벤트 처리 (`on_click` 메서드)

사용자가 누른 버튼의 텍스트에 따라 분기하여 연산을 처리하는 핵심 로직입니다.

### 5.1 숫자 및 소수점 입력 (`0~9`, `.`)
- 숫자를 누르면 `current_input` 문자열 뒤에 계속 이어 붙입니다.
- 단, 방금 전 연산이 끝난 상태(`is_result == True`)에서 숫자를 누르면 이전 기록을 모두 지우고 새로 입력을 시작합니다.
- 소수점(`.`)은 하나의 숫자에 한 번만 입력되도록 방어 로직이 적용되어 있습니다.

### 5.2 초기화 (`AC`)
모든 변수(`expression`, `current_input`, `is_result`)를 초기화하고 상단과 하단 디스플레이를 모두 비우거나 `0`으로 되돌립니다.

### 5.3 사칙 연산자 (`+`, `-`, `*`, `/`)
- 숫자가 입력된 상태에서 연산자를 누르면, 현재 숫자를 `expression` 리스트에 담고 연산자도 리스트에 추가합니다.
- 연산자를 연속으로 누를 경우, 마지막으로 입력된 연산자를 새 연산자로 덮어씌웁니다.
- 위 작업 후 `update_displays()`를 호출하여 하단 메인 화면에 수식이 이어지도록 합니다.

### 5.4 부호 변경 (`+/-`) 및 백분율 (`%`)
- `+/-`: 현재 입력된 숫자(`current_input`)의 맨 앞에 `-` 기호를 붙이거나 제거합니다.
- `%`: 현재 입력된 숫자를 100으로 나눈 값으로 변경합니다.

### 5.5 연산 실행 (`=`)
1. 마지막으로 입력된 숫자를 `expression` 리스트에 추가합니다.
2. 수식의 맨 끝이 연산자로 끝난 경우(예: `12 + `), 불필요한 연산자를 제거합니다.
3. 리스트에 모인 전체 수식을 문자열로 결합합니다. (예: `'12 + 34 * 5'`)
4. 파이썬의 내장 함수인 **`eval()`**을 사용하여 수식 문자열을 한 번에 계산합니다.
5. 계산이 성공하면:
   - 계산된 전체 수식(예: `12 + 34 =`)을 **상단 회색 디스플레이(`expr_display`)**로 이동시킵니다.
   - 계산된 최종 결과값만 **하단 메인 디스플레이(`main_display`)**에 띄웁니다.
6. 0으로 나누거나(`ZeroDivisionError`) 잘못된 수식이 들어간 경우 화면에 `Error`를 출력합니다.

## 6. 실행부

```python
if __name__ == '__main__':
    app = QApplication(sys.argv)
    calc = Calculator()
    calc.show()
    sys.exit(app.exec_())
```
스크립트가 직접 실행될 때 PyQt5 애플리케이션 객체를 생성하고, 위에서 정의한 `Calculator` 창을 화면에 띄운 뒤 메인 이벤트 루프(`exec_()`)를 실행하여 프로그램이 종료되지 않고 입력을 대기하도록 합니다.
