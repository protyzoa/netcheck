from netcheck.core.base_checker import BaseChecker
from netcheck.core.models import CheckResult, CheckStatus, CheckCategory
import netcheck.core.platform_utils as platform_utils

class DNSChecker(BaseChecker):
    def name(self) -> str:
        return "dns"
        
    def depends_on(self) -> list[str]:
        return ["internet"]
        
    def check(self) -> list[CheckResult]:
        try:
            servers = platform_utils.get_dns_servers()
            local_res = platform_utils.dns_resolve("google.com")
            public_res = platform_utils.dns_resolve("google.com", server="8.8.8.8")
            
            details = [f"DNS Servers: {', '.join(servers)}", f"Local resolution: {'Success' if local_res.success else 'Failed'} ({local_res.response_time_ms}ms)", f"Public resolution: {'Success' if public_res.success else 'Failed'} ({public_res.response_time_ms}ms)"]
            raw_data = {"servers": servers, "local_res": vars(local_res), "public_res": vars(public_res)}
            
            if local_res.success and public_res.success:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.PASS,
                    category=CheckCategory.DNS,
                    title_key="check.dns.title",
                    summary_key="check.dns.pass",
                    summary_params={"server": servers[0] if servers else "8.8.8.8"},
                    details=details,
                    raw_data=raw_data
                )]
            elif not local_res.success and public_res.success:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.WARNING,
                    category=CheckCategory.DNS,
                    title_key="check.dns.title",
                    summary_key="check.dns.warn_local_issue",
                    details=details,
                    recommendations=["check.dns.rec.change_dns"],
                    raw_data=raw_data
                )]
            else:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.FAIL,
                    category=CheckCategory.DNS,
                    title_key="check.dns.title",
                    summary_key="check.dns.fail",
                    details=details,
                    recommendations=["check.dns.rec.change_dns", "check.dns.rec.flush_dns"],
                    raw_data=raw_data
                )]
        except Exception as e:
            return [CheckResult(
                name=self.name(),
                status=CheckStatus.FAIL,
                category=CheckCategory.DNS,
                title_key="check.dns.title",
                summary_key="check.error",
                details=[f"Error checking DNS: {str(e)}"],
                raw_data={"error": str(e)}
            )]
