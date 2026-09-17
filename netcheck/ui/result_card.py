from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from netcheck.core.models import CheckResult, CheckStatus
from netcheck.i18n.translator import translator
from netcheck.ui.styles import STATUS_COLORS, STATUS_BG_COLORS

class ResultCard(QWidget):
    def __init__(self, checker_name: str, parent=None):
        super().__init__(parent)
        self.checker_name = checker_name
        self.result = None
        
        self.setup_ui()
        try:
            translator.language_changed.connect(self.update_texts)
        except AttributeError:
            pass
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.container = QWidget(self)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(16, 16, 16, 16)
        
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_icon = QLabel("●")
        self.title_label = QLabel(self.checker_name)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #757575;")
        self.toggle_btn = QPushButton("▾")
        self.toggle_btn.setFlat(True)
        self.toggle_btn.setFixedSize(24, 24)
        
        self.header_layout.addWidget(self.status_icon)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.status_label)
        self.header_layout.addWidget(self.toggle_btn)
        
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.details_label = QLabel("")
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet("font-family: monospace; color: #424242;")
        self.body_layout.addWidget(self.details_label)
        self.body.hide()
        
        self.container_layout.addWidget(self.header)
        self.container_layout.addWidget(self.body)
        
        self.main_layout.addWidget(self.container)
        
        self.container.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 8px;
            }
        """)
        
        self.header.mousePressEvent = self.header_clicked
        self.toggle_btn.clicked.connect(self.toggle)
        self.is_expanded = False
        
        self.animation = QPropertyAnimation(self.body, b"maximumHeight")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.setDuration(200)

    def header_clicked(self, event):
        self.toggle()

    def toggle(self):
        if not self.result or not self.result.details:
            return
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        self.body.show()
        self.animation.setStartValue(0)
        self.animation.setEndValue(self.body.sizeHint().height())
        self.animation.start()
        self.toggle_btn.setText("▴")
        self.is_expanded = True

    def collapse(self):
        self.animation.setStartValue(self.body.height())
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.body.hide)
        self.animation.start()
        self.toggle_btn.setText("▾")
        self.is_expanded = False
        
    def set_result(self, result: CheckResult):
        self.result = result
        self.update_texts()
        
        status_color = STATUS_COLORS.get(result.status, "#9E9E9E")
        bg_color = STATUS_BG_COLORS.get(result.status, "#FFFFFF")
        
        self.status_icon.setStyleSheet(f"color: {status_color}; font-size: 16px;")
        self.container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 8px;
            }}
        """)
        
        if result.details:
            self.details_label.setText("\n".join(result.details))
            self.toggle_btn.show()
        else:
            self.toggle_btn.hide()
            
    def set_running(self):
        self.status_icon.setStyleSheet(f"color: {STATUS_COLORS[CheckStatus.RUNNING]}; font-size: 16px;")
        self.status_label.setText(translator.t('status.running') if hasattr(translator, 't') else 'Running')
        self.container.setStyleSheet(f"""
            QWidget {{
                background-color: {STATUS_BG_COLORS[CheckStatus.RUNNING]};
                border-radius: 8px;
            }}
        """)
        
    def update_texts(self):
        if self.result and hasattr(translator, 't'):
            # Title also gets summary_params (e.g. custom targets use {name})
            self.title_label.setText(
                translator.t(self.result.title_key, **self.result.summary_params)
            )
            self.status_label.setText(
                translator.t(self.result.summary_key, **self.result.summary_params)
            )
