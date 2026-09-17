from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QTimer, Qt
from netcheck.i18n.translator import translator

class CheckButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._state = 'idle'
        self._current = 0
        self._total = 0
        self.update_text()
        try:
            translator.language_changed.connect(self.update_text)
        except AttributeError:
            pass
        self.update_style()
        
    def set_progress(self, current: int, total: int):
        self._current = current
        self._total = total
        self.update_text()
        
    def set_state(self, state: str):
        self._state = state
        self.update_text()
        self.update_style()
        if state == 'done':
            QTimer.singleShot(2000, lambda: self.set_state('idle'))
            
    def update_text(self):
        if self._state == 'idle':
            self.setText(translator.t('btn.check') if hasattr(translator, 't') else 'Check')
        elif self._state == 'running':
            self.setText(translator.t('btn.checking', current=self._current, total=self._total) if hasattr(translator, 't') else f'Checking {self._current}/{self._total}')
        elif self._state == 'done':
            self.setText("✓")
            
    def update_style(self):
        base_style = """
            QPushButton {
                border-radius: 60px;
                font-size: 24px;
                font-weight: bold;
                color: white;
                border: none;
            }
        """
        if self._state == 'idle':
            self.setStyleSheet(base_style + """
                QPushButton { background-color: #1976D2; }
                QPushButton:hover { background-color: #1565C0; }
            """)
        elif self._state == 'running':
            self.setStyleSheet(base_style + """
                QPushButton { background-color: #2196F3; }
            """)
        elif self._state == 'done':
            self.setStyleSheet(base_style + """
                QPushButton { background-color: #4CAF50; }
            """)
