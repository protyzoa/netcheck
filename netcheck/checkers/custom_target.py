from netcheck.core.base_checker import BaseChecker
from netcheck.core.models import CheckResult, CheckStatus, CheckCategory, CustomTarget, CheckType
import netcheck.core.platform_utils as platform_utils

class CustomTargetChecker(BaseChecker):
    def __init__(self, targets: list[CustomTarget]):
        self.targets = targets

    def name(self) -> str:
        return "custom_target"
        
    def depends_on(self) -> list[str]:
        return []
        
    def check(self) -> list[CheckResult]:
        results = []
        try:
            if not self.targets:
                return []
                
            for target in self.targets:
                if not target.enabled:
                    continue
                    
                status = CheckStatus.FAIL
                details = []
                raw_data = {"target": vars(target)}
                
                try:
                    if target.check_type == CheckType.PING:
                        res = platform_utils.ping(target.host)
                        details = [f"Loss: {res.packet_loss_pct}%", f"Avg Latency: {res.avg_ms}ms"]
                        raw_data["result"] = vars(res)
                        if res.packet_loss_pct == 0:
                            status = CheckStatus.PASS
                        elif res.packet_loss_pct < 100:
                            status = CheckStatus.WARNING
                    elif target.check_type == CheckType.DNS:
                        res = platform_utils.dns_resolve(target.host)
                        details = [f"Addresses: {', '.join(res.addresses)}", f"Time: {res.response_time_ms}ms"]
                        raw_data["result"] = vars(res)
                        if res.success:
                            status = CheckStatus.PASS
                    elif target.check_type == CheckType.HTTP:
                        res = platform_utils.check_http(target.host)
                        details = [f"Status Code: {res.status_code}", f"Time: {res.response_time_ms}ms"]
                        raw_data["result"] = vars(res)
                        if res.success:
                            status = CheckStatus.PASS
                    elif target.check_type == CheckType.PORT:
                        res = platform_utils.check_port(target.host, target.port)
                        details = [f"Time: {res.response_time_ms}ms"]
                        raw_data["result"] = vars(res)
                        if res.success:
                            status = CheckStatus.PASS
                except Exception as e:
                    details = [f"Error: {str(e)}"]
                    raw_data["error"] = str(e)
                    
                # Build summary_params based on check type and result
                summary_params: dict = {"name": target.name}
                if target.check_type == CheckType.PING and status != CheckStatus.FAIL:
                    summary_params["avg_ms"] = round(res.avg_ms, 1) if hasattr(res, "avg_ms") else 0
                    summary_key = "check.custom.pass_ping" if status == CheckStatus.PASS else "check.custom.fail_ping"
                elif target.check_type == CheckType.PING:
                    summary_key = "check.custom.fail_ping"
                elif target.check_type == CheckType.DNS:
                    summary_key = "check.custom.pass_dns" if status == CheckStatus.PASS else "check.custom.fail_dns"
                elif target.check_type == CheckType.HTTP:
                    summary_params["status_code"] = res.status_code if hasattr(res, "status_code") else 0
                    summary_key = "check.custom.pass_http" if status == CheckStatus.PASS else "check.custom.fail_http"
                elif target.check_type == CheckType.PORT:
                    summary_params["port"] = target.port or 0
                    summary_key = "check.custom.pass_port" if status == CheckStatus.PASS else "check.custom.fail_port"
                else:
                    summary_key = "check.custom.pass" if status == CheckStatus.PASS else "check.custom.fail"

                results.append(CheckResult(
                    name=f"custom_{target.id}",
                    status=status,
                    category=CheckCategory.CUSTOM,
                    title_key="check.custom.title",
                    summary_key=summary_key,
                    summary_params=summary_params,
                    details=details,
                    raw_data=raw_data
                ))
            return results
        except Exception as e:
            return [CheckResult(
                name=self.name(),
                status=CheckStatus.FAIL,
                category=CheckCategory.CUSTOM,
                title_key="check.custom.error_title",
                summary_key="check.error",
                details=[f"Error checking custom targets: {str(e)}"],
                raw_data={"error": str(e)}
            )]
