from netcheck.core.base_checker import BaseChecker
from netcheck.core.models import CheckResult, CheckStatus, CheckCategory
import netcheck.core.platform_utils as platform_utils

class IPConfigChecker(BaseChecker):
    def name(self) -> str:
        return "ip_config"
        
    def depends_on(self) -> list[str]:
        return ["adapter"]
        
    def check(self) -> list[CheckResult]:
        try:
            adapters = platform_utils.get_adapter_info()
            active_adapter = next((a for a in adapters if a.is_up and not a.is_loopback), None)
            
            if not active_adapter:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.FAIL,
                    category=CheckCategory.IP_CONFIG,
                    title_key="check.ip_config.title",
                    summary_key="check.ip_config.fail_no_adapter",
                    details=["No active adapter found."],
                    raw_data={}
                )]
                
            ip = active_adapter.ipv4_address
            gateway = platform_utils.get_default_gateway()
            is_dhcp = not ip.startswith("169.254.") if ip else False
            
            details = [f"IP Address: {ip}", f"Subnet Mask: {active_adapter.ipv4_netmask}", f"Gateway: {gateway}", f"DHCP: {'Yes' if is_dhcp else 'No'}"]
            raw_data = {"ip": ip, "netmask": active_adapter.ipv4_netmask, "gateway": gateway, "is_dhcp": is_dhcp}
            
            if not ip:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.FAIL,
                    category=CheckCategory.IP_CONFIG,
                    title_key="check.ip_config.title",
                    summary_key="check.ip_config.fail_no_ip",
                    details=details,
                    recommendations=["check.ip_config.rec.check_dhcp"],
                    raw_data=raw_data
                )]
                
            if ip.startswith("169.254."):
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.FAIL,
                    category=CheckCategory.IP_CONFIG,
                    title_key="check.ip_config.title",
                    summary_key="check.ip_config.fail_apipa",
                    details=details,
                    recommendations=["check.ip_config.rec.restart_router"],
                    raw_data=raw_data
                )]
                
            if not gateway:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.WARNING,
                    category=CheckCategory.IP_CONFIG,
                    title_key="check.ip_config.title",
                    summary_key="check.ip_config.warn_no_gateway",
                    details=details,
                    recommendations=["check.ip_config.rec.check_gateway"],
                    raw_data=raw_data
                )]
                
            return [CheckResult(
                name=self.name(),
                status=CheckStatus.PASS,
                category=CheckCategory.IP_CONFIG,
                title_key="check.ip_config.title",
                summary_key="check.ip_config.pass",
                summary_params={"ip": ip, "gateway": gateway or "N/A"},
                details=details,
                raw_data=raw_data
            )]
        except Exception as e:
            return [CheckResult(
                name=self.name(),
                status=CheckStatus.FAIL,
                category=CheckCategory.IP_CONFIG,
                title_key="check.ip_config.title",
                summary_key="check.error",
                details=[f"Error checking IP config: {str(e)}"],
                raw_data={"error": str(e)}
            )]
