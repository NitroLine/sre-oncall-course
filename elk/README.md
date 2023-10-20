# ELK docker

Based on https://github.com/deviantony/docker-elk


### Startup

0. If you want you can change passwords in `.env`
1. Run setup `sudo docker compose up setup`
2. Run system ELK `sudo docker compose up -d`
3. Run filebeat `sudo docker compose -f docker-compose.yml -f extensions/filebeat/filebeat-compose.yml up -d`
4. To other container which not need to collect logs set in docker compose file:
```
    labels:
      co.elastic.logs/enabled: "false"
```
