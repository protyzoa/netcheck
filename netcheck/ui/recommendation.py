from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from netcheck.core.models import DiagnosisResult, CheckStatus
from netcheck.i18n.translator import translator

class RecommendationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        try:
            translator.language_changed.connect(self.update_texts)
        except AttributeError:
            pass
        self.diagnosis = None
        self.hide()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        
        self.icon_label = QLabel()
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.recs_label = QLabel()
        self.recs_label.setWordWrap(True)
        
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.desc_label)
        self.layout.addWidget(self.recs_label)
        
    def set_diagnosis(self, diagnosis: DiagnosisResult):
        self.diagnosis = diagnosis
        self.update_texts()
        
        if diagnosis.severity == CheckStatus.PASS:
            self.icon_label.setText("✅")
            self.setStyleSheet("background-color: #E8F5E9; border-radius: 8px;")
        elif diagnosis.severity == CheckStatus.WARNING:
            self.icon_label.setText("⚠️")
            self.setStyleSheet("background-color: #FFF3E0; border-radius: 8px;")
        else:
            self.icon_label.setText("❌")
            self.setStyleSheet("background-color: #FFEBEE; border-radius: 8px;")
            
        self.show()
        
    def clear(self):
        self.diagnosis = None
        self.hide()
        
    def update_texts(self):
        if self.diagnosis and hasattr(translator, 't'):
            self.title_label.setText(translator.t(self.diagnosis.title_key))
            self.desc_label.setText(translator.t(self.diagnosis.description_key, **self.diagnosis.description_params))
            recs_text = "\n".join(f"{i+1}. {translator.t(rec)}" for i, rec in enumerate(self.diagnosis.recommendations))
            self.recs_label.setText(recs_text)
