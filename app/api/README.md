
## POST   /api/v1/logs           # вставка записи или батча

Request body:
```
[
  {
    "application": "string",
    "event_time": "2026-10-01T17:29:14.255Z",
    "message": "string"
  }
]
```
## GET    /api/v1/logs           # выборка по application (+период, пагинация)

Request query params:
```
    "application": "string"
```
Response
```
{
  "items": [
    {
      "id": 0,
      "application": "string",
      "event_time": "2026-10-01T17:30:14.768Z",
      "message": "string"
    }
  ],
  "total": 0,
  "limit": 0,
  "offset": 0
}
```
## DELETE /api/v1/logs           # удаление по application за период
Request query params:
```
    "application": "string"
    "from": "string"
    "to": "string"
```

## DELETE /api/v1/logs/all       # очистить всё

## GET    /api/v1/counters       # счётчики (опц. application=)

Request query params:
```
    "application": "string"
```

## GET    /health

Response body
```
{
  "status": "fail",
  "db": "down"
}
```