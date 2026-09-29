```
POST   /api/v1/logs           # вставка записи или батча
GET    /api/v1/logs           # выборка по application (+период, пагинация)
DELETE /api/v1/logs           # удаление по application за период
DELETE /api/v1/logs/all       # очистить всё
GET    /api/v1/counters       # счётчики (опц. application=)
GET    /health
```