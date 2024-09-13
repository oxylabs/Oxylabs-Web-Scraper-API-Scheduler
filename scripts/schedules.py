import requests

from scripts import utils


def _get_schedules(params: dict) -> list:
    response = requests.request(
        "GET",
        "https://data.oxylabs.io/v1/schedules",
        auth=(params["creds_username"], params["creds_password"]),
    )
    if error := utils.check_if_error(response.json()):
        raise ConnectionRefusedError(f"Could not retrieve schedules. `{error}`.")

    return response.json()["schedules"]


def _deactivate_schedule(schedule_id: str, params: dict) -> None:
    requests.request(
        "GET",
        f"https://data.oxylabs.io/v1/schedules/{schedule_id}/state",
        auth=(params["creds_username"], params["creds_password"]),
        json={"active": False},
    )


def stop_scheduler(params: dict) -> None:
    schedules = _get_schedules(params)
    schedule_id = schedules[
        utils.get_user_choice("Select schedule you wish to stop.", schedules)
    ]
    _deactivate_schedule(schedule_id, params)
    print("Schedule deactivated.")
