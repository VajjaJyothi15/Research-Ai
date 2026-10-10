import ipaddress
import re
import socket
from urllib.parse import urlparse
from typing import Tuple
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Private and cloud metadata IP networks to block for SSRF protection
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # AWS/GCP/Azure Metadata
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_FILE_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".xlsx"}


def is_ip_blocked(ip_str: str) -> bool:
    """Checks if an IP address falls inside any blocked private or loopback range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        for net in BLOCKED_IP_NETWORKS:
            if ip in net:
                return True
        return False
    except ValueError:
        return True


def validate_url_for_ssrf(url: str) -> Tuple[bool, str]:
    """
    Validates a target URL against SSRF attacks:
    - Ensures scheme is http or https.
    - Resolves hostname via DNS and verifies IP is not in blocked private/loopback/metadata ranges.
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme.lower() not in ALLOWED_SCHEMES:
            return False, f"Invalid URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are allowed."

        hostname = parsed.hostname
        if not hostname:
            return False, "URL missing hostname."

        # Check direct IP literal hostname
        try:
            ip = ipaddress.ip_address(hostname)
            if is_ip_blocked(str(ip)):
                return False, f"Target IP address '{hostname}' is restricted (private/loopback/metadata)."
            return True, "URL validated successfully."
        except ValueError:
            pass  # It's a standard domain name, proceed to DNS resolution

        # Resolve DNS to IPs
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            resolved_ips = {info[4][0] for info in addr_info if info[4]}
            for resolved_ip in resolved_ips:
                if is_ip_blocked(resolved_ip):
                    return False, f"Domain '{hostname}' resolved to restricted IP '{resolved_ip}'."
        except socket.gaierror:
            return False, f"Could not resolve hostname '{hostname}'."

        return True, "URL validated successfully."
    except Exception as e:
        logger.error(f"SSRF validation exception for URL {url}: {e}")
        return False, f"URL validation error: {str(e)}"


def sanitize_prompt_input(text: str) -> str:
    """Basic prompt injection defense to strip aggressive system override attempts."""
    forbidden_patterns = [
        r"(?i)ignore previous instructions",
        r"(?i)system prompt:",
        r"(?i)override safety rules",
        r"(?i)reveal secret",
    ]
    cleaned = text
    for pattern in forbidden_patterns:
        cleaned = re.sub(pattern, "[FILTERED_INPUT]", cleaned)
    return cleaned


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
