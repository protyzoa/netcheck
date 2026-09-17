import json
import os
from pathlib import Path

class Settings:
    def __init__(self):
        if os.name == 'nt':
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            self.config_dir = Path(appdata) / 'NetCheck'
        else:
            self.config_dir = Path.home() / '.netcheck'
            
        self.config_file = self.config_dir / 'settings.json'
        
        self.language = 'id'
        self.window_geometry = {}
        self.last_check_time = ""
        
        self.load()
        
    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.language = data.get('language', 'id')
                    self.window_geometry = data.get('window_geometry', {})
                    self.last_check_time = data.get('last_check_time', "")
            except Exception:
                pass
                
    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        data = {
            'language': self.language,
            'window_geometry': self.window_geometry,
            'last_check_time': self.last_check_time
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

settings = Settings()
