import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def read_urls(urls_path: str) -> Optional[list]:
    try:
        with open(urls_path) as f:
            return f.read().splitlines()
    except FileNotFoundError:
        msg = (
            f"File in URLs path does not exist or is corrupted. "
            f"Path - `{urls_path}`."
        )
        raise FileNotFoundError(msg)


def read_payload(payload_path: str) -> dict:
    try:
        with open(payload_path) as f:
            return json.loads(f.read())
    except FileNotFoundError as exc:
        msg = (
            f"File in payload path does not exist or is corrupted. "
            f"Path - `{payload_path}`."
        )
        raise FileNotFoundError(msg)


def check_if_error(response: dict) -> Optional[list]:
    if errors := response.get("errors"):
        return errors
    if error_message := response.get("message"):
        return [{"message": error_message}]


def ask(text: str) -> str:
    print(f"\033[1m{text}\033[0m")
    return input().strip()


def get_user_choice(prompt: str, options: list) -> int:
    print(f"\033[1m{prompt}\033[0m")

    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    choice = ask("Enter your choice:")
    while True:
        if choice.isdigit() and int(choice) in range(1, len(options) + 1):
            break
        print(
            "\033[0mInvalid choice. You must enter the number of your wanted option. "
            "Please try again.\033[0m"
        )
        choice = ask("Enter your choice:")
    return int(choice) - 1
