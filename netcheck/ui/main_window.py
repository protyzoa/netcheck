"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QPushButton, QLabel, QMessageBox, QApplication,
)
from PyQt6.QtCore import Qt, QSettings

from netcheck.ui.toolbar import Toolbar
from netcheck.ui.check_button import CheckButton
from netcheck.ui.result_card import ResultCard
from netcheck.ui.recommendation import RecommendationPanel
from netcheck.ui.target_manager import TargetManagerDialog
from netcheck.ui.styles import MAIN_STYLESHEET
from netcheck.core.models import CheckResult, CheckStatus, CheckCategory, DiagnosisResult
from netcheck.core.engine import CheckerEngine
from netcheck.checkers.adapter import AdapterChecker
from netcheck.checkers.ip_config import IPConfigChecker
from netcheck.checkers.gateway import GatewayChecker
from netcheck.checkers.internet import InternetChecker
from netcheck.checkers.dns import DNSChecker
from netcheck.checkers.custom_target import CustomTargetChecker
from netcheck.config.targets import target_manager
from netcheck.reporting.generator import ReportGenerator
from netcheck.i18n.translator import translator


def diagnose(results: list[CheckResult]) -> DiagnosisResult:
    """Analyze combined results and produce an auto-diagnosis.

    Uses a decision-tree approach based on which layer failed first.
    """
    if not results:
        return DiagnosisResult(
            title_key="diagnosis.all_ok",
            description_key="diagnosis.all_ok_desc",
            severity=CheckStatus.PASS,
        )

    # Build a status map by checker name
    status_map: dict[str, CheckStatus] = {}
    for r in results:
        # Use the worst status per checker name
        if r.name not in status_map or _severity(r.status) > _severity(status_map[r.name]):
            status_map[r.name] = r.status

    # All pass?
    if all(s == CheckStatus.PASS for s in status_map.values()):
        return DiagnosisResult(
            title_key="diagnosis.all_ok",
            description_key="diagnosis.all_ok_desc",
            severity=CheckStatus.PASS,
        )

    # Check from bottom layer up to find root cause
    if status_map.get("adapter") == CheckStatus.FAIL:
        return DiagnosisResult(
            title_key="diagnosis.cable_unplugged",
            description_key="diagnosis.cable_unplugged_desc",
            severity=CheckStatus.FAIL,
            recommendations=["rec.check_cable", "rec.enable_adapter", "rec.restart_adapter"],
        )

    if status_map.get("ip_config") == CheckStatus.FAIL:
        return DiagnosisResult(
            title_key="diagnosis.no_ip",
            description_key="diagnosis.no_ip_desc",
            severity=CheckStatus.FAIL,
            recommendations=["rec.restart_router", "rec.renew_ip", "rec.check_dhcp"],
        )

    if status_map.get("gateway") == CheckStatus.FAIL:
        return DiagnosisResult(
            title_key="diagnosis.gateway_down",
            description_key="diagnosis.gateway_down_desc",
            severity=CheckStatus.FAIL,
            recommendations=["rec.check_cable", "rec.restart_router"],
        )

    if status_map.get("internet") == CheckStatus.FAIL:
        return DiagnosisResult(
            title_key="diagnosis.internet_down",
            description_key="diagnosis.internet_down_desc",
            severity=CheckStatus.FAIL,
            recommendations=["rec.restart_modem", "rec.restart_router", "rec.contact_isp"],
        )

    if status_map.get("dns") == CheckStatus.FAIL:
        return DiagnosisResult(
            title_key="diagnosis.dns_issue",
            description_key="diagnosis.dns_issue_desc",
            severity=CheckStatus.FAIL,
            recommendations=["rec.change_dns", "rec.flush_dns"],
        )

    # Any warnings?
    if any(s == CheckStatus.WARNING for s in status_map.values()):
        return DiagnosisResult(
            title_key="diagnosis.unstable",
            description_key="diagnosis.unstable_desc",
            severity=CheckStatus.WARNING,
            recommendations=["rec.check_cable", "rec.restart_router", "rec.move_closer"],
        )

    # Default fallback
    return DiagnosisResult(
        title_key="diagnosis.all_ok",
        description_key="diagnosis.all_ok_desc",
        severity=CheckStatus.PASS,
    )


