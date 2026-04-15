import os
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "brand_voice.yaml"


def load_brand_voice() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def update_brand_voice(updates: dict) -> None:
    config = load_brand_voice()
    config.update(updates)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


if __name__ == "__main__":
    import json
    config = load_brand_voice()
    print(json.dumps(config, indent=2))