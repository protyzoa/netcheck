"""Dialog for managing custom check targets."""

import uuid

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit,
    QComboBox, QSpinBox, QMessageBox, QLabel, QCheckBox,
)
from PyQt6.QtCore import Qt

from netcheck.core.models import CustomTarget, CheckType
from netcheck.config.targets import target_manager
from netcheck.i18n.translator import translator


class TargetDialog(QDialog):
    """Add/edit dialog for a single custom target."""

    def __init__(self, target: CustomTarget | None = None, parent=None):
        super().__init__(parent)
        self.target = target
        self._setup_ui()
        if target:
            self._populate(target)

    def _setup_ui(self):
        self.setWindowTitle(
            translator.t("target.edit_title") if self.target
            else translator.t("target.add_title")
        )
        self.setMinimumWidth(360)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Name
        layout.addWidget(QLabel(translator.t("target.name")))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(translator.t("target.placeholder_name"))
        layout.addWidget(self.name_input)

        # Host
        layout.addWidget(QLabel(translator.t("target.host")))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText(translator.t("target.placeholder_host"))
        layout.addWidget(self.host_input)

        # Check Type
        layout.addWidget(QLabel(translator.t("target.type")))
        self.type_combo = QComboBox()
        for ctype in CheckType:
            self.type_combo.addItem(ctype.value.upper(), ctype)
        layout.addWidget(self.type_combo)

        # Port (only visible for PORT type)
        self.port_label = QLabel(translator.t("target.port"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(80)
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_spin)
        self._update_port_visibility(self.type_combo.currentData())

        self.type_combo.currentIndexChanged.connect(
            lambda: self._update_port_visibility(self.type_combo.currentData())
        )

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton(translator.t("btn.save"))
        self.save_btn.setDefault(True)
        self.cancel_btn = QPushButton(translator.t("btn.close"))
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

    def _update_port_visibility(self, check_type: CheckType | None):
        is_port = check_type == CheckType.PORT
        self.port_label.setVisible(is_port)
        self.port_spin.setVisible(is_port)

    def _populate(self, target: CustomTarget):
        self.name_input.setText(target.name)
        self.host_input.setText(target.host)
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == target.check_type:
                self.type_combo.setCurrentIndex(i)
                break
        if target.port:
            self.port_spin.setValue(target.port)

    def _on_save(self):
        name = self.name_input.text().strip()
        host = self.host_input.text().strip()

        if not name:
            QMessageBox.warning(self, translator.t("app.title"), translator.t("target.validation_name"))
            return
        if not host:
            QMessageBox.warning(self, translator.t("app.title"), translator.t("target.validation_host"))
            return

        self.accept()

    def get_target(self) -> CustomTarget:
        """Build a CustomTarget from the current form values."""
        check_type = self.type_combo.currentData()
        port = self.port_spin.value() if check_type == CheckType.PORT else None
        return CustomTarget(
            id=self.target.id if self.target else str(uuid.uuid4()),
            name=self.name_input.text().strip(),
            host=self.host_input.text().strip(),
            check_type=check_type,
            port=port,
            enabled=self.target.enabled if self.target else True,
        )


class TargetManagerDialog(QDialog):
    """Dialog for managing the list of custom check targets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle(translator.t("target.title"))
        self.resize(520, 380)
        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            translator.t("target.name"),
            translator.t("target.host"),
            translator.t("target.type"),
            "Enabled",
        ])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QTableWidget.horizontalHeader(self.table).ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(translator.t("btn.add"))
        self.edit_btn = QPushButton(translator.t("btn.edit"))
        self.del_btn = QPushButton(translator.t("btn.delete"))
        self.close_btn = QPushButton(translator.t("btn.close"))

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self.add_btn.clicked.connect(self._add_target)
        self.edit_btn.clicked.connect(self._edit_target)
        self.del_btn.clicked.connect(self._delete_target)
        self.close_btn.clicked.connect(self.accept)
        self.table.doubleClicked.connect(self._edit_target)

    def _load_data(self):
        self.table.setRowCount(0)
        for target in target_manager.get_all():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(target.name))
            self.table.setItem(row, 1, QTableWidgetItem(target.host))
            self.table.setItem(row, 2, QTableWidgetItem(target.check_type.value.upper()))
            self.table.setItem(row, 3, QTableWidgetItem("✓" if target.enabled else "✗"))
            # Store target reference in the first column's item
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, target)

    def _selected_target(self) -> CustomTarget | None:
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _add_target(self):
        dlg = TargetDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            target_manager.add(dlg.get_target())
            self._load_data()

    def _edit_target(self):
        target = self._selected_target()
        if not target:
            return
        dlg = TargetDialog(target=target, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            target_manager.update(dlg.get_target())
            self._load_data()

    def _delete_target(self):
        target = self._selected_target()
        if not target:
            return
        reply = QMessageBox.question(
            self,
            translator.t("target.title"),
            translator.t("target.delete_confirm", name=target.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            target_manager.delete(target.id)
            self._load_data()
