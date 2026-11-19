# Changelog

## [0.1.0] — 2026-11-19

### Breaking

- Минимальная поддерживаемая версия Python — 3.10 (ранее 3.8).
- Минимальная версия `aio_pika` — 9.6.0 (ранее 6.8.0).
- `BaseAdapter` больше не создаёт event loop в `__init__`: loop резолвится лениво
  из current running loop. Если loop не передан явно, обращение к
  `adapter.loop` вне корутины вызывает `RuntimeError`.
- Из тестовых extras удалены `asynctest` и `envparse` (не использовались,
  `asynctest` несовместим с Python 3.14).

### Fixed

- Совместимость с Python 3.14: `asyncio.get_event_loop()` больше не используется
  в CLI и адаптерах. `python -m mq_misc.publish` и `python -m mq_misc.consume`
  работают на Python 3.14.
- `start_server` создаёт и устанавливает новый event loop, если loop не передан.
- CLI publish больше не скрывает ошибки: исключение логируется и пробрасывается,
  процесс завершается с ненулевым кодом.
- CLI consume корректно завершается по Ctrl+C (раньше `run_forever()` запускался
  повторно) и не зависает при ошибке подключения.

### Changed

- CLI publish переведён на `asyncio.run`.
- CLI consume переведён на `asyncio.run`; добавлен внутренний `_run` с
  необязательным `stop_event` и гарантированным закрытием consumer.
- `create_connection` передаёт текущий running loop в `aio_pika.connect`.
- Интеграционные тесты читают адрес брокера из `MQ_MISC_TEST_AMQP_URL`
  (по умолчанию `amqp://guest:guest@localhost:5672/`).
- `pytest.ini`: задан `asyncio_default_fixture_loop_scope=function`.

### Added

- Тесты CLI-точек входа: `asyncio.run`, проброс ошибок, закрытие consumer,
  обработка Ctrl+C.
- Тесты event loop: создание адаптера вне корутины, ленивый резолв loop,
  передача loop в aio_pika, `start_server`.
- CI-матрица Python 3.10–3.14 с RabbitMQ и отдельная проверка на aio-pika 9.6.2.

### Docs

- README актуализирован: требования, установка, API, SSL, переменные окружения,
  актуальный вывод `--help`.
- Исправлены примеры CLI: несуществующий `-u` заменён на `-url`/`--amqp-url`.
- Описаны ранее не документированные `ssl_options`, `ssl_context`,
  `decode_message`, `log_message_body`.
