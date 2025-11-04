import sys
from filelock import FileLock
from pyautogui import click, doubleClick, dragTo
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QWidget, QLabel, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QPoint, QRectF, Qt, QTimer, QAbstractNativeEventFilter, QAbstractEventDispatcher
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont, QCursor, QPixmap, QIcon
from pyqtkeybind import keybinder
from os import path
from json import load

FILE_PATH = path.join(path.dirname(sys.executable) if getattr(sys, 'frozen', False) else path.dirname(__file__))
SETTINGS_FILE_PATH = FILE_PATH + '/settings.json'
IMAGE_FILE_PATH = FILE_PATH + '/assets/mouse-cursor.jpg'
TITLE = "OpenMouseless"
with open(SETTINGS_FILE_PATH, 'r') as file:
    settings = load(file)

class OpenMouseless(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(TITLE)
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

        self.tray_icon = QSystemTrayIcon(QIcon(IMAGE_FILE_PATH), self)
        self.tray_icon.setToolTip(TITLE)

        menu = QMenu()

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.show)
        menu.addAction(open_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        language = settings.get("language", "EN")    

        self.keyboard_layout = [
            ['q', 'w', 'e', 'r', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'j', 'k', 'l', ('ç' if "BR" in language else ';')],
            ['z', 'x', 'c', 'v', 'm', ',', '.', (';' if "BR" in language else '?')]
        ]
        self.inner_cols = len(self.keyboard_layout[0])
        self.inner_rows = len(self.keyboard_layout)
        self.keyboard_positions = self._create_keyboard_map()
        
        self.buffer_pixmap = None
        self.flash_timer = None
        self.cell_width = 0
        self.cell_height = 0
        
        self._setup_window()
        self._init_flash_label()
        self.reset_selection()

    def show(self):
        self._setup_window_position()
        super().show()

    def _setup_window_position(self):
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, screen.width(), screen.height())

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._setup_window_position()

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
        self._update_buffer()

    def _update_buffer(self):
        """Atualiza o buffer apenas com elementos estruturais"""
        self.buffer_pixmap = QPixmap(self.size())
        self.buffer_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self.buffer_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        square_color = QColor(0, 0, 0, 25)
        border_color = QColor(255, 255, 255, 25)

        inner_square_width = self.cell_width / self.inner_cols
        inner_square_height = self.cell_height / self.inner_rows
        
        for row in range(26):
            for col in range(26):
                x = col * self.cell_width
                y = row * self.cell_height
                
                painter.setPen(border_color)
                cell_rect = QRectF(x, y, self.cell_width, self.cell_height)
                painter.drawRect(cell_rect)
                
                for i in range(self.inner_cols):
                    for j in range(self.inner_rows):
                        painter.setBrush(QBrush(square_color))
                        inner_rect = QRectF(x + i * inner_square_width, y + j * inner_square_height, inner_square_width, inner_square_height)
                        painter.drawRect(inner_rect)
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

        cell_height_over_5 = self.cell_height/5
        half_of_cell_width = self.cell_width/2
        half_of_cell_height = self.cell_height/2
        
        for row in range(26):
            for col in range(26):
                x = col * self.cell_width
                y = row * self.cell_height
                
                painter.drawText(
                    QRectF(x, y + cell_height_over_5, half_of_cell_width, half_of_cell_height),
                    Qt.AlignCenter, alphabet[row]
                )
                painter.drawText(
                    QRectF(x + half_of_cell_width, y + cell_height_over_5, half_of_cell_width, half_of_cell_height),
                    Qt.AlignCenter, alphabet[col]
                )

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
                self.hide()
            self.reset_selection()
            self.update()
            return
        if a0.key() == Qt.Key_Return:
            self.hide()
            click()

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
            actions_text = self.actions_text.get(self.action)
            if not actions_text:
                return
            self.show_flash_message(actions_text)
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
            if self.action == "4":
                self.reset_selection()
                self.hold = True
                return
            self.hide()
            function, args = self.functions[self.action]
            function(**args)
        self.reset_selection()

class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0

class EventDispatcher:
    """Install a native event filter to receive events from the OS"""

    def __init__(self, keybinder) -> None:
        self.win_event_filter = WinEventFilter(keybinder)
        self.event_dispatcher = QAbstractEventDispatcher.instance()
        self.event_dispatcher.installNativeEventFilter(self.win_event_filter)

class QtKeyBinder:
    def __init__(self, win_id) -> None:
        keybinder.init()
        self.win_id = win_id

        self.event_dispatcher = EventDispatcher(keybinder=keybinder)

    def register_hotkey(self, hotkey: str, callback) -> None:
        keybinder.register_hotkey(self.win_id, hotkey, callback)

    def unregister_hotkey(self, hotkey: str) -> None:
        keybinder.unregister_hotkey(self.win_id, hotkey)

if __name__ == "__main__":
    lock_file = ".open_mouseless.lock"

    lock = FileLock(lock_file)
    try:
        lock.acquire(timeout=0)
    except Exception:
        sys.exit()
    show_hotkey = settings.get("show_hotkey", "Ctrl+m")
    quit_hotkey = settings.get("quit_hotkey", "Ctrl+Alt+q")
    app = QApplication(sys.argv)
    overlay = OpenMouseless()
    hotkey = QtKeyBinder(win_id=None)
    hotkey.register_hotkey(show_hotkey, overlay.show)
    hotkey.register_hotkey(quit_hotkey, app.quit)
    app.exec_()
    hotkey.unregister_hotkey(show_hotkey)
    hotkey.unregister_hotkey(quit_hotkey)
