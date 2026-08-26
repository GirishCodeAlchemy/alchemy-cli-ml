"""Query preprocessing for AlchemyCLI AI.

Handles normalization, typo correction, synonym expansion,
and technology detection from natural language queries.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

from rapidfuzz import fuzz, process

# Technology aliases → canonical name
TECHNOLOGY_ALIASES: dict[str, str] = {
    # Kubernetes
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "kubectl": "kubernetes",
    "kubelet": "kubernetes",
    "kubeadm": "kubernetes",
    "minikube": "kubernetes",
    "k3s": "kubernetes",
    "kind": "kubernetes",
    "eks": "kubernetes",
    "aks": "kubernetes",
    "gke": "kubernetes",
    "openshift": "kubernetes",
    "helm": "kubernetes",
    "kustomize": "kubernetes",
    "pod": "kubernetes",
    "pods": "kubernetes",
    "deployment": "kubernetes",
    "deployments": "kubernetes",
    "statefulset": "kubernetes",
    "daemonset": "kubernetes",
    "cronjob": "kubernetes",
    "configmap": "kubernetes",
    "namespace": "kubernetes",
    "ingress": "kubernetes",
    "pvc": "kubernetes",
    "hpa": "kubernetes",
    # Docker
    "docker": "docker",
    "dockerfile": "docker",
    "container": "docker",
    "containers": "docker",
    "docker-compose": "docker",
    "docker compose": "docker",
    "compose": "docker",
    "buildx": "docker",
    "dockerhub": "docker",
    # Git
    "git": "git",
    "github": "git",
    "gitlab": "git",
    "bitbucket": "git",
    "commit": "git",
    "branch": "git",
    "merge": "git",
    "rebase": "git",
    "stash": "git",
    "cherry-pick": "git",
    "cherrypick": "git",
    # Linux
    "linux": "linux",
    "bash": "linux",
    "shell": "linux",
    "terminal": "linux",
    "unix": "linux",
    "macos": "linux",
    "ubuntu": "linux",
    "debian": "linux",
    "centos": "linux",
    "rhel": "linux",
    "fedora": "linux",
    "systemctl": "linux",
    "journalctl": "linux",
    "systemd": "linux",
    "cron": "linux",
    "crontab": "linux",
    "apt": "linux",
    "yum": "linux",
    "dnf": "linux",
    "pacman": "linux",
    "chmod": "linux",
    "chown": "linux",
    "grep": "linux",
    "sed": "linux",
    "awk": "linux",
    "find": "linux",
    "xargs": "linux",
    "curl": "linux",
    "wget": "linux",
    "ssh": "linux",
    "scp": "linux",
    "rsync": "linux",
    "tar": "linux",
    "gzip": "linux",
    "zip": "linux",
    "unzip": "linux",
    "lsof": "linux",
    "netstat": "linux",
    "ss": "linux",
    "ip": "linux",
    "ifconfig": "linux",
    "ping": "linux",
    "traceroute": "linux",
    "dig": "linux",
    "nslookup": "linux",
    "process": "linux",
    "port": "linux",
    "disk": "linux",
    "memory": "linux",
    "cpu": "linux",
    # Python
    "python": "python",
    "python3": "python",
    "pip": "python",
    "pip3": "python",
    "venv": "python",
    "virtualenv": "python",
    "conda": "python",
    "poetry": "python",
    "uv": "python",
    "pytest": "python",
    "ruff": "python",
    "mypy": "python",
    "black": "python",
    "isort": "python",
    "pylint": "python",
    "flake8": "python",
    "pyenv": "python",
    # Go
    "go": "go",
    "golang": "go",
    "gomod": "go",
    "gofmt": "go",
    "gotest": "go",
    "govet": "go",
    # Rust
    "rust": "rust",
    "cargo": "rust",
    "rustc": "rust",
    "rustup": "rust",
    "clippy": "rust",
    "crate": "rust",
    "crates": "rust",
    # Kafka
    "kafka": "kafka",
    "kafka-topics": "kafka",
    "kafka-console-consumer": "kafka",
    "kafka-console-producer": "kafka",
    "kafka-consumer-groups": "kafka",
    "consumer group": "kafka",
    "consumer lag": "kafka",
    "topic": "kafka",
    "broker": "kafka",
    "zookeeper": "kafka",
    # Terraform
    "terraform": "terraform",
    "tf": "terraform",
    "hcl": "terraform",
    "tfstate": "terraform",
    "tfplan": "terraform",
    "tfvars": "terraform",
    "terragrunt": "terraform",
}

# Common typo corrections
TYPO_CORRECTIONS: dict[str, str] = {
    "kubernets": "kubernetes",
    "kuberentes": "kubernetes",
    "kuberenetes": "kubernetes",
    "kuberntes": "kubernetes",
    "kubernestes": "kubernetes",
    "kubernetse": "kubernetes",
    "kuberneets": "kubernetes",
    "k8": "k8s",
    "dockr": "docker",
    "dokcer": "docker",
    "docekr": "docker",
    "dcoker": "docker",
    "pyhton": "python",
    "pyton": "python",
    "pytohn": "python",
    "pythno": "python",
    "pythn": "python",
    "ptyhon": "python",
    "kafak": "kafka",
    "kafkfa": "kafka",
    "kfaka": "kafka",
    "promtheus": "prometheus",
    "promethues": "prometheus",
    "promethus": "prometheus",
    "grafna": "grafana",
    "grafaan": "grafana",
    "grfana": "grafana",
    "terrafom": "terraform",
    "terrafrm": "terraform",
    "terrafrom": "terraform",
    "terrafomr": "terraform",
    "postgrs": "postgres",
    "psotgres": "postgres",
    "deplyment": "deployment",
    "deplyoment": "deployment",
    "depoyment": "deployment",
    "deploymnet": "deployment",
    "contaner": "container",
    "containr": "container",
    "contianer": "container",
    "contanier": "container",
    "comit": "commit",
    "commmit": "commit",
    "commti": "commit",
    "bracnh": "branch",
    "barnch": "branch",
    "branhc": "branch",
    "servce": "service",
    "serivce": "service",
    "srevice": "service",
    "namesapce": "namespace",
    "namepsace": "namespace",
    "namspace": "namespace",
}

# Synonym normalization (expand synonyms for better matching)
SYNONYMS: dict[str, list[str]] = {
    "remove": ["delete", "rm", "erase", "destroy", "drop"],
    "delete": ["remove", "rm", "erase", "destroy", "drop"],
    "restart": ["reboot", "recycle", "reload", "bounce"],
    "show": ["list", "display", "view", "print", "get"],
    "list": ["show", "display", "view", "get", "ls"],
    "inspect": ["describe", "examine", "detail", "info"],
    "describe": ["inspect", "examine", "detail", "info"],
    "logs": ["log", "output", "stdout", "stderr"],
    "memory": ["ram", "mem"],
    "cpu": ["processor", "cores"],
    "undo": ["revert", "rollback", "reverse", "reset"],
    "rollback": ["undo", "revert", "reverse"],
    "find": ["search", "locate", "look for", "where"],
    "search": ["find", "locate", "look for", "grep"],
    "stop": ["halt", "terminate", "kill", "end"],
    "kill": ["stop", "terminate", "end", "halt"],
    "create": ["make", "new", "init", "generate", "add"],
    "start": ["begin", "launch", "run", "boot"],
    "update": ["upgrade", "patch", "modify"],
    "copy": ["cp", "duplicate", "clone"],
    "move": ["mv", "rename", "transfer"],
    "connect": ["ssh", "login", "remote", "access"],
    "download": ["fetch", "pull", "get", "retrieve"],
    "upload": ["push", "send", "transfer"],
    "check": ["verify", "validate", "test", "inspect"],
}

# Secret patterns to redact
SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?:password|passwd|pwd)\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"(?:token|api[_-]?key|secret[_-]?key|access[_-]?key)\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"(?:Bearer|Basic)\s+[A-Za-z0-9+/=._-]{20,}", re.IGNORECASE),
    re.compile(r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----"),
    re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}"),  # AWS access keys
    re.compile(r"ghp_[A-Za-z0-9]{36}"),  # GitHub tokens
    re.compile(r"sk-[A-Za-z0-9]{32,}"),  # API keys
]


def normalize_query(query: str) -> str:
    """Normalize a user query for processing.

    Steps:
    1. Unicode normalization
    2. Lowercase
    3. Whitespace normalization
    4. Remove special characters (keep alphanumeric, hyphens, slashes, dots)
    5. Typo correction
    """
    # Unicode normalize
    query = unicodedata.normalize("NFKC", query)
    # Lowercase
    query = query.lower().strip()
    # Normalize whitespace
    query = re.sub(r"\s+", " ", query)
    # Remove question marks and trailing punctuation
    query = query.rstrip("?!.")
    # Apply typo corrections
    query = _correct_typos(query)
    return query.strip()


def _correct_typos(text: str) -> str:
    """Apply known typo corrections."""
    words = text.split()
    corrected = []
    for word in words:
        if word in TYPO_CORRECTIONS:
            corrected.append(TYPO_CORRECTIONS[word])
        else:
            corrected.append(word)
    return " ".join(corrected)


def detect_technology(query: str) -> str | None:
    """Detect the technology mentioned in a query.

    Returns the canonical technology name or None.
    """
    query_lower = query.lower()
    words = re.split(r"[\s/\-_]+", query_lower)

    # Direct word match
    for word in words:
        if word in TECHNOLOGY_ALIASES:
            return TECHNOLOGY_ALIASES[word]

    # Multi-word match
    for alias, tech in TECHNOLOGY_ALIASES.items():
        if " " in alias and alias in query_lower:
            return tech

    # Fuzzy match on technology names
    all_techs = list(set(TECHNOLOGY_ALIASES.values()))
    for word in words:
        if len(word) >= 4:
            result = process.extractOne(
                word,
                all_techs,
                scorer=fuzz.ratio,
                score_cutoff=80,
            )
            if result:
                return result[0]

    return None


def detect_all_technologies(query: str) -> list[str]:
    """Detect all technologies mentioned in a query."""
    query_lower = query.lower()
    words = re.split(r"[\s/\-_]+", query_lower)
    techs: set[str] = set()

    for word in words:
        if word in TECHNOLOGY_ALIASES:
            techs.add(TECHNOLOGY_ALIASES[word])

    for alias, tech in TECHNOLOGY_ALIASES.items():
        if " " in alias and alias in query_lower:
            techs.add(tech)

    return sorted(techs)


@lru_cache(maxsize=256)
def extract_keywords(query: str) -> list[str]:
    """Extract meaningful keywords from a query, removing stop words."""
    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "up", "about", "into", "through", "during", "before", "after",
        "above", "below", "between", "out", "off", "over", "under",
        "again", "further", "then", "once", "here", "there", "when",
        "where", "why", "how", "all", "each", "every", "both", "few",
        "more", "most", "other", "some", "such", "no", "nor", "not",
        "only", "own", "same", "so", "than", "too", "very", "just",
        "because", "as", "until", "while", "that", "this", "these",
        "those", "it", "its", "i", "me", "my", "we", "our", "you",
        "your", "he", "him", "his", "she", "her", "they", "them",
        "their", "what", "which", "who", "whom", "and", "but", "if",
        "or", "am", "want", "need", "like", "way", "using", "use",
    }
    words = re.split(r"[\s/\-_]+", query.lower())
    return [w for w in words if w and w not in stop_words and len(w) > 1]


def redact_secrets(text: str) -> str:
    """Redact potential secrets from text."""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def is_ambiguous(query: str) -> bool:
    """Detect if a query is too vague and needs clarification."""
    normalized = normalize_query(query)
    words = normalized.split()

    # Very short queries with pronouns
    if len(words) <= 3:
        pronouns = {"it", "this", "that", "them", "those", "these"}
        if any(w in pronouns for w in words):
            return True

    # Just a verb without context
    if len(words) == 1 and words[0] in {"restart", "delete", "remove", "stop", "start", "run"}:
        return True

    return False


def expand_query(query: str) -> str:
    """Expand a query with synonyms for better matching."""
    words = query.lower().split()
    expanded = list(words)

    for word in words:
        if word in SYNONYMS:
            # Add top 2 synonyms
            for syn in SYNONYMS[word][:2]:
                if syn not in expanded:
                    expanded.append(syn)

    return " ".join(expanded)


def compute_keyword_overlap(query_keywords: list[str], target_keywords: list[str]) -> float:
    """Compute keyword overlap score between query and target."""
    if not query_keywords or not target_keywords:
        return 0.0

    query_set = set(query_keywords)
    target_set = set(target_keywords)

    intersection = query_set & target_set
    if not intersection:
        return 0.0

    # Jaccard-like similarity
    union = query_set | target_set
    return len(intersection) / len(union)
