import os
from pathlib import Path

from dotenv import load_dotenv, set_key

from scripts import scrape, utils

STORAGE = ["local", "cloud"]
SCHEDULER_OPTIONS = ["daily", "weekly", "monthly"]
DEFAULT_URLS_PATH = "runtime_files/urls.txt"
DEFAULT_PAYLOAD_PATH = "runtime_files/payload.json"


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
        "urls_path": utils.ask(
            "Enter path to file containing URLs. "
            "Leave empty if you wish to use default from `runtime_files/urls.txt`.",
        )
        or DEFAULT_URLS_PATH,
        "payload_path": utils.ask(
            "Enter path to file containing request payload. "
            "Leave empty if you wish to use default from `runtime_files/payload.json`.",
        )
        or DEFAULT_PAYLOAD_PATH,
        "storage": STORAGE[
            utils.get_user_choice(
                "Select where you wish to store the results.",
                ["Locally", "Cloud"],
            )
        ],
    }
    if params["storage"] == "local":
        params.update(
            {
                "output_path": utils.ask(
                    "Full path to existing directory where results should be stored:",
                )
            }
        )
    else:
        params.update(
            {
                "output_path": utils.ask(
                    "Path to cloud bucket and directory/partition "
                    "where results should be stored:"
                )
            }
        )
    if params["storage"] == "cloud":
        params.update(
            {
                "schedule": utils.ask(
                    "Do you want to schedule urls to be scraped repetitively?(y/n)",
                ).lower()
                in ("yes", "y")
            }
        )
        if params["schedule"]:
            params.update(
                {
                    "frequency": SCHEDULER_OPTIONS[
                        utils.get_user_choice(
                            "Select frequency.",
                            ["Daily", "Weekly", "Monthly"],
                        )
                    ]
                }
            )
            params.update(
                {
                    "time": utils.ask(
                        "Specify hour of the day you wish to run scraping (e.g. 12):",
                    ),
                }
            )
            if params["frequency"] == "weekly":
                params.update(
                    {
                        "weekday": utils.get_user_choice(
                            "Select on which day it should run.",
                            [
                                "Monday",
                                "Tuesday",
                                "Wednesday",
                                "Thursday",
                                "Friday",
                                "Saturday",
                                "Sunday",
                            ],
                        )
                    }
                )
            elif params["frequency"] == "monthly":
                params.update(
                    {
                        "month_day": int(
                            utils.ask(
                                "Specify day of the month requests should be run:"
                            )
                        )
                    }
                )
            params.update(
                {
                    "end_datetime": utils.ask(
                        "Specify date and time when scheduler should "
                        "stop (e.g `2032-12-21 12:34:45`).\nIf you think you will stop "
                        "it manually, still enter some date far in the future."
                    )
                }
            )

    print("\n\033[1mParameters collected. Initiating jobs.\033[0m")
    if params["storage"] == "local":
        scrape.once_store_local(params)
    elif params["storage"] == "cloud":
        scrape.store_cloud(params)
