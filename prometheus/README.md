# Система мониторинга

Мониторинг через prometheus.
Настройки в `prometheus.yml`.
Запуск через `docker-compose up -d`

## Скрипт подсчёта строк в логах

Подсчитывает количество строк в access.log, благодоря чему можно отслеживать число запросов обработых сервером.
Можно увидеть как кто-то заходит на наш непопулярный сервис из вне. Можно увидеть как часто сканится наш порт сканерами.


### Запуск
- В файле `generate_metrics.sh` заменить пути до файла с логами `LOG_FILE_PATH` поменяв путь до проекта
- Там же заменить путь до папки куда будут собираться логи `TEXTFILE_COLLECTOR_DIR`
- Добавить скрпит в cron: `crontab -e`, добавить туда строчку : `*/2 * * * * <путь до проекта>/prometheus/generate_metric.sh`
