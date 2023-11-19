import base64
import hashlib
import hmac
import json
import logging
import signal
import sys
import time
from datetime import datetime, timedelta

import requests
from environs import Env
from prometheus_client import Counter, Gauge
from prometheus_client import start_http_server
from requests.utils import requote_uri

requests_latency = Gauge('prober_request_latency_seconds', 'API answer request handle latency', ['action'])

total_counter = Counter('prober_requests_total', 'Total api requests', ['action'])
failed_counter = Counter('prober_failed_requests_total', 'Count of success api request', ['action'])
success_counter = Counter('prober_success_requests_total', 'Count of failed api requests', ['action'])

env = Env()
env.read_env()


ONCALL_HOST = env("ONCALL_HOST", 'http://localhost:8080/')
EXPORTER_UPDATE_INTERVAL = env.int("EXPORTER_UPDATE_INTERVAL", 60)
EXPORTER_METRICS_PORT = env.int("EXPORTER_METRICS_PORT", 9447)
EXPORTER_LOG_LEVEL = env.log_level("EXPORTER_LOG_LEVEL", logging.INFO)
APP_NAME = env("ONCALL_APP_NAME", 'test_app')
APP_KEY = env("ONCALL_APP_KEY", 'test_key')


class FailureError(RuntimeError):
    pass


def wrap_error(reraise_exception=True):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                total_counter.labels(func.__name__).inc()
                t = time.time()
                ans = func(*args, **kwargs)
                requests_latency.labels(func.__name__).set(time.time() - t)
                return ans
            except Exception as e:
                failed_counter.labels(func.__name__).inc()
                if reraise_exception:
                    raise e
        return wrapper
    return decorator


def get_hmac_header(method, path, body):
    window = int(time.time()) // 5
    text = f"{window} {method} /{path} {body}"
    hashed = hmac.new(APP_KEY.encode(), text.encode('utf-8'), hashlib.sha512)
    signature = base64.urlsafe_b64encode(hashed.digest()).decode('utf-8')
    return f"hmac {APP_NAME}:{signature}"


def make_api_post(url, data):
    body = json.dumps(data)
    auth = get_hmac_header('POST', url, body)
    res = requests.post(f'{ONCALL_HOST}{url}', json=data, headers={'AUTHORIZATION': auth})
    if not res.ok:
        logging.debug(res.text)
        raise FailureError(f'Error on request {url}: {res.status_code}')
    return res.text


def make_api_delete(url):
    auth = get_hmac_header('DELETE', url, '')
    return requests.delete(f'{ONCALL_HOST}{url}', headers={'AUTHORIZATION': auth})


@wrap_error()
def create_team(team_name, tz, email, slack):
    data = {
        "name": team_name,
        "scheduling_timezone": tz,
        "email": email,
        "slack_channel": slack,
        "admin": 'root'
    }
    return make_api_post('api/v0/teams', data)


@wrap_error(False)
def delete_user(user):
    return make_api_delete(f'api/v0/users/{requote_uri(user)}')


@wrap_error(False)
def delete_team(team):
    return make_api_delete(f'api/v0/teams/{requote_uri(team)}')


@wrap_error()
def get_teams_list():
    r = requests.get(f"{ONCALL_HOST}api/v0/teams/", timeout=10)
    if r.status_code != 200:
        raise FailureError('Cant get teams')
    data = r.json()
    if not isinstance(data, list):
        raise FailureError('No list of teams from API')
    return r.json()


@wrap_error()
def get_next(team):
    r = requests.get(f"{ONCALL_HOST}api/v0/teams/{requote_uri(team)}/summary", timeout=10)
    if r.status_code != 200:
        raise FailureError(f'Wrong status code {r.status_code}')
    data = r.json()
    if "current" not in data:
        raise FailureError('No current in data')
    if "next" not in data:
        raise FailureError('No next in data')
    return data


@wrap_error()
def create_user(name):
    data = {
        "name": name,
    }
    return make_api_post('api/v0/users', data)


@wrap_error()
def create_roster(team, name):
    return make_api_post(f'api/v0/teams/{team}/rosters', {"name": name})


@wrap_error()
def add_user_to_team_roster(team, user, roster_name):
    return make_api_post(f'api/v0/teams/{team}/rosters/{roster_name}/users', {"name": user})


@wrap_error()
def create_event(team, user, role, date):
    start = time.mktime(date.timetuple())
    end = start + 86400.0
    data = {
        "start": start,
        "end": end,
        "team": team,
        "user": user,
        "role": role,
    }
    return make_api_post('api/v0/events', data)


def get_metric():
    try:
        create_user('prober.test')
        success_counter.labels(create_user.__name__).inc()
        create_team('prober test team', 'Europe/Moscow', 'prbeer.test.team@probe.test', '#prober-test-team')
        success_counter.labels(create_team.__name__).inc()
        create_roster('prober test team', 'duty')
        success_counter.labels(create_roster.__name__).inc()
        add_user_to_team_roster('prober test team', 'prober.test', 'duty')
        success_counter.labels(add_user_to_team_roster.__name__).inc()
        create_event('prober test team', 'prober.test', 'primary', datetime.now() + timedelta(days=4))
        success_counter.labels(create_event.__name__).inc()
        teams = get_teams_list()
        if 'prober test team' not in teams:
            failed_counter.labels(get_teams_list.__name__).inc()
            raise FailureError('no test team in list')
        success_counter.labels(get_teams_list.__name__).inc()
        next_duty = get_next('prober test team')
        if 'primary' not in next_duty['next']:
            failed_counter.labels(get_next.__name__).inc()
            raise FailureError('No next duty found in summary')
        found_users = next_duty['next']['primary']
        if len(found_users) != 1:
            failed_counter.labels(get_next.__name__).inc()
            raise FailureError('Wrong array len')
        found_user = found_users[0]
        if found_user['role'] != 'primary' or found_user['user'] != 'prober.test':
            failed_counter.labels(get_next.__name__).inc()
            raise FailureError('Wrong user duty in team')
    finally:
        delete_user('prober.test')
        delete_team('prober test team')


def main():
    logging.basicConfig(stream=sys.stdout,
                        level=EXPORTER_LOG_LEVEL,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    start_http_server(EXPORTER_METRICS_PORT)
    while True:
        logging.debug("Send requests to API")
        start = time.time()
        total_counter.labels('full_scenario').inc()
        try:
            get_metric()
            success_counter.labels('full_scenario').inc()
        except Exception as e:
            logging.error(e)
            failed_counter.labels('full_scenario').inc()
        requests_latency.labels('full_scenario').set(time.time() - start)
        logging.debug(f"Waiting for next scrape: {EXPORTER_UPDATE_INTERVAL}")
        time.sleep(EXPORTER_UPDATE_INTERVAL)


def terminate():
    print('Terminating...')
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, terminate)
    main()



