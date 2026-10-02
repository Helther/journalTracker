## FastAPI сервис для хранения записей из journalctl и отслеживания их количества в БД
Стек:
 * Python3
 * FastAPI
 * Postgresql

## API
Описан в [readme](app/api/README.md)

Либо запустив сервис можно зайти на \<host>:\<port>/docs и проверить весб API

Схема БД задана в [schema.py](app/db/schema.py)
## Установка, деплой
Использовать docker-compose(из корневой папки):
```
docker-compose up
```

Либо вручную:
 - Поднять сервер Postgresql-16 с заданными параметрами подключения
 - запустить [bootstrap](utils/bootstrap.py)
 ```
 python -m utils.bootstrap
 ```
 - запустить сервис
 ```
uvicorn app.main:api --host 0.0.0.0 --port 8000
 ```

 ## Использование
 В качестве "клиента" приложены скрипты в папке utils
 
 Примеры использования:
 - Добавить записи в сервис (3 штуки)
 ```
 utils/journalctl_tail.sh 3 | utils/log_inserter.sh localhost 8000
 ```
 - Получить записи для приложения из сервиса (systemd)
 ```
 utils/fetch_logs.sh localhost 8000 systemd
 ```
 - Удалить записи для приложения
 ```
 utils/delete_logs.sh localhost 8000 systemd "2026-10-01T18:00:35Z" "2026-10-01T18:00:35Z"
 ```
