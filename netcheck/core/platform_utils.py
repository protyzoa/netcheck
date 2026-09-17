"""OS-specific command wrappers for network diagnostics.

Abstracts platform differences for ping, traceroute, adapter info,
DNS resolution, HTTP checks, port checks, and WiFi info.
"""

import platform
import re
import socket
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

import psutil

# Lazy import for dns.resolver to avoid import errors if dnspython not installed
try:
    import dns.resolver
    import dns.exception
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False


# ---------------------------------------------------------------------------
# Data classes for results
# ---------------------------------------------------------------------------

@dataclass
class PingResult:
    """Result of a ping operation."""
    success: bool
    packets_sent: int = 0
    packets_received: int = 0
    packet_loss_pct: float = 100.0
    min_ms: float = 0.0
    avg_ms: float = 0.0
    max_ms: float = 0.0
    error_message: str = ""


@dataclass
class TracerouteHop:
    """A single hop in a traceroute."""
    hop_number: int
    ip: Optional[str] = None  # None if timeout
    rtt_ms: Optional[float] = None  # None if timeout


@dataclass
class AdapterInfo:
    """Network adapter information."""
    name: str
    is_up: bool
    speed_mbps: int = 0
    mtu: int = 0
    ipv4_address: Optional[str] = None
    ipv4_netmask: Optional[str] = None
    mac_address: Optional[str] = None
    is_loopback: bool = False


@dataclass
class DNSResolveResult:
    """Result of a DNS resolution."""
    success: bool
    addresses: list[str] = field(default_factory=list)
    error_message: str = ""
    response_time_ms: float = 0.0


@dataclass
class HTTPCheckResult:
    """Result of an HTTP check."""
    success: bool
    status_code: int = 0
    response_time_ms: float = 0.0
    error_message: str = ""


@dataclass
class PortCheckResult:
    """Result of a TCP port check."""
    success: bool
    response_time_ms: float = 0.0
    error_message: str = ""


@dataclass
class WiFiInfo:
    """WiFi connection information."""
    ssid: str = ""
    signal_strength_pct: int = 0
    bssid: str = ""
    channel: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SYSTEM = platform.system()  # "Windows", "Linux", "Darwin"


def _run_cmd(args: list[str], timeout: int = 15) -> tuple[str, str, int]:
    """Run a subprocess command and return (stdout, stderr, returncode)."""
    try:
        # On Windows, hide the console window
        startupinfo = None
        if _SYSTEM == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            startupinfo=startupinfo,
            encoding="utf-8",
            errors="replace",
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", -1
    except FileNotFoundError:
        return "", f"Command not found: {args[0]}", -2
    except Exception as e:
        return "", str(e), -3


# ---------------------------------------------------------------------------
# Ping
# ---------------------------------------------------------------------------

def ping(host: str, count: int = 4, timeout: int = 3) -> PingResult:
    """Ping a host using the OS native ping command.

    Args:
        host: Hostname or IP address to ping.
        count: Number of ping packets to send.
        timeout: Timeout per packet in seconds.

    Returns:
        PingResult with parsed statistics.
    """
    try:
        if _SYSTEM == "Windows":
            # Windows: timeout is in milliseconds
            args = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
        elif _SYSTEM == "Darwin":
            args = ["ping", "-c", str(count), "-t", str(timeout), host]
        else:  # Linux
            args = ["ping", "-c", str(count), "-W", str(timeout), host]

        stdout, stderr, rc = _run_cmd(args, timeout=count * timeout + 10)

        if not stdout:
            return PingResult(
                success=False,
                error_message=stderr or "No output from ping command",
            )

        return _parse_ping_output(stdout, count)

    except Exception as e:
        return PingResult(success=False, error_message=str(e))


