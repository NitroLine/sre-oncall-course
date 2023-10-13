
# Custom metrics exporter for LinkedIn oncall

Homework №4 (9.1) for Tinkoff SRE course

Exporter in prometheus format

Metrics available:
- `request_latency_seconds`
- `duty_current_roles_count`
- `duty_next_roles_count`
- `total_teams_count`
- `failed_requests_total`
- `requests_total`


## How to run
Two ways:
### On machine
1. Install requirements `pip install -r requirements.txt`
2. Set `ONCALL_HOST` environment variable
   - Set more environment if you want
   - `EXPORTER_UPDATE_INTERVAL`, `EXPORTER_METRICS_PORT`, `EXPORTER_LOG_LEVEL`
3. Run service
   - Just script: `python custom_oncall_exporter.py`
   - Or setup as service using `oncallexporter.service`


### Using docker
(docker container for one script 😋)
1. Install docker
2. Change environment variables in `docker-compose.yml`
3. Run `docker-compose up -d`
