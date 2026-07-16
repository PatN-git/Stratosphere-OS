"""Config + secret hygiene for jules-dispatch.

Key is read from env var JULES_API_KEY (falling back to .env.local) and sent as the
X-Goog-Api-Key header by jules_api. The key value is never logged.
"""
import os
from pathlib import Path

from jules_api import JulesError

ENV_VAR = "JULES_API_KEY"


def _parse_dotenv(path):
    vals = {}
    if not path.exists():
        return vals
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        if k.startswith("export "):
            k = k[len("export "):].strip()
        vals[k] = v.strip().strip('"').strip("'")
    return vals


def load_api_key(project_root=".", env=None):
    """Return the Jules key from env or .env.local. Fail closed (JulesError) if absent."""
    env = os.environ if env is None else env
    key = env.get(ENV_VAR)
    if not key:
        key = _parse_dotenv(Path(project_root) / ".env.local").get(ENV_VAR)
    if not key:
        raise JulesError(0, f"{ENV_VAR} not configured in .env.local")
    return key


def safe_log(msg, secret):
    """Scrub the key literal out of anything before it is printed/written."""
    if secret and isinstance(msg, str):
        return msg.replace(secret, "***REDACTED***")
    return msg