def _parse_ping_output(output: str, count: int) -> PingResult:
    """Parse ping command output across platforms."""
    result = PingResult(success=False, packets_sent=count)

    # Parse packet statistics
    # Windows: "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)"
    # Linux/macOS: "4 packets transmitted, 4 received, 0% packet loss"
    loss_match = re.search(r"(\d+)%\s*(?:loss|packet loss|perdida)", output, re.IGNORECASE)
    if loss_match:
        result.packet_loss_pct = float(loss_match.group(1))

    recv_match = re.search(r"Received\s*=\s*(\d+)", output, re.IGNORECASE)
    if recv_match:
        result.packets_received = int(recv_match.group(1))
    else:
        recv_match = re.search(r"(\d+)\s+received", output, re.IGNORECASE)
        if recv_match:
            result.packets_received = int(recv_match.group(1))
        else:
            result.packets_received = round(count * (100 - result.packet_loss_pct) / 100)

    sent_match = re.search(r"Sent\s*=\s*(\d+)", output, re.IGNORECASE)
    if sent_match:
        result.packets_sent = int(sent_match.group(1))
    else:
        sent_match = re.search(r"(\d+)\s+packets?\s+transmitted", output, re.IGNORECASE)
        if sent_match:
            result.packets_sent = int(sent_match.group(1))

    # Parse RTT statistics
    # Windows: "Minimum = 1ms, Maximum = 3ms, Average = 2ms"
    # Linux/macOS: "rtt min/avg/max/mdev = 1.234/2.345/3.456/0.567 ms"
    rtt_match = re.search(
        r"(?:rtt|round-trip)\s+min/avg/max(?:/[a-z]+)?\s*=\s*"
        r"([\d.]+)/([\d.]+)/([\d.]+)",
        output, re.IGNORECASE,
    )
    if rtt_match:
        result.min_ms = float(rtt_match.group(1))
        result.avg_ms = float(rtt_match.group(2))
        result.max_ms = float(rtt_match.group(3))
    else:
        # Windows format
        min_match = re.search(r"Minimum\s*=\s*(\d+)\s*ms", output, re.IGNORECASE)
        max_match = re.search(r"Maximum\s*=\s*(\d+)\s*ms", output, re.IGNORECASE)
        avg_match = re.search(r"Average\s*=\s*(\d+)\s*ms", output, re.IGNORECASE)
        if min_match:
            result.min_ms = float(min_match.group(1))
        if max_match:
            result.max_ms = float(max_match.group(1))
        if avg_match:
            result.avg_ms = float(avg_match.group(1))

    result.success = result.packets_received > 0
    return result


# ---------------------------------------------------------------------------
# Traceroute
# ---------------------------------------------------------------------------

def traceroute(host: str, max_hops: int = 15, timeout: int = 3) -> list[TracerouteHop]:
    """Run traceroute to a host.

    Args:
        host: Target hostname or IP.
        max_hops: Maximum number of hops.
        timeout: Timeout per hop in seconds.

    Returns:
        List of TracerouteHop objects.
    """
    try:
        if _SYSTEM == "Windows":
            args = ["tracert", "-d", "-h", str(max_hops), "-w", str(timeout * 1000), host]
        else:
            args = ["traceroute", "-n", "-m", str(max_hops), "-w", str(timeout), host]

        stdout, stderr, rc = _run_cmd(args, timeout=max_hops * timeout + 15)
        if not stdout:
            return []

        return _parse_traceroute_output(stdout)

    except Exception:
        return []


def _parse_traceroute_output(output: str) -> list[TracerouteHop]:
    """Parse traceroute output."""
    hops = []
    for line in output.splitlines():
        line = line.strip()
        # Match lines starting with a hop number
        hop_match = re.match(r"^\s*(\d+)\s+", line)
        if not hop_match:
            continue

        hop_num = int(hop_match.group(1))

        # Check for timeout (all *)
        if re.search(r"\*\s+\*\s+\*", line):
            hops.append(TracerouteHop(hop_number=hop_num))
            continue

        # Extract IP address
        ip_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
        ip = ip_match.group(1) if ip_match else None

        # Extract RTT (first numeric value that looks like ms)
        rtt_match = re.search(r"(\d+(?:\.\d+)?)\s*ms", line)
        rtt = float(rtt_match.group(1)) if rtt_match else None

        hops.append(TracerouteHop(hop_number=hop_num, ip=ip, rtt_ms=rtt))

    return hops


