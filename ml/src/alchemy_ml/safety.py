"""Safety classifier for AlchemyCLI AI.

Classifies commands as safe, warning, or dangerous based on
pattern matching and heuristic analysis. Independent of the
ML retrieval model.
"""

from __future__ import annotations

import re
from enum import Enum

from .models import RiskLevel


# Dangerous command patterns — these can cause data loss or system damage
DANGEROUS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # File system destruction
    (re.compile(r"\brm\s+(-[rfvI]*\s+)*(/|~|\$HOME|\$\{HOME\}|\.\.)"), "Recursive delete on critical path"),
    (re.compile(r"\brm\s+-rf\b"), "Force recursive delete"),
    (re.compile(r"\bmkfs\b"), "Format filesystem"),
    (re.compile(r"\bdd\s+if="), "Raw disk write"),
    (re.compile(r">\s*/dev/sd[a-z]"), "Write to raw device"),
    (re.compile(r"\bshred\b"), "Secure file deletion"),

    # Kubernetes destructive
    (re.compile(r"kubectl\s+delete\s+(namespace|ns)\b"), "Delete Kubernetes namespace"),
    (re.compile(r"kubectl\s+delete\s+.*--all\b"), "Delete all resources"),
    (re.compile(r"kubectl\s+drain\b"), "Drain Kubernetes node"),
    (re.compile(r"kubectl\s+cordon\b"), "Cordon Kubernetes node"),

    # Docker destructive
    (re.compile(r"docker\s+system\s+prune\s+-a"), "Remove ALL Docker data"),
    (re.compile(r"docker\s+volume\s+prune"), "Remove Docker volumes"),
    (re.compile(r"docker\s+container\s+prune"), "Remove stopped containers"),

    # Git destructive
    (re.compile(r"git\s+push\s+.*--force\b"), "Force push to remote"),
    (re.compile(r"git\s+push\s+-f\b"), "Force push to remote"),
    (re.compile(r"git\s+reset\s+--hard\b"), "Hard reset discards changes"),
    (re.compile(r"git\s+clean\s+-[dxf]+"), "Remove untracked files"),

    # Terraform destructive
    (re.compile(r"terraform\s+destroy\b"), "Destroy infrastructure"),
    (re.compile(r"terraform\s+state\s+rm\b"), "Remove from state"),
    (re.compile(r"terraform\s+force-unlock\b"), "Force unlock state"),

    # System destructive
    (re.compile(r"\bchmod\s+-R\s+777\s+/"), "Set world-writable on root"),
    (re.compile(r"\bchown\s+-R\s+.*\s+/\s*$"), "Change ownership of root"),
    (re.compile(r":\(\)\s*\{"), "Fork bomb pattern"),
    (re.compile(r"\bkill\s+-9\s+-1\b"), "Kill all processes"),
    (re.compile(r"\bkillall\b"), "Kill all matching processes"),
    (re.compile(r"\bsystemctl\s+stop\b"), "Stop system service"),
    (re.compile(r"\bsystemctl\s+disable\b"), "Disable system service"),

    # Database destructive
    (re.compile(r"\bDROP\s+(DATABASE|TABLE|INDEX)\b", re.IGNORECASE), "Drop database object"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "Truncate table"),
    (re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE), "Delete data"),

    # Cloud destructive
    (re.compile(r"aws\s+.*\s+delete-"), "AWS delete operation"),
    (re.compile(r"gcloud\s+.*\s+delete\b"), "GCloud delete operation"),
    (re.compile(r"az\s+.*\s+delete\b"), "Azure delete operation"),
]

