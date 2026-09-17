import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from netcheck.ui.main_window import MainWindow

try:
    from netcheck.config.settings import settings
except ImportError:
    class Settings:
        language = 'en'
        def load(self): pass
    settings = Settings()

try:
    from netcheck.i18n.translator import translator
except ImportError:
    class Translator:
        def set_language(self, l): pass
    translator = Translator()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('NetCheck')
    app.setApplicationVersion('1.0.0')
    
    # Load settings
    settings.load()
    translator.set_language(settings.language)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
