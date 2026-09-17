"""Top toolbar widget with language selector and about button."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt

from netcheck.i18n.translator import translator


class Toolbar(QWidget):
    """Top toolbar with language selector and about button."""

    about_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        translator.language_changed.connect(self._on_language_changed)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        self.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E0E0E0;")

        # App logo / name on the left
        logo = QLabel("🌐 NetCheck")
        logo.setStyleSheet("font-weight: bold; font-size: 15px; color: #1976D2;")
        layout.addWidget(logo)

        layout.addStretch()

        # Language selector
        self.lang_combo = QComboBox()
        self.lang_combo.setCursor(Qt.CursorShape.PointingHandCursor)

        # Populate from translator's available languages
        self._available = translator.available_languages()  # [(code, display_name), ...]
        for code, display in self._available:
            self.lang_combo.addItem(display, code)

        # Set current index to match current language
        current = translator.current_language
        for i, (code, _) in enumerate(self._available):
            if code == current:
                self.lang_combo.setCurrentIndex(i)
                break

        self.lang_combo.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self.lang_combo)

        # About button
        self.about_btn = QPushButton(translator.t("about.title"))
        self.about_btn.setFlat(True)
        self.about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.about_btn.clicked.connect(self.about_clicked)
        layout.addWidget(self.about_btn)

    def _on_combo_changed(self, index: int):
        """Called when user picks a language from the combo."""
        if 0 <= index < len(self._available):
            code = self._available[index][0]
            # Avoid infinite loop — only set if actually different
            if code != translator.current_language:
                translator.set_language(code)

    def _on_language_changed(self, lang: str):
        """Update UI when language changes (e.g. triggered externally)."""
        # Update combo selection without triggering _on_combo_changed
        self.lang_combo.blockSignals(True)
        for i, (code, _) in enumerate(self._available):
            if code == lang:
                self.lang_combo.setCurrentIndex(i)
                break
        self.lang_combo.blockSignals(False)

        # Update about button text
        self.about_btn.setText(translator.t("about.title"))
