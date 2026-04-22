import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, 
    QPushButton, QLabel, QLineEdit
)
from PyQt5.QtCore import Qt


class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.expression = []
        self.current_input = ''
        self.is_result = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Calculator')
        self.setStyleSheet('background-color: black;')
        self.setFixedSize(350, 520)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 15)
        
        self.expr_display = QLabel('')
        self.expr_display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.expr_display.setStyleSheet('color: #888888; border: none; background-color: black; font-size: 20px;')
        self.expr_display.setFixedHeight(30)
        layout.addWidget(self.expr_display)

        self.main_display = QLineEdit('0')
        self.main_display.setReadOnly(True)
        self.main_display.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.main_display.setStyleSheet('color: white; border: none; background-color: black; font-size: 45px;')
        self.main_display.setFixedHeight(60)
        layout.addWidget(self.main_display)
        
        grid = QGridLayout()
        grid.setSpacing(15)
        
        buttons = [
            ('AC', 0, 0, 1, 1), ('+/-', 0, 1, 1, 1), ('%', 0, 2, 1, 1), ('/', 0, 3, 1, 1),
            ('7', 1, 0, 1, 1), ('8', 1, 1, 1, 1), ('9', 1, 2, 1, 1), ('*', 1, 3, 1, 1),
            ('4', 2, 0, 1, 1), ('5', 2, 1, 1, 1), ('6', 2, 2, 1, 1), ('-', 2, 3, 1, 1),
            ('1', 3, 0, 1, 1), ('2', 3, 1, 1, 1), ('3', 3, 2, 1, 1), ('+', 3, 3, 1, 1),
            ('0', 4, 0, 1, 2), ('.', 4, 2, 1, 1), ('=', 4, 3, 1, 1)
        ]
        
        for text, row, col, row_span, col_span in buttons:
            btn = QPushButton(text)
            
            font = btn.font()
            font.setPointSize(24)
            if text in ['/', '*', '-', '+', '=']:
                font.setPointSize(30)
            btn.setFont(font)
            
            if text in ['AC', '+/-', '%']:
                bg_color = '#a5a5a5'
                color = 'black'
                pressed_color = '#d4d4d2'
            elif text in ['/', '*', '-', '+', '=']:
                bg_color = '#ff9f0a'
                color = 'white'
                pressed_color = '#fcc777'
            else:
                bg_color = '#333333'
                color = 'white'
                pressed_color = '#737373'
                
            extra_style = ''
            if text == '0':
                btn.setFixedSize(155, 70)
                extra_style = 'text-align: left; padding-left: 25px;'
            else:
                btn.setFixedSize(70, 70)
                
            style = f'''
                QPushButton {{
                    background-color: {bg_color};
                    color: {color};
                    border-radius: 35px;
                    {extra_style}
                }}
                QPushButton:pressed {{
                    background-color: {pressed_color};
                }}
            '''
            
            btn.setStyleSheet(style)
            btn.clicked.connect(self.on_click)
            grid.addWidget(btn, row, col, row_span, col_span)
            
        layout.addLayout(grid)
        self.setLayout(layout)

    def update_displays(self):
        display_text = ' '.join(self.expression)
        if self.current_input:
            display_text += (' ' if display_text else '') + self.current_input
            
        if not display_text:
            display_text = '0'
            
        self.main_display.setText(display_text)

    def on_click(self):
        sender = self.sender()
        text = sender.text()
        
        if text in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']:
            if self.is_result:
                self.expression = []
                self.current_input = ''
                self.expr_display.setText('')
                self.is_result = False
                
            if text == '.':
                if not self.current_input or self.current_input == '-':
                    self.current_input += '0.'
                elif '.' in self.current_input:
                    return
                else:
                    self.current_input += '.'
            else:
                if self.current_input == '0':
                    self.current_input = text
                elif self.current_input == '-0':
                    self.current_input = '-' + text
                else:
                    self.current_input += text
            self.update_displays()
            
        elif text == 'AC':
            self.expression = []
            self.current_input = ''
            self.is_result = False
            self.expr_display.setText('')
            self.update_displays()
            
        elif text in ['+', '-', '*', '/']:
            if self.is_result:
                self.expression = [self.current_input]
                self.current_input = ''
                self.is_result = False
                self.expr_display.setText('')
                
            if self.current_input:
                self.expression.append(self.current_input)
                self.expression.append(text)
                self.current_input = ''
            elif self.expression:
                if self.expression[-1] in ['+', '-', '*', '/']:
                    self.expression[-1] = text
            self.update_displays()
            
        elif text == '=':
            if not self.expression and not self.current_input:
                return
                
            if self.current_input:
                self.expression.append(self.current_input)
                self.current_input = ''
                
            if self.expression and self.expression[-1] in ['+', '-', '*', '/']:
                self.expression.pop()
                
            if not self.expression:
                return
                
            expr_str = ' '.join(self.expression)
            try:
                result = eval(expr_str)
                if isinstance(result, float) and result.is_integer():
                    result_str = str(int(result))
                else:
                    result_str = str(round(result, 8)).rstrip('0').rstrip('.') if '.' in str(result) else str(result)
                
                self.expr_display.setText(expr_str + ' =')
                self.main_display.setText(result_str)
                self.current_input = result_str
                self.expression = []
                self.is_result = True
                
            except ZeroDivisionError:
                self.main_display.setText('Error')
                self.expr_display.setText(expr_str + ' =')
                self.current_input = ''
                self.expression = []
                self.is_result = True
            except Exception:
                self.main_display.setText('Error')
                self.expr_display.setText(expr_str + ' =')
                self.current_input = ''
                self.expression = []
                self.is_result = True
            
        elif text == '+/-':
            if self.is_result:
                self.expr_display.setText('')
                self.is_result = False
                
            if not self.current_input or self.current_input == '0':
                self.current_input = '-0'
            elif self.current_input.startswith('-'):
                self.current_input = self.current_input[1:]
            else:
                self.current_input = '-' + self.current_input
            self.update_displays()
                
        elif text == '%':
            if self.is_result:
                self.expr_display.setText('')
                self.is_result = False
                
            if self.current_input and self.current_input not in ['-', '-0']:
                try:
                    val = float(self.current_input) / 100
                    if val.is_integer():
                        self.current_input = str(int(val))
                    else:
                        self.current_input = str(val)
                    self.update_displays()
                except ValueError:
                    pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calc = Calculator()
    calc.show()
    sys.exit(app.exec_())