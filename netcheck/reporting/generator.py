"""Report generation for network diagnostics."""

import platform
import socket
from datetime import datetime

from netcheck.core.models import CheckResult, CheckStatus, DiagnosisResult
from netcheck.reporting.templates import (
    REPORT_HEADER_TEMPLATE,
    REPORT_CHECK_LINE_TEMPLATE,
    REPORT_FOOTER_TEMPLATE,
)
from netcheck.i18n.translator import translator


_STATUS_SYMBOLS = {
    CheckStatus.PASS: "PASS",
    CheckStatus.WARNING: "WARN",
    CheckStatus.FAIL: "FAIL",
    CheckStatus.SKIPPED: "SKIP",
    CheckStatus.RUNNING: "RUN ",
}


class ReportGenerator:
    """Generate diagnostic reports from check results."""

    def generate(
        self,
        results: list[CheckResult],
        diagnosis: DiagnosisResult | None = None,
    ) -> str:
        """Generate a full text report.

        Args:
            results: List of CheckResult objects.
            diagnosis: Optional DiagnosisResult for the conclusion section.

        Returns:
            Formatted report string.
        """
        report_lines: list[str] = []

        # Header
        header = REPORT_HEADER_TEMPLATE.format(
            title=translator.t("report.title"),
            time_label=translator.t("report.time"),
            time_val=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            computer_label=translator.t("report.computer"),
            computer_val=socket.gethostname(),
            os_label=translator.t("report.os"),
            os_val=platform.platform(),
        )
        report_lines.append(header)

        # Results
        report_lines.append(f"--- {translator.t('report.results')} ---")
        for result in results:
            status_str = _STATUS_SYMBOLS.get(result.status, "????")
            title = translator.t(result.title_key)
            summary = translator.t(result.summary_key, **result.summary_params)

            line = REPORT_CHECK_LINE_TEMPLATE.format(
                status=status_str,
                title=title,
                summary=summary,
            )
            report_lines.append(line)

            # Show details for failed/warning checks
            if result.status in (CheckStatus.FAIL, CheckStatus.WARNING) and result.details:
                for detail in result.details:
                    report_lines.append(f"  | {detail}")

        report_lines.append("")

        # Diagnosis / conclusion
        if diagnosis:
            diag_title = translator.t(diagnosis.title_key, **diagnosis.description_params)
            diag_desc = translator.t(diagnosis.description_key, **diagnosis.description_params)
            footer = REPORT_FOOTER_TEMPLATE.format(
                conclusion_label=translator.t("report.conclusion"),
                diagnosis_title=diag_title,
                diagnosis_desc=diag_desc,
            )
            report_lines.append(footer)

            if diagnosis.recommendations:
                report_lines.append("")
                for i, rec_key in enumerate(diagnosis.recommendations, 1):
                    report_lines.append(f"  {i}. {translator.t(rec_key)}")

        report_lines.append("=========================================")
        return "\n".join(report_lines)

    def to_clipboard(self, report: str) -> None:
        """Copy report text to system clipboard."""
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(report)

    def to_file(self, report: str, path: str) -> None:
        """Save report to a text file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