# Warning patterns — these modify state but are recoverable
WARNING_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Kubernetes modifying
    (re.compile(r"kubectl\s+apply\b"), "Apply Kubernetes manifest"),
    (re.compile(r"kubectl\s+rollout\s+restart\b"), "Restart deployment"),
    (re.compile(r"kubectl\s+rollout\s+undo\b"), "Rollback deployment"),
    (re.compile(r"kubectl\s+scale\b"), "Scale deployment"),
    (re.compile(r"kubectl\s+edit\b"), "Edit Kubernetes resource"),
    (re.compile(r"kubectl\s+patch\b"), "Patch Kubernetes resource"),
    (re.compile(r"kubectl\s+delete\s+pod\b"), "Delete pod"),
    (re.compile(r"kubectl\s+taint\b"), "Taint node"),
    (re.compile(r"kubectl\s+label\b"), "Label resource"),
    (re.compile(r"kubectl\s+annotate\b"), "Annotate resource"),

    # Docker modifying
    (re.compile(r"docker\s+stop\b"), "Stop container"),
    (re.compile(r"docker\s+restart\b"), "Restart container"),
    (re.compile(r"docker\s+rm\b"), "Remove container"),
    (re.compile(r"docker\s+rmi\b"), "Remove image"),
    (re.compile(r"docker\s+system\s+prune\b"), "Docker system prune"),
    (re.compile(r"docker\s+image\s+prune\b"), "Prune images"),
    (re.compile(r"docker\s+push\b"), "Push image"),

    # Git modifying
    (re.compile(r"git\s+reset\b"), "Git reset"),
    (re.compile(r"git\s+revert\b"), "Git revert"),
    (re.compile(r"git\s+merge\b"), "Git merge"),
    (re.compile(r"git\s+rebase\b"), "Git rebase"),
    (re.compile(r"git\s+stash\s+drop\b"), "Drop stash"),
    (re.compile(r"git\s+branch\s+-[dD]\b"), "Delete branch"),

    # Terraform modifying
    (re.compile(r"terraform\s+apply\b"), "Apply infrastructure changes"),
    (re.compile(r"terraform\s+import\b"), "Import resource"),
    (re.compile(r"terraform\s+state\s+mv\b"), "Move state resource"),

    # System modifying
    (re.compile(r"\bchmod\b"), "Change permissions"),
    (re.compile(r"\bchown\b"), "Change ownership"),
    (re.compile(r"\bsystemctl\s+(start|restart|enable)\b"), "Modify service"),
    (re.compile(r"\bkill\b"), "Kill process"),

    # Package managers
    (re.compile(r"pip\s+install\b"), "Install Python package"),
    (re.compile(r"pip\s+uninstall\b"), "Uninstall Python package"),
    (re.compile(r"npm\s+install\b"), "Install npm package"),
    (re.compile(r"cargo\s+install\b"), "Install Rust crate"),
    (re.compile(r"go\s+install\b"), "Install Go package"),

    # Kafka modifying
    (re.compile(r"kafka-topics.*--(create|delete|alter)\b"), "Modify Kafka topic"),
    (re.compile(r"kafka-consumer-groups.*--reset-offsets\b"), "Reset consumer offsets"),
]


def classify_risk(command: str) -> RiskLevel:
    """Classify the risk level of a command.

    Args:
        command: The shell command to classify.

    Returns:
        RiskLevel enum value.
    """
    # Check dangerous patterns first
    for pattern, _reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return RiskLevel.DANGEROUS

    # Check warning patterns
    for pattern, _reason in WARNING_PATTERNS:
        if pattern.search(command):
            return RiskLevel.WARNING

    return RiskLevel.SAFE


def get_risk_reason(command: str) -> str:
    """Get human-readable reason for a command's risk level.

    Args:
        command: The shell command to analyze.

    Returns:
        Reason string, or empty if safe.
    """
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return reason

    for pattern, reason in WARNING_PATTERNS:
        if pattern.search(command):
            return reason

    return ""


def classify_risk_detailed(command: str) -> dict:
    """Get detailed risk classification.

    Returns:
        Dict with risk level, reason, and matched patterns.
    """
    matched_dangerous = []
    matched_warning = []

    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            matched_dangerous.append(reason)

    for pattern, reason in WARNING_PATTERNS:
        if pattern.search(command):
            matched_warning.append(reason)

    if matched_dangerous:
        return {
            "risk": RiskLevel.DANGEROUS,
            "reasons": matched_dangerous,
            "requires_confirmation": True,
        }

    if matched_warning:
        return {
            "risk": RiskLevel.WARNING,
            "reasons": matched_warning,
            "requires_confirmation": True,
        }

    return {
        "risk": RiskLevel.SAFE,
        "reasons": [],
        "requires_confirmation": False,
    }


def validate_no_execution(text: str) -> bool:
    """Validate that text doesn't contain execution patterns.

    AlchemyCLI AI must NEVER execute commands. This validates
    that user input isn't trying to inject execution.

    Returns:
        True if text is safe (no execution patterns), False otherwise.
    """
    execution_patterns = [
        re.compile(r"\$\(.*\)"),           # Command substitution
        re.compile(r"`.*`"),                # Backtick substitution
        re.compile(r"\|\s*sh\b"),           # Pipe to shell
        re.compile(r"\|\s*bash\b"),         # Pipe to bash
        re.compile(r";\s*exec\b"),          # Exec command
        re.compile(r"&&\s*eval\b"),         # Eval command
        re.compile(r"\bsource\s+/dev/"),    # Source from device
    ]

    for pattern in execution_patterns:
        if pattern.search(text):
            return False

    return True
