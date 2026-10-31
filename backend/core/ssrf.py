import ipaddress
import socket
from urllib.parse import urlparse
from typing import List


class SSRFSecurityError(ValueError):
    """Raised when a URL violates SSRF security boundaries."""
    pass


FORBIDDEN_NETWORKS: List[UnionNetwork] = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),       # Link-local & cloud metadata 169.254.169.254
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),          # Multicast
    ipaddress.ip_network("240.0.0.0/4"),          # Reserved
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::1/128"),              # Loopback
    ipaddress.ip_network("fc00::/7"),             # Unique local
    ipaddress.ip_network("fe80::/10"),            # Link-local
    ipaddress.ip_network("ff00::/8"),             # Multicast
]


def is_ip_forbidden(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True

    # Handle RFC 6052 NAT64 Well-Known Prefix (64:ff9b::/96)
    if ip.version == 6 and ip in ipaddress.ip_network("64:ff9b::/96"):
        embedded_ipv4 = ipaddress.IPv4Address(ip.packed[-4:])
        return is_ip_forbidden(str(embedded_ipv4))

    # Check loopback, private, link-local, multicast, reserved
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return True

    for net in FORBIDDEN_NETWORKS:
        if ip in net:
            return True

    return False


def validate_url_ssrf_safe(url: str) -> str:
    """
    Validates that a URL is safe against SSRF attacks.
    - Only allows http and https schemes.
    - Rejects URLs with embedded userinfo (e.g. user:pass@host).
    - Resolves host DNS to verify no destination IP resolves to private,
      loopback, link-local, or cloud metadata addresses.
    """
    if not url or not isinstance(url, str):
        raise SSRFSecurityError("URL cannot be empty")

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFSecurityError(f"Prohibited URL scheme '{parsed.scheme}'. Only http and https are allowed.")

    if not parsed.hostname:
        raise SSRFSecurityError("URL hostname is missing or malformed.")

    if parsed.username or parsed.password:
        raise SSRFSecurityError("Embedded credentials in URL are prohibited.")

    hostname = parsed.hostname.lower()

    # Block localhost string shortcuts
    if hostname in ("localhost", "localhost.localdomain", "127.0.0.1", "::1", "metadata.google.internal"):
        raise SSRFSecurityError(f"Target host '{hostname}' is a restricted local or metadata address.")

    # Resolve IP addresses
    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise SSRFSecurityError(f"Failed to resolve hostname '{hostname}': {str(e)}")

    if not addr_info:
        raise SSRFSecurityError(f"No address returned for hostname '{hostname}'.")

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        if is_ip_forbidden(ip_str):
            raise SSRFSecurityError(
                f"Hostname '{hostname}' resolves to restricted/private IP address: {ip_str}"
            )

    return url
