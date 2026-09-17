REPORT_HEADER_TEMPLATE = """=========================================
{title}
=========================================
{time_label}: {time_val}
{computer_label}: {computer_val}
{os_label}: {os_val}
-----------------------------------------
"""

REPORT_CHECK_LINE_TEMPLATE = "[{status}] {title}: {summary}"

REPORT_FOOTER_TEMPLATE = """-----------------------------------------
{conclusion_label}
-----------------------------------------
{diagnosis_title}
{diagnosis_desc}
"""
