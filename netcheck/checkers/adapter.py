from netcheck.core.base_checker import BaseChecker
from netcheck.core.models import CheckResult, CheckStatus, CheckCategory
import netcheck.core.platform_utils as platform_utils

class AdapterChecker(BaseChecker):
    def name(self) -> str:
        return "adapter"
        
    def depends_on(self) -> list[str]:
        return []
        
    def check(self) -> list[CheckResult]:
        try:
            adapters = platform_utils.get_adapter_info()
            adapters = [a for a in adapters if not a.is_loopback]
            
            if not adapters:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.FAIL,
                    category=CheckCategory.PHYSICAL,
                    title_key="check.adapter.title",
                    summary_key="check.adapter.fail_no_adapters",
                    details=["No network adapters found."],
                    recommendations=["check.adapter.rec.install_driver"],
                    raw_data={}
                )]
            
            active_adapters = [a for a in adapters if a.is_up]
            
            if not active_adapters:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.FAIL,
                    category=CheckCategory.PHYSICAL,
                    title_key="check.adapter.title",
                    summary_key="check.adapter.fail_unplugged",
                    details=["No active adapters found."],
                    recommendations=["check.adapter.rec.enable", "check.adapter.rec.plug_cable"],
                    raw_data={"adapters": [vars(a) for a in adapters]}
                )]
            
            details = []
            status = CheckStatus.PASS
            summary_key = "check.adapter.pass"
            raw_data = {"adapters": [vars(a) for a in active_adapters]}
            
            for adapter in active_adapters:
                details.append(f"Adapter: {adapter.name}, Speed: {adapter.speed_mbps} Mbps")
                if "wi-fi" in adapter.name.lower() or "wlan" in adapter.name.lower():
                    wifi_info = platform_utils.get_wifi_info()
                    if wifi_info:
                        details.append(f"WiFi SSID: {wifi_info.ssid}, Signal: {wifi_info.signal_strength_pct}%")
                        raw_data["wifi"] = vars(wifi_info)
                        if wifi_info.signal_strength_pct < 30:
                            status = CheckStatus.WARNING
                            summary_key = "check.adapter.warn_weak_signal"
                            
            return [CheckResult(
                name=self.name(),
                status=status,
                category=CheckCategory.PHYSICAL,
                title_key="check.adapter.title",
                summary_key=summary_key,
                details=details,
                recommendations=["check.adapter.rec.move_closer"] if status == CheckStatus.WARNING else [],
                raw_data=raw_data
            )]
        except Exception as e:
            return [CheckResult(
                name=self.name(),
                status=CheckStatus.FAIL,
                category=CheckCategory.PHYSICAL,
                title_key="check.adapter.title",
                summary_key="check.error",
                details=[f"Error checking adapters: {str(e)}"],
                raw_data={"error": str(e)}
            )]
