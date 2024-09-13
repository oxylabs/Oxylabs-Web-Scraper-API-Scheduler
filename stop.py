import os
from pathlib import Path

from dotenv import load_dotenv, set_key

from scripts import schedules, utils


if __name__ == "__main__":
    load_dotenv()
    creds_username = os.environ.get("OXY_USERNAME") or utils.ask("Oxylabs Username:")
    creds_password = os.environ.get("OXY_PASSWORD") or utils.ask("Oxylabs Password:")
    env_file_path = Path(".env")
    env_file_path.touch()
    set_key(env_file_path, key_to_set="OXY_USERNAME", value_to_set=creds_username)
    set_key(env_file_path, key_to_set="OXY_PASSWORD", value_to_set=creds_password)
    params = {
        "creds_username": creds_username,
        "creds_password": creds_password,
    }
    schedules.stop_scheduler(params)
