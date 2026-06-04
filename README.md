# Credit Card Default Prediction ML Service

Production-like ML-сервис для прогнозирования дефолта по кредитным картам (UCI [Default of Credit Card Clients](https://archive.ics.uci.edu/ml/datasets/default+of+credit+card+clients)).
Докер образ - [ссылка](https://hub.docker.com/r/xifeni/credit-card-ml-service`).

## Модели

| Версия | Алгоритм | Файл | A/B группа |
|--------|----------|------|------------|
| `v1` | Logistic Regression | `models/logistic_regression_model.pkl` | A (контроль) |
| `v2` | Random Forest | `models/random_forest_model.pkl` | B (тест) |

Общий препроцессор: `models/preprocessor.pkl` - `ColumnTransformer`: OneHotEncoder для категориальных признаков (`SEX`, `EDUCATION`, `MARRIAGE`, `PAY_*`), StandardScaler для числовых.
Подробная архитектура: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)  
План A/B: [docs/ab_test_plan.md](docs/AB_TEST_PLAN.md)

## Старт локально

```bash
git clone https://github.com/xifeni/credit-card-ml-service.git
cd credit-card-ml-service
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
PYTHONPATH=. python app/api.py
```

Сервис: http://localhost:5000

## Docker

### Сборка и запуск одного контейнера

```bash
docker build -t credit-card-ml-service .
docker run --rm -p 5000:5000 credit-card-ml-service
curl http://localhost:5000/health
```

### Docker Compose (ML + NGINX)

```bash
docker compose up --build
```

| URL | Назначение |
|-----|------------|
| http://localhost:8080 | через NGINX (рекомендуется) |
| http://localhost:5000 | напрямую к Flask (только `ml-service`, если пробросить порт в compose) |

В Compose включён автосплит: `AB_TEST_ENABLED=true`, `AB_SPLIT_RATIO=0.5`.

### Docker Hub

```text
docker pull xifeni/credit-card-ml-service:latest
```

## API

### `GET /health`

```bash
curl http://localhost:5000/health
```

Ответ:

```json
{"status": "healthy"}
```

### `POST /predict`

Принимает JSON с признаками UCI (без `ID` и без целевой переменной).

Служебные поля (не идут в модель):

| Поле | Описание |
|------|----------|
| `model_version` | `v1` или `v2` (ручной выбор; иначе автосплит при `AB_TEST_ENABLED=true`) |
| `customer_id` | ID клиента для стабильного A/B-сплита |
| `request_id` | альтернатива для хеша |

Ответ:

| Поле | Тип | Описание |
|------|-----|----------|
| `prediction` | 0 / 1 | класс дефолта |
| `probability` | float | P(дефолт=1) |
| `model_version` | string | использованная модель |
| `ab_assigned` | bool | версию назначил автосплит |
| `ab_group` | `A` / `B` | A=v1, B=v2 |

#### Пример: v1 по умолчанию

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "LIMIT_BAL": 20000,
    "SEX": 2,
    "EDUCATION": 2,
    "MARRIAGE": 1,
    "AGE": 24,
    "PAY_0": 2,
    "PAY_2": 2,
    "PAY_3": -1,
    "PAY_4": -1,
    "PAY_5": -2,
    "PAY_6": -2,
    "BILL_AMT1": 3913,
    "BILL_AMT2": 3102,
    "BILL_AMT3": 689,
    "BILL_AMT4": 0,
    "BILL_AMT5": 0,
    "BILL_AMT6": 0,
    "PAY_AMT1": 0,
    "PAY_AMT2": 689,
    "PAY_AMT3": 0,
    "PAY_AMT4": 0,
    "PAY_AMT5": 0,
    "PAY_AMT6": 0
  }'
```

#### Пример: явно v2

Добавьте `"model_version": "v2"` в JSON.

#### Пример: A/B автосплит

```bash
AB_TEST_ENABLED=true AB_SPLIT_RATIO=0.5 PYTHONPATH=. python app/api.py
```
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "client-42", "LIMIT_BAL": 20000, "SEX": 2, ...}'
```

Полный скрипт примеров: [docs/demo/api_examples.sh](docs/demo/api_examples.sh)

### Ошибки

```json
{"error": "Empty request body"}
```

```json
{"error": "Invalid model_version: v3"}
```

## Логирование

Запросы логируются в stdout в формате JSON (см. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), образцы: [docs/demo/sample_logs.jsonl](docs/demo/sample_logs.jsonl)).

## A/B-тестирование

- Контроль (A): v1 - Logistic Regression  
- Тест (B): v2 - Random Forest  
- Сплит: 50/50 по `customer_id` (детерминированный хеш)  
- План и метрики: [docs/ab_test_plan.md](docs/AB_TEST_PLAN.md)

## Демонстрация для сдачи

1. Скриншот или вывод: `curl /health` и `curl /predict`.  
2. Логи JSON из контейнера: `docker compose logs ml-service`.  
3. Скрипт: `bash docs/demo/api_examples.sh` (нужен `jq`).  
4. Ссылка на GitHub и Docker Hub в README (замените плейсхолдеры).

## Воспроизводимость

- `requirements.txt` - зафиксированные зависимости  
- `python -m venv .venv`  
- `models/train_model.py` - переобучение  
- Docker / Compose - идентичное окружение  

Рекомендуемый Python: 3.10+ (в образе: 3.12).

