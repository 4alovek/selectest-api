# Шаг 1: Запуск контейнеров
### Баг 1. Контейнер не стартует, исправил config.py, было пару опечаток

# Шаг 2: Исправление получения данных
### Баг 2. Поправил scheduler, т.к. вместо 5 минут вакансии парсятся раз в 5 секунд
### Появляется ошибка:
```
2026-03-12 13:22:47,837 | ERROR | app.main | Ошибка фонового парсинга: 'NoneType' object has no attribute 'name'
Traceback (most recent call last):
  File "/app/app/main.py", line 24, in _run_parse_job
    await parse_and_store(session)
  File "/app/app/services/parser.py", line 43, in parse_and_store
    "city_name": item.city.name.strip(),
                 ^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'name'
```
### Баг 3. Исправил парсер, т.к. не во всех вакансиях есть city
### Баг 4. Обновил версию python в Dockerfile, т.к. контейнер 3.11-slim имеет уязвимость

# Шаг 3: Исправление конфликтов external_id
### Баг 5. Исправил возвращаемое значение в тайпинге функции, т.к. линтер ругался
```get_session() -> AsyncGenerator[AsyncSession, None]:```
### POST/PUT теперь возвращают 409 при попытке использовать уже существующий external_id
### Баг 6. Добавил коды ошибок чтобы в swagger'e не было undocumented

# Шаг 4: Стабильность парсинга
### Баг 7. Изменил строку httpx.AsyncClient через async with, чтобы не было утечки соединений
### Баг 8. Исправил гонку при параллельном запуске парсинга: сделал атомарный upsert по external_id

# Скриншоты с работой api в swagger'е приложил в папке photos