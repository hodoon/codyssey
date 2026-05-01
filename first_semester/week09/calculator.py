import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLabel
)
from PyQt5.QtCore import Qt


MAX_VALUE = 1e15


class Calculator:
    '''계산기 핵심 로직 클래스'''

    def __init__(self):
        self.reset()

    def reset(self):
        '''계산기 상태를 초기화한다.'''
        self.display_value = '0'
        self.stored_value = None
        self.pending_op = None
        self.is_new_input = True
        self.is_error = False
        return self.display_value

    def input_digit(self, digit):
        '''숫자를 입력받아 현재 표시값에 누적한다.'''
        if self.is_error:
            self.reset()
        if self.is_new_input:
            self.display_value = digit
            self.is_new_input = False
        else:
            if self.display_value == '0':
                self.display_value = digit
            elif self.display_value == '-0':
                self.display_value = '-' + digit if digit != '0' else '-0'
            else:
                self.display_value += digit
        return self.display_value

    def input_dot(self):
        '''소수점을 입력한다. 이미 소수점이 있으면 무시한다.'''
        if self.is_error:
            return self.display_value
        if self.is_new_input:
            self.display_value = '0.'
            self.is_new_input = False
        elif '.' not in self.display_value:
            self.display_value += '.'
        return self.display_value

    def _to_float(self):
        '''현재 표시값을 float으로 변환한다.'''
        try:
            return float(self.display_value)
        except ValueError:
            return 0.0

    def _format_value(self, value):
        '''숫자를 표시 문자열로 변환한다. 소수점 6자리 이하 반올림.'''
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        rounded = round(value, 6)
        result = f'{rounded:.10f}'.rstrip('0').rstrip('.')
        return result

    def _compute(self, left, op, right):
        '''두 값에 연산자를 적용해 결과를 반환한다.'''
        if op == '+':
            result = left + right
        elif op == '-':
            result = left - right
        elif op == '*':
            result = left * right
        elif op == '/':
            if right == 0:
                raise ZeroDivisionError('0으로 나눌 수 없습니다')
            result = left / right
        else:
            raise ValueError(f'알 수 없는 연산자: {op}')

        if abs(result) > MAX_VALUE:
            raise OverflowError('처리할 수 있는 숫자의 범위를 초과했습니다')

        return result

    def _set_operator(self, op):
        '''연산자를 설정하고 필요 시 중간 계산을 수행한다.'''
        if self.is_error:
            return self.display_value

        if not self.is_new_input:
            current = self._to_float()
            if self.stored_value is not None and self.pending_op is not None:
                try:
                    self.stored_value = self._compute(
                        self.stored_value, self.pending_op, current
                    )
                except (ZeroDivisionError, OverflowError):
                    self.display_value = 'Error'
                    self.is_error = True
                    self.stored_value = None
                    self.pending_op = None
                    self.is_new_input = True
                    return self.display_value
            else:
                self.stored_value = current
        else:
            if self.stored_value is None:
                try:
                    self.stored_value = float(self.display_value)
                except ValueError:
                    pass

        self.pending_op = op
        self.is_new_input = True
        return self.display_value

    def add(self):
        '''덧셈 연산자를 설정한다.'''
        return self._set_operator('+')

    def subtract(self):
        '''뺄셈 연산자를 설정한다.'''
        return self._set_operator('-')

    def multiply(self):
        '''곱셈 연산자를 설정한다.'''
        return self._set_operator('*')

    def divide(self):
        '''나눗셈 연산자를 설정한다.'''
        return self._set_operator('/')

    def equal(self):
        '''현재 연산을 완료하고 결과를 반환한다.'''
        if self.is_error:
            return self.display_value
        if self.stored_value is None or self.pending_op is None or self.is_new_input:
            return self.display_value

        current = self._to_float()
        try:
            result = self._compute(self.stored_value, self.pending_op, current)
            self.display_value = self._format_value(result)
            self.stored_value = None
            self.pending_op = None
            self.is_new_input = True
        except (ZeroDivisionError, OverflowError):
            self.display_value = 'Error'
            self.is_error = True
            self.stored_value = None
            self.pending_op = None
            self.is_new_input = True

        return self.display_value

    def negative_positive(self):
        '''현재 값의 양수/음수를 전환한다.'''
        if self.is_error:
            return self.display_value
        if self.display_value.startswith('-'):
            self.display_value = self.display_value[1:]
        else:
            self.display_value = '-' + self.display_value
        return self.display_value

    def percent(self):
        '''현재 값을 100으로 나눈다.'''
        if self.is_error:
            return self.display_value
        try:
            val = float(self.display_value) / 100
            self.display_value = self._format_value(val)
        except ValueError:
            pass
        return self.display_value

    def get_intermediate_result(self):
        '''연쇄 계산 후 중간 결과 문자열을 반환한다.'''
        if self.stored_value is not None:
            return self._format_value(self.stored_value)
        return self.display_value


