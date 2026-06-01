import re
import unicodedata

SAFE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$")
SAFE_INTERFACE_PATTERN = re.compile(r"^(eth|ens|enp|lo)[a-zA-Z0-9_.:-]{0,30}$")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    lowered = normalized.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:80] or "lab-template"


def is_safe_node_name(value: str) -> bool:
    return bool(SAFE_NAME_PATTERN.fullmatch(value))


def is_safe_interface_name(value: str) -> bool:
    return bool(SAFE_INTERFACE_PATTERN.fullmatch(value))