# ---------------------------------------------------------------------------
# Adapter Info
# ---------------------------------------------------------------------------

def get_adapter_info() -> list[AdapterInfo]:
    """Get information about all network adapters using psutil.

    Returns:
        List of AdapterInfo objects.
    """
    adapters = []
    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        for name, stat in stats.items():
            info = AdapterInfo(
                name=name,
                is_up=stat.isup,
                speed_mbps=stat.speed,
                mtu=stat.mtu,
                is_loopback=(name.lower() in ("lo", "loopback", "lo0")
                             or name.startswith("Loopback")),
            )

            # Get addresses for this adapter
            if name in addrs:
                for addr in addrs[name]:
                    if addr.family == socket.AF_INET:
                        info.ipv4_address = addr.address
                        info.ipv4_netmask = addr.netmask
                    elif addr.family == psutil.AF_LINK:
                        info.mac_address = addr.address

            adapters.append(info)

    except Exception:
        pass

    return adapters


# ---------------------------------------------------------------------------
# Default Gateway
# ---------------------------------------------------------------------------

def get_default_gateway() -> Optional[str]:
    """Get the default gateway IP address.

    Returns:
        Gateway IP as string, or None if not found.
    """
    try:
        if _SYSTEM == "Windows":
            stdout, _, _ = _run_cmd(["ipconfig"], timeout=10)
            # Find "Default Gateway" lines with an IP
            for line in stdout.splitlines():
                if "default gateway" in line.lower() or "puerta de enlace" in line.lower() or "gateway predeterminado" in line.lower():
                    ip_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                    if ip_match:
                        return ip_match.group(1)
        elif _SYSTEM == "Linux":
            stdout, _, _ = _run_cmd(["ip", "route", "show", "default"], timeout=5)
            match = re.search(r"default via (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", stdout)
            if match:
                return match.group(1)
        elif _SYSTEM == "Darwin":
            stdout, _, _ = _run_cmd(["route", "-n", "get", "default"], timeout=5)
            match = re.search(r"gateway:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", stdout)
            if match:
                return match.group(1)
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# DNS Servers
# ---------------------------------------------------------------------------