class CalculatorApp(QWidget):
    '''계산기 UI 클래스'''

    OP_METHODS = {
        '+': 'add',
        '-': 'subtract',
        '*': 'multiply',
        '/': 'divide',
    }

    def __init__(self):
        super().__init__()
        self.calc = Calculator()
        self.expr_tokens = []
        self.is_after_result = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Calculator')
        self.setStyleSheet('background-color: black;')
        self.setFixedSize(350, 530)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 15)

        self.expr_label = QLabel('')
        self.expr_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.expr_label.setStyleSheet(
            'color: #888888; border: none; background-color: black; font-size: 20px;'
        )
        self.expr_label.setFixedHeight(30)
        layout.addWidget(self.expr_label)

        self.main_label = QLabel('0')
        self.main_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.main_label.setStyleSheet(
            'color: white; border: none; background-color: black; font-size: 70px;'
        )
        self.main_label.setFixedHeight(90)
        layout.addWidget(self.main_label)

        grid = QGridLayout()
        grid.setSpacing(15)

        buttons = [
            ('AC',  0, 0, 1, 1), ('+/-', 0, 1, 1, 1), ('%', 0, 2, 1, 1), ('/', 0, 3, 1, 1),
            ('7',   1, 0, 1, 1), ('8',   1, 1, 1, 1), ('9', 1, 2, 1, 1), ('*', 1, 3, 1, 1),
            ('4',   2, 0, 1, 1), ('5',   2, 1, 1, 1), ('6', 2, 2, 1, 1), ('-', 2, 3, 1, 1),
            ('1',   3, 0, 1, 1), ('2',   3, 1, 1, 1), ('3', 3, 2, 1, 1), ('+', 3, 3, 1, 1),
            ('0',   4, 0, 1, 2), ('.',   4, 2, 1, 1), ('=', 4, 3, 1, 1),
        ]

        for text, row, col, row_span, col_span in buttons:
            btn = QPushButton(text)

            font = btn.font()
            font.setPointSize(24)
            if text in ['/', '*', '-', '+', '=']:
                font.setPointSize(30)
            btn.setFont(font)

            if text in ['AC', '+/-', '%']:
                bg_color, color, pressed_color = '#a5a5a5', 'black', '#d4d4d2'
            elif text in ['/', '*', '-', '+', '=']:
                bg_color, color, pressed_color = '#ff9f0a', 'white', '#fcc777'
            else:
                bg_color, color, pressed_color = '#333333', 'white', '#737373'

            extra_style = ''
            if text == '0':
                btn.setFixedSize(155, 70)
                extra_style = 'text-align: left; padding-left: 25px;'
            else:
                btn.setFixedSize(70, 70)

            btn.setStyleSheet(f'''
                QPushButton {{
                    background-color: {bg_color};
                    color: {color};
                    border-radius: 35px;
                    {extra_style}
                }}
                QPushButton:pressed {{
                    background-color: {pressed_color};
                }}
            ''')
            btn.clicked.connect(self.on_click)
            grid.addWidget(btn, row, col, row_span, col_span)

        layout.addLayout(grid)
        self.setLayout(layout)

    def _adjust_font_size(self, text):
        '''텍스트 길이에 따라 적절한 폰트 크기를 반환한다.'''
        length = len(text)
        if length <= 6:
            return 70
        elif length <= 9:
            return 55
        elif length <= 12:
            return 42
        elif length <= 15:
            return 32
        else:
            return 24

    def update_main(self, text):
        '''메인 디스플레이를 업데이트하고 폰트 크기를 조정한다.'''
        font_size = self._adjust_font_size(text)
        self.main_label.setStyleSheet(
            f'color: white; border: none; background-color: black; font-size: {font_size}px;'
        )
        self.main_label.setText(text)

    def on_click(self):
        sender = self.sender()
        text = sender.text()

        if text.isdigit():
            if self.is_after_result:
                self.expr_tokens = []
                self.is_after_result = False
            result = self.calc.input_digit(text)
            self.update_main(result)

        elif text == '.':
            if self.is_after_result:
                self.expr_tokens = []
                self.is_after_result = False
            result = self.calc.input_dot()
            self.update_main(result)

        elif text == 'AC':
            self.calc.reset()
            self.expr_tokens = []
            self.is_after_result = False
            self.expr_label.setText('')
            self.update_main('0')

        elif text in self.OP_METHODS:
            self._handle_operator(text)

        elif text == '=':
            self._handle_equal()

        elif text == '+/-':
            result = self.calc.negative_positive()
            self.update_main(result)
            if self.is_after_result:
                self.is_after_result = False

        elif text == '%':
            result = self.calc.percent()
            self.update_main(result)
            if self.is_after_result:
                self.is_after_result = False

    def _handle_operator(self, op):
        '''연산자 버튼 처리: 중간 계산 수행 및 수식 표시 업데이트'''
        was_new_input = self.calc.is_new_input
        had_chain = (
            self.calc.stored_value is not None
            and self.calc.pending_op is not None
            and not was_new_input
        )
        current_before = self.calc.display_value

        method = getattr(self.calc, self.OP_METHODS[op])
        result = method()

        if result == 'Error':
            self.update_main('Error')
            self.expr_label.setText('')
            self.expr_tokens = []
            self.is_after_result = True
            return

        if was_new_input and self.expr_tokens:
            self.expr_tokens[-1] = op
        elif had_chain:
            intermediate = self.calc.get_intermediate_result()
            self.expr_tokens = [intermediate, op]
        else:
            if self.is_after_result:
                self.is_after_result = False
            self.expr_tokens = [current_before, op]

        self.expr_label.setText(' '.join(self.expr_tokens))

    def _handle_equal(self):
        '''= 버튼 처리: 최종 계산 수행 및 수식 표시'''
        if self.calc.pending_op is None or self.calc.is_new_input:
            return

        current_display = self.calc.display_value
        expr_text = ' '.join(self.expr_tokens) + ' ' + current_display + ' ='

        result = self.calc.equal()
        self.expr_label.setText(expr_text)
        self.update_main(result)
        self.expr_tokens = []
        self.is_after_result = True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calc = CalculatorApp()
    calc.show()
    sys.exit(app.exec_())
