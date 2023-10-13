import logging
import sys
import time

import requests
from environs import Env
from prometheus_client import Counter, Gauge, Summary
from prometheus_client import start_http_server
from requests.utils import requote_uri

requests_latency = Summary('request_latency_seconds', 'API answer request handle latency for duty exist', ['team'])

current_duty_gauge = Gauge('duty_current_roles_count', 'Count of current date roles duty', ['team'])
next_duty_gauge = Gauge('duty_next_roles_count', 'Count of next date roles duty', ['team'])
total_teams_count = Gauge('total_teams_count', 'Count of total teams list in system')

failed_counter = Counter('failed_requests_total', 'Count of failed requests')
total_counter = Counter('requests_total', 'Count of total requests to API')

env = Env()
env.read_env()


ONCALL_HOST = env("ONCALL_HOST", 'http://158.160.96.191:8080/')
EXPORTER_UPDATE_INTERVAL = env.int("EXPORTER_UPDATE_INTERVAL", 60)
EXPORTER_METRICS_PORT = env.int("EXPORTER_METRICS_PORT", 9337)
EXPORTER_LOG_LEVEL = env.log_level("EXPORTER_LOG_LEVEL", logging.INFO)


class FailureError(RuntimeError):
    pass


def get_teams_list():
    total_counter.inc()
    r = requests.get(f"{ONCALL_HOST}api/v0/teams/", timeout=10)
    if r.status_code != 200:
        raise FailureError('Cant get teams')
    data = r.json()
    if not isinstance(data, list):
        raise FailureError('No list of teams from API')
    return r.json()


def get_next(team):
    total_counter.inc()
    r = requests.get(f"{ONCALL_HOST}api/v0/teams/{requote_uri(team)}/summary", timeout=10)
    if r.status_code != 200:
        raise FailureError(f'Wrong status code {r.status_code}')
    data = r.json()
    if "current" not in data:
        raise FailureError('No current in data')
    if "next" not in data:
        raise FailureError('No next in data')
    return data


def get_metric():
    teams = []
    try:
        teams = get_teams_list()
        total_teams_count.set(len(teams))
    except Exception as e:
        logging.error("Error while get teams list")
        logging.error(e)
        failed_counter.inc()
    for team in teams:
        try:
            t = time.time()
            data = get_next(team)
            current_duty_gauge.labels(team=team).set(len(data['current']))
            next_duty_gauge.labels(team=team).set(len(data['next']))
            requests_latency.labels(team=team).observe(time.time() - t)
        except Exception as e:
            failed_counter.inc()
            logging.error("Error while get teams summary info")
            logging.error(e)


def main():
    logging.basicConfig(stream=sys.stdout,
                        level=EXPORTER_LOG_LEVEL,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    start_http_server(EXPORTER_METRICS_PORT)
    while True:
        logging.debug("Send requests to API")
        get_metric()
        logging.debug(f"Waiting for next scrape: {EXPORTER_UPDATE_INTERVAL}")
        time.sleep(EXPORTER_UPDATE_INTERVAL)


if __name__ == '__main__':
    main()



