import sys
from filelock import FileLock
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import QPoint
from pyautogui import click, doubleClick, dragTo
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import QRectF, Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont, QPixmap, QTransform
from os import path
from json import load

SETTINGS_FILE_PATH = path.join(path.dirname(sys.executable) if getattr(sys, 'frozen', False) else path.dirname(__file__)) + '/settings.json'

class OpenMouseless(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouseless")
        self.alphabet = list(map(chr, range(65, 65 + 26)))
        self.numbers = "01234"

        self.keyboard_layout = [
            ['q', 'w', 'e', 'r', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'j', 'k', 'l', ';'],
            ['z', 'x', 'c', 'v', 'm', ',', '.', '?']
        ]
        self.inner_cols = len(self.keyboard_layout[0])
        self.inner_rows = len(self.keyboard_layout)
        
        self.buffer_pixmap = None
        self.flash_timer = None
        self.cell_width = 0
        self.cell_height = 0
        self._setup_window()
        self.flash_label = None
        self.reset_selection()
        self.create_static_texts()
        QTimer.singleShot(0, self.post_init_optimizations)
        QTimer.singleShot(0, self.load_settings_async)

    def load_settings_async(self):
        try:
            with open(SETTINGS_FILE_PATH, 'r') as file:
                settings = load(file)
            language = settings.get("language", "EN")
            
            self.keyboard_layout[1][-1] = 'ç' if "BR" in language else ';'
            self.keyboard_layout[2][-1] = ';' if "BR" in language else '?'
            self.keyboard_positions = self._create_keyboard_map()
        except Exception as e:
            print("Erro ao carregar configurações:", e)

    def post_init_optimizations(self):
        self._update_buffer()
        self.update()

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen.width(), screen.height())

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
        self.cell_width = self.width() / 26
        self.cell_height = self.height() / 26
        self.update_grid_lines()
        self._update_buffer()  

    def create_static_texts(self):
        from PyQt5.QtGui import QStaticText
        self.static_texts = [QStaticText(letter) for letter in self.alphabet]
        for static_text in self.static_texts:
            static_text.prepare(QTransform(), QFont('Arial', 14, QFont.Bold))

    def update_grid_lines(self):
        self.vertical_lines = [(int(i * self.cell_width), 0, int(i * self.cell_width), self.height()) for i in range(27)]
        self.horizontal_lines = [(0, int(i * self.cell_height), self.width(), int(i * self.cell_height)) for i in range(27)]

    def _update_buffer(self):
        """Atualiza o buffer usando linhas para melhor performance"""
        self.buffer_pixmap = QPixmap(self.size())
        self.buffer_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self.buffer_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        line_color = QColor(255, 255, 255, 50)
        painter.setPen(line_color)
        for line in self.vertical_lines:
            painter.drawLine(*line)
        for line in self.horizontal_lines:
            painter.drawLine(*line)

        
        sub_line_color = QColor(0, 0, 0, 25)
        painter.setPen(sub_line_color)

        cell_width_over_inner_cols = self.cell_width / self.inner_cols
        cell_height_over_inner_rows = self.cell_height / self.inner_rows
        
        
        for col in range(26):
            for i in range(1, self.inner_cols):
                x = col * self.cell_width + i * cell_width_over_inner_cols
                painter.drawLine(int(x), 0, int(x), self.height())
        
        
        for row in range(26):
            for j in range(1, self.inner_rows):
                y = row * self.cell_height + j * cell_height_over_inner_rows
                painter.drawLine(0, int(y), self.width(), int(y))

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

    def precompute_letter_positions(self):
        self.letter_positions = []
        cell_text_offset = self.cell_height / 5  
        for row in range(26):
            for col in range(26):
                x = col * self.cell_width
                y = row * self.cell_height + cell_text_offset
                self.letter_positions.append((x, y))

    def _draw_main_letters(self, painter):
        painter.setFont(QFont('Arial', 14, QFont.Bold))
        painter.setPen(QColor(255, 255, 255, 150))
        
        if not hasattr(self, 'letter_positions'):
            self.precompute_letter_positions()
        
        for index, (x, y) in enumerate(self.letter_positions):
            letter1 = self.alphabet[index // 26]
            letter2 = self.alphabet[index % 26]
            painter.drawText(QRectF(x, y, self.cell_width/2, self.cell_height/2), Qt.AlignCenter, letter1)
            painter.drawText(QRectF(x + self.cell_width/2, y, self.cell_width/2, self.cell_height/2), Qt.AlignCenter, letter2)

    def _draw_subgrid(self, painter):
        cell_x = self.selected_col * self.cell_width
        cell_y = self.selected_row * self.cell_height
        
        painter.setFont(QFont('Arial', 10))
        painter.setPen(QColor(255, 255, 255, 200))

        cols_size = self.cell_width / self.inner_cols
        rows_size = self.cell_height / self.inner_rows
        
        for sub_row in range(self.inner_rows):
            for sub_col in range(self.inner_cols):
                try:
                    char = self.keyboard_layout[sub_row][sub_col]
                    x = cell_x + sub_col * cols_size
                    y = cell_y + sub_row * rows_size
                    painter.drawText(QRectF(x, y, cols_size, rows_size), 
                                   Qt.AlignCenter, char.upper())
                except IndexError:
                    pass

    def show_flash_message(self):
        if self.flash_label is None:
            self._init_flash_label()
        actions_text = ["Click", "Right click", "Double click", "Triple click", "Hold"]
        message = actions_text[self.action]
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
        self.action = 0
        self.hold = False
    
    def get_letter_code(self, letter):
        return ord(letter.upper()) - 65

    def handle_first_two_letters(self, event):
        key = event.text().upper()
        if key in self.numbers and not self.hold:
            try:
                self.action = int(key)
            except ValueError:
                return
            self.show_flash_message()
            return
        if key not in self.alphabet:
            return

        if not self.letter1:
            self.letter1 = key
            return
        if not self.letter2:
            self.letter2 = key
            self.selected_row = self.get_letter_code(self.letter1)
            self.selected_col = self.get_letter_code(self.letter2)

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
        cell_width = self.width() / 26
        cell_height = self.height() / 26
        
        x = (self.selected_col * cell_width) + (sub_col * (cell_width / self.inner_cols)) + (cell_width / (2 * self.inner_cols))
        y = (self.selected_row * cell_height) + (sub_row * (cell_height / self.inner_rows)) + (cell_height / (2 * self.inner_rows))
        
        global_pos = self.mapToGlobal(QPoint(int(x), int(y)))
        if self.hold:
            self.hide()
            dragTo(global_pos.x(), global_pos.y())
        else:
            QCursor.setPos(global_pos)
            if self.action == 4:
                self.reset_selection()
                self.hold = True
                return
            self.hide()
            functions = [
                (click, {}), 
                (click, {"button":'right'}),
                (doubleClick, {}),
                (click, {"clicks": 3})
            ]
            function, args = functions[self.action]
            function(**args)
        QApplication.quit()

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    lock_file = ".open_mouseless.lock"

    lock = FileLock(lock_file)
    try:
        lock.acquire(timeout=0)
    except Exception:
        sys.exit()
    app = QApplication(sys.argv)
    overlay = OpenMouseless()
    overlay.show()
    sys.exit(app.exec_())
