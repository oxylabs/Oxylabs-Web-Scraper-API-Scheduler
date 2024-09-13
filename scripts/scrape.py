import json
import logging
import time
from os.path import isdir
from queue import Queue

import requests

from scripts import utils


logger = logging.getLogger(__name__)


def _get_job_content(job_id: str, params: dict) -> dict:
    response = requests.request(
        method="GET",
        url=f"http://data.oxylabs.io/v1/queries/{job_id}/results",
        auth=(params["creds_username"], params["creds_password"]),
    )
    return response.json()


def _get_batch_results(jobs: Queue, params: dict) -> None:
    completed_jobs = 0
    total_number_of_jobs = jobs.qsize()
    while not jobs.empty():
        job_id = jobs.get()
        status_response = requests.request(
            "GET",
            url=f"http://data.oxylabs.io/v1/queries/{job_id}",
            auth=(params["creds_username"], params["creds_password"]),
        )
        if status_response.json()["status"] != "done":
            time.sleep(1)
            jobs.put(job_id)
            continue
        with open(f"{params['output_path']}/{job_id}.json", "w") as f:
            f.write(json.dumps(_get_job_content(job_id, params)))
        completed_jobs += 1
        print(f"Progress - `{completed_jobs}/{total_number_of_jobs}`")


def _generate_cron_expression(params: dict) -> str:
    frequency = params.get("frequency")
    hour = params.get("time")
    cron_expression = ""
    if frequency == "daily":
        cron_expression = f"0 {hour} * * *"
    elif frequency == "weekly":
        weekday = params.get("weekday")
        cron_expression = f"0 {hour} * * {weekday}"
    elif frequency == "monthly":
        month_day = params.get("month_day")
        cron_expression = f"0 {hour} {month_day} * *"
    return cron_expression


def once_store_local(params: dict) -> None:
    if not isdir(params["output_path"]):
        print(
            f"Path you provided to store results does not exist on your device. "
            f"`{params['output_path']}`.",
        )
        return
    urls = utils.read_urls(params["urls_path"])
    print(
        f"\033[1mWill scrape `{len(urls)}` URLs and store results locally - "
        f"`{params['output_path']}`.\033[0m"
    )
    payload = utils.read_payload(params["payload_path"])
    payload.update({"url": urls})
    response = requests.request(
        "POST",
        "https://data.oxylabs.io/v1/queries/batch",
        auth=(params["creds_username"], params["creds_password"]),
        json=payload,
    )
    if errors := utils.check_if_error(response.json()):
        print(f"Errors received while making request. `{errors}`")
        return
    jobs_queue = Queue()
    [
        jobs_queue.put(query_response["id"])
        for query_response in response.json()["queries"]
    ]
    _get_batch_results(jobs=jobs_queue, params=params)


def store_cloud(params: dict) -> None:
    urls = utils.read_urls(params["urls_path"])
    payload = utils.read_payload(params["payload_path"])
    storage_type = None
    if params["output_path"].startswith("s3://"):
        storage_type = "s3"
    elif params["output_path"].startswith("gs://"):
        storage_type = "gcs"
    if not storage_type:
        raise ValueError(
            f"Cloud storage URL is not from AWS S3 or Google Cloud Storage. "
            f"We support only these. Cloud path - `{params['output_path']}`.",
        )
    payload.update(
        {
            "storage_type": storage_type,
            "storage_url": params["output_path"],
        }
    )

    if params["schedule"]:
        print(
            f"\033[1mWill schedule to scrape `{len(urls)}` URLs {params['frequency']} "
            f"and store results in cloud - `{params['output_path']}`.\033[0m"
        )
        cron_expression = _generate_cron_expression(params)
        schedule_items = []
        for url in urls:
            payload.update({"url": url})
            schedule_items.append(payload)
        scheduled_payload = {
            "cron": cron_expression,
            "items": schedule_items,
            "end_time": params["end_datetime"],
        }
        scheduled_response = requests.request(
            "POST",
            "https://data.oxylabs.io/v1/schedules",
            auth=(params["creds_username"], params["creds_password"]),
            json=scheduled_payload,
        )
        if errors := utils.check_if_error(scheduled_response.json()):
            print(f"Errors received while making request. `{errors}`")
            return
        print(
            "\033[1mScraping jobs registered. "
            "Check your cloud storage for completed jobs.\033[0m"
        )
        print(
            "\033[1mBe aware that jobs will be repeated until specified end date or "
            "scheduler stopped manually, copying `schedule_id` could be useful.\033[0m"
        )
        print(scheduled_response.json())
        return

    print(
        f"\033[1mWill schedule to scrape `{len(urls)}` URLs and store results in "
        f"cloud - `{params['output_path']}`.\033[0m"
    )
    payload.update({"url": urls})
    response = requests.request(
        "POST",
        "https://data.oxylabs.io/v1/queries/batch",
        auth=(params["creds_username"], params["creds_password"]),
        json=payload,
    )
    if errors := utils.check_if_error(response.json()):
        print(f"Errors received while making request. `{errors}`")
        return
    print("Scraping jobs registered. Check your cloud storage for completed jobs.")
