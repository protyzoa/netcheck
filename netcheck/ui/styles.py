from enum import Enum
from netcheck.core.models import CheckStatus

STATUS_COLORS = {
    CheckStatus.PASS: "#4CAF50",
    CheckStatus.WARNING: "#FF9800",
    CheckStatus.FAIL: "#F44336",
    CheckStatus.SKIPPED: "#9E9E9E",
    CheckStatus.RUNNING: "#2196F3",
}

STATUS_BG_COLORS = {
    CheckStatus.PASS: "#E8F5E9",
    CheckStatus.WARNING: "#FFF3E0",
    CheckStatus.FAIL: "#FFEBEE",
    CheckStatus.SKIPPED: "#F5F5F5",
    CheckStatus.RUNNING: "#E3F2FD",
}

MAIN_STYLESHEET = """
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #212121;
}
QMainWindow {
    background-color: #FAFAFA;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}
"""
