"""
AutoCloser — Settings Manager
Loads, saves, and provides access to runtime-tunable settings in data/settings.json.
Falls back to sensible defaults if the file is missing or corrupted.
"""

import os
import json

SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "settings.json"
)

# ── Defaults ─────────────────────────────────────────────────
DEFAULTS = {
    "sender_name": "Alex",
    "company_name": "Autocloser",
    "calendly_link": "https://calendly.com/yourname/15min",
    "cycle_interval_minutes": 15,
    "pipeline_mode": "ai",
    "email_tone": "conversational",
    "auto_confirm_meetings": False,
    "auto_create_invoices": False,
    "default_service_id": "2",
    "max_email_words": 100,
    "notifications_enabled": True,
}

# In-memory cache (loaded once, refreshed on explicit load)
_cache = None


def load_settings() -> dict:
    """Load settings.json, merging with defaults for any missing keys."""
    global _cache

    settings = dict(DEFAULTS)

    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                user_settings = json.load(f)
            settings.update(user_settings)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[SETTINGS] Warning: Could not read {SETTINGS_PATH}: {e}")
            print("[SETTINGS] Using defaults.")

    _cache = settings
    return settings


def save_settings(settings: dict) -> None:
    """Write settings dict back to settings.json."""
    global _cache

    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)

    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

    _cache = settings
    print(f"[SETTINGS] Saved to {SETTINGS_PATH}")


def get(key: str, default=None):
    """Get a single setting value. Loads from file if not cached."""
    global _cache

    if _cache is None:
        load_settings()

    return _cache.get(key, default if default is not None else DEFAULTS.get(key))


def update(key: str, value) -> bool:
    """
    Update a single setting and save to disk.

    Returns True if the key is valid, False if the key is unknown.
    """
    global _cache

    if _cache is None:
        load_settings()

    if key not in DEFAULTS:
        print(f"[SETTINGS] Unknown setting: '{key}'")
        print(f"[SETTINGS] Valid settings: {', '.join(sorted(DEFAULTS.keys()))}")
        return False

    # Type coercion based on the default's type
    expected_type = type(DEFAULTS[key])
    try:
        if expected_type == bool:
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes", "on")
            else:
                value = bool(value)
        elif expected_type == int:
            value = int(value)
        elif expected_type == str:
            value = str(value)
    except (ValueError, TypeError) as e:
        print(f"[SETTINGS] Invalid value for '{key}': {e}")
        return False

    old_value = _cache.get(key)
    _cache[key] = value
    save_settings(_cache)

    print(f"[SETTINGS] Updated '{key}': {repr(old_value)} → {repr(value)}")
    return True


def reset() -> dict:
    """Reset all settings to defaults and save."""
    save_settings(dict(DEFAULTS))
    print("[SETTINGS] All settings reset to defaults.")
    return dict(DEFAULTS)


def display() -> str:
    """Return a formatted string of all current settings for display."""
    global _cache

    if _cache is None:
        load_settings()

    lines = []
    lines.append("═" * 55)
    lines.append("  ⚙️  AutoCloser Settings")
    lines.append("═" * 55)

    for key in sorted(_cache.keys()):
        value = _cache[key]
        default = DEFAULTS.get(key)
        marker = " " if value == default else "✏️"
        lines.append(f"  {marker} {key:30s} = {repr(value)}")

    lines.append("═" * 55)
    lines.append("  (✏️ = modified from default)")
    lines.append("")

    return "\n".join(lines)


# Quick self-test
if __name__ == "__main__":
    settings = load_settings()
    print(display())
    print(f"sender_name = {get('sender_name')}")
    print(f"cycle_interval_minutes = {get('cycle_interval_minutes')}")
