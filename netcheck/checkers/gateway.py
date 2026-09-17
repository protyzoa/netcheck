from netcheck.core.base_checker import BaseChecker
from netcheck.core.models import CheckResult, CheckStatus, CheckCategory
import netcheck.core.platform_utils as platform_utils

class GatewayChecker(BaseChecker):
    def name(self) -> str:
        return "gateway"
        
    def depends_on(self) -> list[str]:
        return ["ip_config"]
        
    def check(self) -> list[CheckResult]:
        try:
            gateway = platform_utils.get_default_gateway()
            if not gateway:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.FAIL,
                    category=CheckCategory.CONNECTIVITY,
                    title_key="check.gateway.title",
                    summary_key="check.gateway.fail_no_gateway",
                    details=["No default gateway configured."],
                    raw_data={}
                )]
                
            ping_res = platform_utils.ping(gateway, count=4)
            details = [f"Gateway: {gateway}", f"Packets Sent: {ping_res.packets_sent}", f"Packets Received: {ping_res.packets_received}", f"Loss: {ping_res.packet_loss_pct}%"]
            raw_data = {"gateway": gateway, "ping": vars(ping_res)}
            
            if ping_res.packet_loss_pct == 100:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.FAIL,
                    category=CheckCategory.CONNECTIVITY,
                    title_key="check.gateway.title",
                    summary_key="check.gateway.fail_unreachable",
                    details=details,
                    recommendations=["check.gateway.rec.check_cable", "check.gateway.rec.restart_router"],
                    raw_data=raw_data
                )]
            elif ping_res.packet_loss_pct > 0:
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.WARNING,
                    category=CheckCategory.CONNECTIVITY,
                    title_key="check.gateway.title",
                    summary_key="check.gateway.warn_loss",
                    summary_params={"loss": ping_res.packet_loss_pct},
                    details=details,
                    recommendations=["check.gateway.rec.check_wifi", "check.gateway.rec.restart_router"],
                    raw_data=raw_data
                )]
            else:
                details.append(f"Avg Latency: {ping_res.avg_ms}ms")
                return [CheckResult(
                    name=self.name(),
                    status=CheckStatus.PASS,
                    category=CheckCategory.CONNECTIVITY,
                    title_key="check.gateway.title",
                    summary_key="check.gateway.pass",
                    summary_params={"avg_ms": round(ping_res.avg_ms, 1)},
                    details=details,
                    raw_data=raw_data
                )]
        except Exception as e:
            return [CheckResult(
                name=self.name(),
                status=CheckStatus.FAIL,
                category=CheckCategory.CONNECTIVITY,
                title_key="check.gateway.title",
                summary_key="check.error",
                details=[f"Error checking gateway: {str(e)}"],
                raw_data={"error": str(e)}
            )]
