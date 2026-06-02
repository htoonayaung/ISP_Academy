import re

from fastapi import HTTPException, status


BLOCKED_PATTERNS = [
    ";",
    "&&",
    "||",
    "|",
    ">",
    "<",
    "`",
    "$(",
    "/bin/sh",
    "bash",
    "sh -c",
    "docker",
    "containerlab",
    "mount",
    "wget",
    "curl",
    " nc ",
    "python",
    "perl",
    "apk",
    "apt",
    "yum",
    "rm ",
    "chmod",
    "chown",
    "/opt",
    "/var/run",
    "/etc/passwd",
]

FRR_PREFIXES = (
    "show ",
    "do show ",
    "configure terminal",
    "interface ",
    "router ospf",
    "router bgp",
    "network ",
    "neighbor ",
    "ip route ",
    "no ",
    "exit",
    "end",
    "write memory",
)

LINUX_COMMANDS = (
    "uname",
    "uname -a",
    "ip addr",
    "ip route",
)


class ConsoleCommandPolicy:
    def validate(self, kind: str, command: str) -> str:
        normalized = self._normalize(command)
        self._block_dangerous(normalized)
        if kind.lower() == "frr":
            if normalized.startswith(FRR_PREFIXES):
                return normalized
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Command blocked by safety policy")
        if kind.lower() == "linux":
            if normalized in LINUX_COMMANDS or re.fullmatch(r"ping -c 3 [A-Za-z0-9:.\\-]+", normalized):
                return normalized
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Linux console supports only read-only safe commands")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Console not available for this node")

    def validate_batch(self, kind: str, commands: list[str]) -> list[str]:
        if kind.lower() != "frr":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Batch console is available only for FRR nodes")
        return [self.validate(kind, command) for command in commands]

    @staticmethod
    def _normalize(command: str) -> str:
        return " ".join(command.strip().split())

    @staticmethod
    def _block_dangerous(command: str) -> None:
        lowered = f" {command.lower()} "
        for pattern in BLOCKED_PATTERNS:
            if pattern in lowered or pattern.strip() in command.lower():
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Command blocked by safety policy")
