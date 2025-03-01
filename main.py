import sys
from pyautogui import click, doubleClick, dragTo
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont, QCursor, QPixmap

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouseless")
        self.alphabet = {key: value for value, key in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
        self.numbers = "01234"
        self.functions = {
            "0": (click, {}), 
            "1": (click, {"button":'right'}),
            "2": (doubleClick, {}),
            "3": (click, {"clicks": 3})
        }
        self.actions_text = {
            "0": "Click",
            "1": "Right click",
            "2": "Double click",
            "3": "Triple click",
            "4": "Hold"
        }
        
        self.keyboard_layout = [
            ['q', 'w', 'e', 'r', 't', 'y', 'u'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j'],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm']
        ]
        self.keyboard_positions = self._create_keyboard_map()
        
        self.buffer_pixmap = None
        self.flash_timer = None
        self.cell_width = 0
        self.cell_height = 0
        
        self._setup_window()
        self._init_flash_label()
        self.reset_selection()

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        screen = QApplication.primaryScreen()
        self.setGeometry(0, 0, screen.size().width() + int(0.21/100 * screen.size().width()), screen.size().height())

    def _create_keyboard_map(self):
        return {char: (sub_row, sub_col) 
                for sub_row, row in enumerate(self.keyboard_layout) 
                for sub_col, char in enumerate(row)}

    def _init_flash_label(self):
        self.flash_label = QLabel(self)
        self.flash_label.setStyleSheet("""
            color: white; 
            font-size: 24px; 
            font-weight: bold; 
            background-color: rgba(0, 0, 0, 150); 
            padding: 10px; 
            border-radius: 10px;
        """)
        self.flash_label.setAlignment(Qt.AlignCenter)
        self.flash_label.hide()

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        self.cell_width = self.width() // 26
        self.cell_height = self.height() // 26
        self._update_buffer()

    def _update_buffer(self):
        """Atualiza o buffer apenas com elementos estruturais"""
        self.buffer_pixmap = QPixmap(self.size())
        self.buffer_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self.buffer_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        square_color = QColor(0, 0, 0, 25)
        border_color = QColor(255, 255, 255, 25)
        
        for row in range(26):
            for col in range(26):
                x = col * self.cell_width
                y = row * self.cell_height
                
                painter.setPen(border_color)
                painter.drawRect(x, y, self.cell_width, self.cell_height)
                
                inner_square_width = self.cell_width // 7
                inner_square_height = self.cell_height // 3
                for i in range(7):
                    for j in range(3):
                        painter.setBrush(QBrush(square_color))
                        painter.drawRect(
                            x + i * inner_square_width,
                            y + j * inner_square_height,
                            inner_square_width,
                            inner_square_height
                        )
        painter.end()

    def paintEvent(self, a0):
        painter = QPainter(self)
        if self.buffer_pixmap:
            painter.drawPixmap(0, 0, self.buffer_pixmap)
        
        if self.selected_row == -1:
            self._draw_main_letters(painter)
        else:
            self._draw_subgrid(painter)
        
        painter.end()

    def _draw_main_letters(self, painter):
        painter.setFont(QFont('Arial', 14, QFont.Bold))
        painter.setPen(QColor(255, 255, 255, 150))
        alphabet = list(self.alphabet.keys())
        
        for row in range(26):
            for col in range(26):
                x = col * self.cell_width
                y = row * self.cell_height
                
                painter.drawText(
                    QRect(x, y + self.cell_height//5, self.cell_width//2, self.cell_height//2),
                    Qt.AlignCenter, alphabet[row]
                )
                painter.drawText(
                    QRect(x + self.cell_width//2, y + self.cell_height//5, self.cell_width//2, self.cell_height//2),
                    Qt.AlignCenter, alphabet[col]
                )

    def _draw_subgrid(self, painter):
        cell_x = self.selected_col * self.cell_width
        cell_y = self.selected_row * self.cell_height
        
        painter.setFont(QFont('Arial', 10))
        painter.setPen(QColor(255, 255, 255, 200))
        
        for sub_row in range(3):
            for sub_col in range(7):
                try:
                    char = self.keyboard_layout[sub_row][sub_col]
                    x = cell_x + sub_col * (self.cell_width // 7)
                    y = cell_y + sub_row * (self.cell_height // 3)
                    painter.drawText(QRect(x, y, self.cell_width//7, self.cell_height//3), 
                                   Qt.AlignCenter, char.upper())
                except IndexError:
                    pass

    def show_flash_message(self, message):
        self.flash_label.setText(message)
        self.flash_label.adjustSize()
        self.flash_label.move(
            self.width()//2 - self.flash_label.width()//2,
            self.height()//2 - self.flash_label.height()//2
        )
        self.flash_label.show()

        if self.flash_timer:
            self.flash_timer.stop()
            self.flash_timer.deleteLater()
        
        self.flash_timer = QTimer(self)
        self.flash_timer.setSingleShot(True)
        self.flash_timer.timeout.connect(self._hide_flash_message)
        self.flash_timer.start(1500)

    def _hide_flash_message(self):
        self.flash_label.hide()
        self.flash_timer = None

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key_Escape:
            if self.letter1 == "":
                QApplication.quit()
            self.reset_selection()
            self.update()
            return

        if self.selected_row == -1:
            self.handle_first_two_letters(a0)
        else:
            self.handle_third_letter(a0)

        self.update()

    def reset_selection(self):
        self.letter1 = ""
        self.letter2 = ""
        self.letter3 = ""
        self.selected_row = -1
        self.selected_col = -1
        self.action = "0"
        self.hold = False

    def handle_first_two_letters(self, event):
        key = event.text().upper()
        if key in self.numbers and not self.hold:
            self.action = key
            self.show_flash_message(self.actions_text[self.action])
            return
        if key not in self.alphabet.keys():
            return

        if not self.letter1:
            self.letter1 = key
            return
        if not self.letter2:
            self.letter2 = key
            self.selected_row = self.alphabet[self.letter1]
            self.selected_col = self.alphabet[self.letter2]

    def get_third_letter(self, event):
        if event.key() == Qt.Key_Space:
            self.letter3 = 'f'
            return
        key = event.text().lower()
        valid_letters = self.keyboard_positions.keys()
        if key in valid_letters:
            self.letter3 = key

    def handle_third_letter(self, event):
        self.get_third_letter(event)
        if self.letter3:
            self.move_mouse_to_subcell()

    def move_mouse_to_subcell(self):
        if self.letter3 not in self.keyboard_positions:
            return
            
        sub_row, sub_col = self.keyboard_positions[self.letter3]
        cell_width = self.width() // 26
        cell_height = self.height() // 26
        
        x = (self.selected_col * cell_width) + (sub_col * (cell_width // 7)) + (cell_width // 14)
        y = (self.selected_row * cell_height) + (sub_row * (cell_height // 3)) + (cell_height // 6)
        
        global_pos = self.mapToGlobal(QPoint(x, y))
        if self.hold:
            self.hide()
            dragTo(global_pos.x(), global_pos.y())
        else:
            QCursor.setPos(global_pos)
            if self.action == "4":
                self.reset_selection()
                self.hold = True
                return
            self.hide()
            function, args = self.functions[self.action]
            function(**args)
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    overlay.show()
    sys.exit(app.exec_())
