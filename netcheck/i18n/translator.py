import json
import os
from PyQt6.QtCore import QObject, pyqtSignal

class Translator(QObject):
    language_changed = pyqtSignal(str)
    
    def __init__(self, default_lang='id'):
        super().__init__()
        self._current_lang = default_lang
        self._translations = {}
        self._fallback_translations = {}
        self._load_translations()
        
    def _load_translations(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load English fallback first
        en_path = os.path.join(base_dir, 'en.json')
        if os.path.exists(en_path):
            with open(en_path, 'r', encoding='utf-8') as f:
                self._fallback_translations = json.load(f)
        else:
            self._fallback_translations = {}
            
        # Load current language
        lang_path = os.path.join(base_dir, f'{self._current_lang}.json')
        if os.path.exists(lang_path):
            with open(lang_path, 'r', encoding='utf-8') as f:
                self._translations = json.load(f)
        else:
            self._translations = {}
            
    def set_language(self, lang: str):
        if self._current_lang != lang:
            self._current_lang = lang
            self._load_translations()
            self.language_changed.emit(lang)
            
    @property
    def current_language(self) -> str:
        return self._current_lang
        
    def t(self, key: str, **params) -> str:
        text = self._translations.get(key, self._fallback_translations.get(key, key))
        if params:
            try:
                return text.format(**params)
            except KeyError:
                return text
        return text
        
    def available_languages(self) -> list[tuple[str, str]]:
        return [
            ('id', 'Bahasa Indonesia'),
            ('en', 'English')
        ]

translator = Translator()
