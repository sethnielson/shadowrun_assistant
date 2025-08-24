import os
import json
from django.conf import settings

CONFIG_ROOT = os.path.join(settings.BASE_DIR, "charcreator", "configs")

def load_config(ruleset: str, section: str) -> dict:
    """
    Loads a single config section for a given ruleset.
    e.g. load_config("sr3", "attributes")
    """
    path = os.path.join(CONFIG_ROOT, ruleset, f"{section}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_sections(ruleset: str) -> list:
    """
    Returns a list of available config sections (json filenames without .json).
    """
    ruleset_path = os.path.join(CONFIG_ROOT, ruleset)
    return [
        f[:-5] for f in os.listdir(ruleset_path)
        if f.endswith(".json")
    ]

def load_all_configs(ruleset: str) -> dict:
    """
    Loads all configs in the ruleset folder and returns them as a dict.
    e.g. {"attributes": {...}, "skills": {...}, ...}
    """
    configs = {}
    for section in list_sections(ruleset):
        configs[section] = load_config(ruleset, section)
    return configs

