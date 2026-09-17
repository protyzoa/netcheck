"""Data models and enums used throughout the application."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CheckStatus(Enum):
    """Status of a network check."""
    PASS = "pass"          # 🟢 Everything OK
    WARNING = "warning"    # 🟡 Partially OK or degraded
    FAIL = "fail"          # 🔴 Failed
    SKIPPED = "skipped"    # ⚪ Skipped (dependency failed)
    RUNNING = "running"    # 🔵 Currently running


class CheckCategory(Enum):
    """Category/layer of a network check."""
    PHYSICAL = "physical"       # Layer 1 - adapter, cable, WiFi
    IP_CONFIG = "ip_config"     # Layer 2 - IP, DHCP, gateway config
    CONNECTIVITY = "connectivity"  # Layer 3 - ping, traceroute
    DNS = "dns"                 # Layer 4 - DNS resolution
    APPLICATION = "application"  # Layer 5 - HTTP, port checks
    CUSTOM = "custom"           # User-defined targets


class CheckType(Enum):
    """Type of check for custom targets."""
    PING = "ping"
    DNS = "dns"
    HTTP = "http"
    PORT = "port"


@dataclass
class CheckResult:
    """Result of a single network check."""
    name: str                           # Internal ID, e.g. "adapter_status"
    status: CheckStatus                 # Pass/Warning/Fail/Skipped
    category: CheckCategory             # Which layer this belongs to
    title_key: str                      # i18n key for display title
    summary_key: str                    # i18n key for one-line summary
    summary_params: dict[str, Any] = field(default_factory=dict)  # Parameters for summary template
    details: list[str] = field(default_factory=list)              # Technical details (expandable)
    recommendations: list[str] = field(default_factory=list)      # i18n keys for recommendations
    raw_data: dict[str, Any] = field(default_factory=dict)        # Raw data for report generation


@dataclass
class CustomTarget:
    """A user-defined check target."""
    id: str              # Unique identifier (UUID)
    name: str            # Display name, e.g. "Server ERP"
    host: str            # Hostname or IP, e.g. "erp.kantor.local"
    check_type: CheckType  # Type of check to perform
    port: int | None = None  # Port number (for PORT check type)
    enabled: bool = True     # Whether this target is active

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "check_type": self.check_type.value,
            "port": self.port,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CustomTarget":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            host=data["host"],
            check_type=CheckType(data["check_type"]),
            port=data.get("port"),
            enabled=data.get("enabled", True),
        )


@dataclass
class DiagnosisResult:
    """Auto-diagnosis based on combined check results."""
    title_key: str                  # i18n key for diagnosis title
    description_key: str            # i18n key for description
    description_params: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)  # i18n keys for recommended actions
    severity: CheckStatus = CheckStatus.FAIL