def _severity(status: CheckStatus) -> int:
    """Return numeric severity for comparison."""
    return {
        CheckStatus.PASS: 0,
        CheckStatus.SKIPPED: 1,
        CheckStatus.WARNING: 2,
        CheckStatus.FAIL: 3,
        CheckStatus.RUNNING: 0,
    }.get(status, 0)


class MainWindow(QMainWindow):
    """Main application window with all UI components."""

    def __init__(self):
        super().__init__()
        self.last_results: list[CheckResult] = []
        self.last_diagnosis: DiagnosisResult | None = None
        self.result_cards: dict[str, ResultCard] = {}
        self.report_gen = ReportGenerator()

        self._setup_engine()
        self._setup_ui()
        self._setup_connections()
        self._restore_geometry()

    def _setup_engine(self):
        """Create the checker engine once and register all checkers."""
        self.engine = CheckerEngine()
        self._refresh_checkers()

    def _refresh_checkers(self):
        """Clear and re-register all checkers (called before each run)."""
        self.engine.clear_checkers()
        self.engine.register_checker(AdapterChecker())
        self.engine.register_checker(IPConfigChecker())
        self.engine.register_checker(GatewayChecker())
        self.engine.register_checker(InternetChecker())
        self.engine.register_checker(DNSChecker())

        # Add custom target checker if there are enabled targets
        targets = target_manager.get_enabled()
        if targets:
            self.engine.register_checker(CustomTargetChecker(targets))

    def _setup_ui(self):
        """Build the UI layout."""
        self.setWindowTitle(translator.t("app.title"))
        self.setMinimumSize(460, 620)
        self.resize(520, 750)
        self.setStyleSheet(MAIN_STYLESHEET)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Toolbar
        self.toolbar = Toolbar()
        self.main_layout.addWidget(self.toolbar)

        # Title area
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(20, 20, 20, 10)

        self.title_label = QLabel(translator.t("app.title"))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #1976D2;"
        )

        self.subtitle_label = QLabel(translator.t("app.subtitle"))
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("color: #757575; font-size: 13px;")

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        self.main_layout.addWidget(title_container)

        # Check button
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.setContentsMargins(20, 10, 20, 20)
        self.check_btn = CheckButton()
        self.check_btn.setFixedSize(240, 120)
        btn_layout.addWidget(self.check_btn)
        self.main_layout.addWidget(btn_container)

        # Results scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(16, 8, 16, 8)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.hide()
        self.main_layout.addWidget(self.scroll_area, 1)

        # Recommendation panel
        self.rec_panel = RecommendationPanel()
        self.main_layout.addWidget(self.rec_panel)

        # Bottom action bar
        self.bottom_bar = QWidget()
        self.bottom_bar.setStyleSheet("background-color: #F5F5F5;")
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(16, 12, 16, 12)

        self.manage_btn = QPushButton(translator.t("btn.manage_targets"))
        self.manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manage_btn.setStyleSheet(
            "QPushButton { padding: 8px 16px; border: 1px solid #BDBDBD; "
            "border-radius: 6px; background: white; }"
            "QPushButton:hover { background: #E3F2FD; }"
        )

        self.copy_btn = QPushButton(translator.t("btn.copy_report"))
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setEnabled(False)
        self.copy_btn.setStyleSheet(
            "QPushButton { padding: 8px 16px; border: 1px solid #BDBDBD; "
            "border-radius: 6px; background: white; }"
            "QPushButton:hover { background: #E3F2FD; }"
            "QPushButton:disabled { color: #BDBDBD; background: #F5F5F5; }"
        )

        bottom_layout.addWidget(self.manage_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.copy_btn)
        self.main_layout.addWidget(self.bottom_bar)

    def _setup_connections(self):
        """Connect signals and slots."""
        self.check_btn.clicked.connect(self._on_check_clicked)
        self.copy_btn.clicked.connect(self._copy_report)
        self.manage_btn.clicked.connect(self._open_manage_targets)
        self.toolbar.about_clicked.connect(self._show_about)

        translator.language_changed.connect(self._update_texts)

        self.engine.check_started.connect(self._on_check_started)
        self.engine.check_completed.connect(self._on_check_completed)
        self.engine.all_completed.connect(self._on_all_completed)
        self.engine.progress.connect(self.check_btn.set_progress)

    def _on_check_clicked(self):
        """Handle check button click — start or cancel checks."""
        if self.check_btn._state == "running":
            self.engine.cancel()
            self.check_btn.set_state("idle")
            return

        # Clear previous results
        self.scroll_area.show()
        self.rec_panel.clear()
        self.copy_btn.setEnabled(False)
        self.last_results.clear()

        for card in self.result_cards.values():
            self.scroll_layout.removeWidget(card)
            card.deleteLater()
        self.result_cards.clear()

        # Refresh checkers (picks up any new custom targets) — engine stays the same
        self._refresh_checkers()

        self.check_btn.set_state("running")
        self.engine.run_all()

    def _on_check_started(self, checker_name: str):
        """Called when a checker starts running."""
        if checker_name not in self.result_cards:
            card = ResultCard(checker_name)
            self.result_cards[checker_name] = card
            # Insert before the stretch
            self.scroll_layout.insertWidget(
                self.scroll_layout.count() - 1, card
            )
        self.result_cards[checker_name].set_running()

    def _on_check_completed(self, checker_name: str, results: list):
        """Called when a checker finishes. Creates one card per result."""
        for result in results:
            card_key = result.name  # unique per result (e.g. custom_<uuid>)
            if card_key in self.result_cards:
                self.result_cards[card_key].set_result(result)
            else:
                # For custom targets: create a new card for each result
                card = ResultCard(card_key)
                self.result_cards[card_key] = card
                self.scroll_layout.insertWidget(
                    self.scroll_layout.count() - 1, card
                )
                card.set_result(result)
            # Also update the "parent" checker card if it exists
            if checker_name in self.result_cards and checker_name != card_key:
                # Use worst status across all results
                worst = max(results, key=lambda r: {
                    "pass": 0, "warning": 1, "fail": 2, "skipped": 1, "running": 0
                }.get(r.status.value, 0))
                self.result_cards[checker_name].set_result(worst)

    def _on_all_completed(self, results: list):
        """Called when all checks are done."""
        self.last_results = results
        self.last_diagnosis = diagnose(results)

        self.check_btn.set_state("done")
        self.rec_panel.set_diagnosis(self.last_diagnosis)
        self.copy_btn.setEnabled(True)

    def _copy_report(self):
        """Generate and copy diagnostic report to clipboard."""
        if not self.last_results:
            return
        report = self.report_gen.generate(self.last_results, self.last_diagnosis)
        self.report_gen.to_clipboard(report)
        QMessageBox.information(
            self,
            translator.t("app.title"),
            translator.t("report.copied"),
        )

    def _open_manage_targets(self):
        """Open the target management dialog."""
        dlg = TargetManagerDialog(self)
        dlg.exec()

    def _show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            translator.t("about.title"),
            f"{translator.t('about.description')}\n\n"
            f"{translator.t('about.version', version='1.0.0')}",
        )

    def _update_texts(self):
        """Update all translatable text when language changes."""
        self.setWindowTitle(translator.t("app.title"))
        self.title_label.setText(translator.t("app.title"))
        self.subtitle_label.setText(translator.t("app.subtitle"))
        self.copy_btn.setText(translator.t("btn.copy_report"))
        self.manage_btn.setText(translator.t("btn.manage_targets"))

    def _restore_geometry(self):
        """Restore window position and size from settings."""
        settings = QSettings("NetCheck", "NetCheckApp")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event):
        """Save window geometry on close."""
        settings = QSettings("NetCheck", "NetCheckApp")
        settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
