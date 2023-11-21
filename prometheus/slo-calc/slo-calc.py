import logging
import signal
import sys
import time
from datetime import datetime

import requests
from environs import Env
from prometheus_client import Gauge, start_http_server

env = Env()
env.read_env()

PROMETHEUS_HOST = env("ONCALL_HOST", 'http://158.160.96.191:8080/')
EXPORTER_SCRAPE_INTERVAL = env.int("EXPORTER_SCRAPE_INTERVA", 60)
EXPORTER_METRICS_PORT = env.int("EXPORTER_METRICS_PORT", 9227)
EXPORTER_LOG_LEVEL = env.log_level("EXPORTER_LOG_LEVEL", logging.INFO)

prober_full_scenario_failed_sli = Gauge('sli_prober_full_scenario_failed',
                                        'The time when break slo. One when scenario from prober failed, zero when success')
prober_full_scenario_timeout_sli = Gauge('sli_prober_full_scenario_timeout',
                                         'The time when break slo. One when scenario takes more than 2 seconds')
current_duty_exits_sli = Gauge('sli_current_duty_exits',
                               'The time when break slo. One when no current duty in many teams')
next_duty_exits_sli = Gauge('sli_next_duty_exits', 'The time when break slo. One when no next duty in many teams')
current_sla = Gauge('sla_current', 'Total service sla calculated from indicators')
total_sla = Gauge('sla_total', 'Total service sla calculated from indicators and history')


def prometheus_request(query, time, default):
    try:
        response = requests.get(f'{PROMETHEUS_HOST}api/v1/query', params={'query': query, 'time': time})
        if not response.ok:
            return default
        content = response.json()
        if not content:
            return default
        if len(content['data']['result']) == 0:
            return default
        return content['data']['result'][0]['value'][1]
    except Exception as e:
        logging.error(e)
        return default


def calc_sli_prober(slo=0):
    value = prometheus_request('increase(prober_failed_requests_total{action="full_scenario"}[2m])', time.time(), 1)
    value = int(float(value))
    if value > slo:
        prober_full_scenario_failed_sli.set(1)
        return 0
    prober_full_scenario_failed_sli.set(0)
    return 1


def calc_sli_time_prober(slo=2):
    value = prometheus_request('prober_request_latency_seconds{action="full_scenario"}', time.time(), 10)
    value = float(value)
    if value > slo:
        prober_full_scenario_timeout_sli.set(1)
        return 0
    prober_full_scenario_timeout_sli.set(0)
    return 1


def calc_sli_next_duty(slo=0.9):
    value = prometheus_request('count(duty_next_roles_count{job!="prober test team"} > 0) / sum(total_teams_count)',
                               time.time(), 0)
    value = float(value)
    if value < slo:
        next_duty_exits_sli.set(1)
        return 0
    next_duty_exits_sli.set(0)
    return 1


def calc_sli_current_duty(slo=0.9):
    week_no = datetime.today().weekday()
    if week_no > 5:  # Если сегодня выходной дежурных может не быть
        next_duty_exits_sli.set(0)
        return 1
    value = prometheus_request('count(duty_current_roles_count{job!="prober test team"} > 0) / sum(total_teams_count)',
                               time.time(), 0)
    value = float(value)
    if value < slo:
        next_duty_exits_sli.set(1)
        return 0
    next_duty_exits_sli.set(0)
    return 1


def calculate_sla():
    prober_status = calc_sli_prober()
    prober_time_status = calc_sli_time_prober()
    current_duty_status = calc_sli_current_duty()
    next_duty_status = calc_sli_next_duty()
    cur_sla = (prober_status * 10 + prober_time_status * 3 + current_duty_status + next_duty_status * 2) / (
                10 + 3 + 1 + 2)
    current_sla.set(cur_sla)


def main():
    logging.basicConfig(stream=sys.stdout,
                        level=EXPORTER_LOG_LEVEL,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    start_http_server(EXPORTER_METRICS_PORT)
    while True:
        logging.debug("Send requests to API")
        try:
            calculate_sla()
        except Exception as e:
            logging.error(e)
        logging.debug(f"Waiting for next scrape: {EXPORTER_SCRAPE_INTERVAL}")
        time.sleep(EXPORTER_SCRAPE_INTERVAL)


def terminate():
    print('Terminating...')
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, terminate)
    main()