def get_dns_servers() -> list[str]:
    """Get configured DNS server addresses.

    Returns:
        List of DNS server IP strings.
    """
    servers = []
    try:
        if _SYSTEM == "Windows":
            stdout, _, _ = _run_cmd(["ipconfig", "/all"], timeout=10)
            in_dns = False
            for line in stdout.splitlines():
                if "dns server" in line.lower() or "servidores dns" in line.lower():
                    in_dns = True
                    ip_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                    if ip_match:
                        servers.append(ip_match.group(1))
                elif in_dns:
                    # Continuation lines for additional DNS servers
                    ip_match = re.match(r"^\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                    if ip_match:
                        servers.append(ip_match.group(1))
                    else:
                        in_dns = False
        else:
            # Linux / macOS: parse /etc/resolv.conf
            try:
                with open("/etc/resolv.conf", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("nameserver"):
                            parts = line.split()
                            if len(parts) >= 2:
                                servers.append(parts[1])
            except FileNotFoundError:
                pass

            # macOS: also try scutil
            if _SYSTEM == "Darwin" and not servers:
                stdout, _, _ = _run_cmd(["scutil", "--dns"], timeout=5)
                for line in stdout.splitlines():
                    match = re.search(r"nameserver\[\d+\]\s*:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                    if match and match.group(1) not in servers:
                        servers.append(match.group(1))

    except Exception:
        pass

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in servers:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


# ---------------------------------------------------------------------------
# DNS Resolve
# ---------------------------------------------------------------------------

def dns_resolve(hostname: str, server: Optional[str] = None) -> DNSResolveResult:
    """Resolve a hostname to IP addresses.

    Args:
        hostname: Domain name to resolve.
        server: Optional DNS server to use. If None, uses system default.

    Returns:
        DNSResolveResult with resolution details.
    """
    start = time.perf_counter()
    try:
        if HAS_DNSPYTHON:
            resolver = dns.resolver.Resolver()
            if server:
                resolver.nameservers = [server]
            resolver.lifetime = 5.0

            answers = resolver.resolve(hostname, "A")
            elapsed = (time.perf_counter() - start) * 1000
            addrs = [rdata.address for rdata in answers]
            return DNSResolveResult(
                success=True,
                addresses=addrs,
                response_time_ms=round(elapsed, 1),
            )
        else:
            # Fallback to socket (can't specify server)
            infos = socket.getaddrinfo(hostname, None, socket.AF_INET)
            elapsed = (time.perf_counter() - start) * 1000
            addrs = list({info[4][0] for info in infos})
            return DNSResolveResult(
                success=True,
                addresses=addrs,
                response_time_ms=round(elapsed, 1),
            )

    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return DNSResolveResult(
            success=False,
            error_message=str(e),
            response_time_ms=round(elapsed, 1),
        )


# ---------------------------------------------------------------------------
# HTTP Check
# ---------------------------------------------------------------------------

def check_http(url: str, timeout: int = 5) -> HTTPCheckResult:
    """Check if a URL is accessible via HTTP(S).

    Args:
        url: Full URL to check (e.g. "https://google.com").
        timeout: Request timeout in seconds.

    Returns:
        HTTPCheckResult with status details.
    """
    import urllib.request
    import urllib.error

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "NetCheck/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.perf_counter() - start) * 1000
            return HTTPCheckResult(
                success=True,
                status_code=resp.status,
                response_time_ms=round(elapsed, 1),
            )
    except urllib.error.HTTPError as e:
        elapsed = (time.perf_counter() - start) * 1000
        # HTTP errors (4xx, 5xx) still mean the server is reachable
        return HTTPCheckResult(
            success=True,
            status_code=e.code,
            response_time_ms=round(elapsed, 1),
        )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return HTTPCheckResult(
            success=False,
            error_message=str(e),
            response_time_ms=round(elapsed, 1),
        )


# ---------------------------------------------------------------------------
# Port Check
# ---------------------------------------------------------------------------

def check_port(host: str, port: int, timeout: int = 3) -> PortCheckResult:
    """Check if a TCP port is open on a host.

    Args:
        host: Hostname or IP address.
        port: TCP port number.
        timeout: Connection timeout in seconds.

    Returns:
        PortCheckResult with status details.
    """
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = (time.perf_counter() - start) * 1000
            return PortCheckResult(
                success=True,
                response_time_ms=round(elapsed, 1),
            )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return PortCheckResult(
            success=False,
            error_message=str(e),
            response_time_ms=round(elapsed, 1),
        )


# ---------------------------------------------------------------------------
# WiFi Info
# ---------------------------------------------------------------------------

def get_wifi_info() -> Optional[WiFiInfo]:
    """Get WiFi connection information.

    Returns:
        WiFiInfo object if connected via WiFi, None otherwise.
    """
    try:
        if _SYSTEM == "Windows":
            return _get_wifi_info_windows()
        elif _SYSTEM == "Linux":
            return _get_wifi_info_linux()
        elif _SYSTEM == "Darwin":
            return _get_wifi_info_macos()
    except Exception:
        pass
    return None


def _get_wifi_info_windows() -> Optional[WiFiInfo]:
    """Get WiFi info on Windows via netsh."""
    stdout, _, rc = _run_cmd(["netsh", "wlan", "show", "interfaces"], timeout=5)
    if rc != 0 or not stdout:
        return None

    info = WiFiInfo()
    for line in stdout.splitlines():
        line = line.strip()
        # SSID (but not BSSID)
        if re.match(r"^\s*SSID\s*:", line, re.IGNORECASE):
            parts = line.split(":", 1)
            if len(parts) == 2:
                info.ssid = parts[1].strip()
        elif re.match(r"^\s*BSSID\s*:", line, re.IGNORECASE):
            parts = line.split(":", 1)
            if len(parts) == 2:
                info.bssid = parts[1].strip()
        elif re.match(r"^\s*Signal\s*:", line, re.IGNORECASE) or re.match(r"^\s*Sinyal\s*:", line, re.IGNORECASE):
            match = re.search(r"(\d+)%", line)
            if match:
                info.signal_strength_pct = int(match.group(1))
        elif re.match(r"^\s*Channel\s*:", line, re.IGNORECASE):
            match = re.search(r"(\d+)", line.split(":", 1)[1])
            if match:
                info.channel = int(match.group(1))

    return info if info.ssid else None


def _get_wifi_info_linux() -> Optional[WiFiInfo]:
    """Get WiFi info on Linux via nmcli or iwconfig."""
    # Try nmcli first
    stdout, _, rc = _run_cmd(
        ["nmcli", "-t", "-f", "active,ssid,signal,bssid,chan", "dev", "wifi"],
        timeout=5,
    )
    if rc == 0 and stdout:
        for line in stdout.splitlines():
            parts = line.split(":")
            if len(parts) >= 5 and parts[0].lower() == "yes":
                info = WiFiInfo(
                    ssid=parts[1],
                    signal_strength_pct=int(parts[2]) if parts[2].isdigit() else 0,
                    bssid=parts[3],
                    channel=int(parts[4]) if parts[4].isdigit() else 0,
                )
                return info

    # Fallback to iwconfig
    stdout, _, rc = _run_cmd(["iwconfig"], timeout=5)
    if rc == 0 and stdout:
        info = WiFiInfo()
        ssid_match = re.search(r'ESSID:"([^"]*)"', stdout)
        if ssid_match:
            info.ssid = ssid_match.group(1)
        signal_match = re.search(r"Signal level[=:](-?\d+)", stdout)
        if signal_match:
            # Convert dBm to approximate percentage
            dbm = int(signal_match.group(1))
            info.signal_strength_pct = max(0, min(100, 2 * (dbm + 100)))
        if info.ssid:
            return info

    return None


def _get_wifi_info_macos() -> Optional[WiFiInfo]:
    """Get WiFi info on macOS."""
    airport_path = (
        "/System/Library/PrivateFrameworks/Apple80211.framework"
        "/Versions/Current/Resources/airport"
    )
    stdout, _, rc = _run_cmd([airport_path, "-I"], timeout=5)
    if rc != 0 or not stdout:
        return None

    info = WiFiInfo()
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("SSID:"):
            info.ssid = line.split(":", 1)[1].strip()
        elif line.startswith("BSSID:"):
            info.bssid = line.split(":", 1)[1].strip()
        elif line.startswith("agrCtlRSSI:"):
            try:
                rssi = int(line.split(":", 1)[1].strip())
                info.signal_strength_pct = max(0, min(100, 2 * (rssi + 100)))
            except ValueError:
                pass
        elif line.startswith("channel:"):
            try:
                info.channel = int(line.split(":", 1)[1].strip().split(",")[0])
            except ValueError:
                pass

    return info if info.ssid else None


# ---------------------------------------------------------------------------
# Media Connected Check
# ---------------------------------------------------------------------------

def is_media_connected(adapter_name: str) -> bool:
    """Check if physical media is connected for a given adapter.

    Args:
        adapter_name: Name of the network adapter.

    Returns:
        True if media is connected (adapter is up).
    """
    try:
        stats = psutil.net_if_stats()
        if adapter_name in stats:
            return stats[adapter_name].isup
    except Exception:
        pass
    return False

