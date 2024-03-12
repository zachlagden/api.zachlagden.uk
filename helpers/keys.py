# Import required modules

# Python standard library
from datetime import datetime
import secrets
import json

# Load the config
with open("config.json", "r") as f:
    CONFIG = json.load(f)

# Load the API keys
with open("api_keys.json", "r") as f:
    API_KEYS = json.load(f)

def generate_api_key(created_by: str = "System") -> str:
    api_keys = API_KEYS

    new_api_key = "ZLAPI-" + secrets.token_urlsafe(32)

    current_date = datetime.now().isoformat()

    api_keys.append(
        {
            "key": new_api_key,
            "created": current_date,
            "created_by": created_by,
        }
    )

    with open("api_keys.json", "w") as f:
        json.dump(api_keys, f, indent=4)

    return new_api_key


def check_api_key(api_key):
    with open("api_keys.json", "r") as f:
        api_keys = json.load(f)

    for key in api_keys:
        if key["key"] == api_key:
            return True
    return False

def check_master_key(api_key):
    return api_key == CONFIG["api"]["master_key"]