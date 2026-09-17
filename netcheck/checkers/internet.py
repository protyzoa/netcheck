from netcheck.core.base_checker import BaseChecker
from netcheck.core.models import CheckResult, CheckStatus, CheckCategory
import netcheck.core.platform_utils as platform_utils

class InternetChecker(BaseChecker):
    def name(self) -> str:
        return "internet"
        
    def depends_on(self) -> list[str]:
        return ["gateway"]
        
    def check(self) -> list[CheckResult]:
        try:
            ping_google = platform_utils.ping("8.8.8.8", count=4)
            if ping_google.packet_loss_pct == 100:
                ping_cf = platform_utils.ping("1.1.1.1", count=4)
                if ping_cf.packet_loss_pct == 100:
                    tr = platform_utils.traceroute("8.8.8.8")
                    details = ["Ping to 8.8.8.8 failed.", "Ping to 1.1.1.1 failed.", "Traceroute to 8.8.8.8:"]
                    for hop in tr:
                        details.append(f"Hop {hop.hop_number}: {hop.ip} ({hop.rtt_ms}ms)")
                    
                    return [CheckResult(
                        name=self.name(),
                        status=CheckStatus.FAIL,
                        category=CheckCategory.CONNECTIVITY,
                        title_key="check.internet.title",
                        summary_key="check.internet.fail",
                        details=details,
                        recommendations=["check.internet.rec.restart_modem", "check.internet.rec.contact_isp"],
                        raw_data={"ping_google": vars(ping_google), "ping_cf": vars(ping_cf), "traceroute": [vars(h) for h in tr]}
                    )]
            
            ping_res = ping_google if ping_google.packet_loss_pct < 100 else ping_cf
            target = "8.8.8.8" if ping_google.packet_loss_pct < 100 else "1.1.1.1"
            
            details = [f"Reached {target}", f"Loss: {ping_res.packet_loss_pct}%", f"Avg Latency: {ping_res.avg_ms}ms"]
            raw_data = {"ping_res": vars(ping_res)}
            
            if ping_res.packet_loss_pct > 0:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.WARNING,
                    category=CheckCategory.CONNECTIVITY,
                    title_key="check.internet.title",
                    summary_key="check.internet.warn_loss",
                    summary_params={"loss": ping_res.packet_loss_pct},
                    details=details,
                    raw_data=raw_data
                )]
                
            return [CheckResult(
                name=self.name(),
                status=CheckStatus.PASS,
                category=CheckCategory.CONNECTIVITY,
                title_key="check.internet.title",
                summary_key="check.internet.pass",
                summary_params={"avg_ms": round(ping_res.avg_ms, 1)},
                details=details,
                raw_data=raw_data
            )]
        except Exception as e:
            return [CheckResult(
                name=self.name(),
                status=CheckStatus.FAIL,
                category=CheckCategory.CONNECTIVITY,
                title_key="check.internet.title",
                summary_key="check.error",
                details=[f"Error checking internet: {str(e)}"],
                raw_data={"error": str(e)}
            )]
