

- Языки/фреймворки:
    
    - **Python** (~68.5%)
        
    - **Vue** (~18.0%)
        
    - **JavaScript** (~12.4%)
### Дерево репозитория

```
├── app.js
├── data.csv
├── Dockerfile
├── finily_csv.py
├── graph_indices.txt
├── G_set.txt
├── input
├── main.py
├── new_script.py
├── package.json
├── package-lock.json
├── post_processed_results
├── p_quntun.py
├── prep_csv.py
├── __pycache__
│   ├── main.cpython-313.pyc
│   ├── quantum_inspired.cpython-313.pyc
│   ├── start_all.cpython-313.pyc
│   ├── visualization_graph.cpython-313.pyc
│   ├── visualizition_graph_quant.cpython-313.pyc
│   └── visual_qi.cpython-313.pyc
├── quant.py
├── requirements.txt
├── result_quant
│   └── input
├── result_quant.zip
├── results
│   └── processed_files.json
├── routes.txt
├── server
│   └── data.csv
├── start_all.py
├── submission.csv
├── submission_inspired.csv
├── total_time.csv
├── total_time_inspired.csv
├── uploads
│   └── data.csv
├── visualised_qf
│   ├── ...
├── visualised_qi
│   ├── ...
├── visualization_graph.py
└── visualizition_graph_quant.py
```

- `app.js` — Node.js-скрипт (вероятно минимальный HTTP-сервер/роутер для демо/загрузок/просмотра результатов). 
- `data.csv` — Базовый входной датасет для локальных запусков/тестов.
- `Dockerfile` — Инструкция сборки Docker-образа проекта (база, установка зависимостей, команда запуска). 
- `finily_csv.py` — Финальная постобработка результатов в формат CSV (агрегация/слияние/закрывающие вычисления). 
- `graph_indices.txt` — Список индексов/ID графов, используемых в расчётах/визуализации.     
- `G_set.txt` — Набор параметров/подмножество «G» для задач над графом (например, вершины/рёбра/ограничения). 
- `input/` — Каталог входных данных для пайплайна (сырьё для скриптов подготовки/расчёта). 
- `main.py` — Главная точка входа Python-части; оркестрация шагов (подготовка → расчёты → экспорт/визуализация). 
- `new_script.py` — Вспомогательный/экспериментальный скрипт (пробные преобразования/отладка). 
- `package.json` — Манифест Node.js: зависимости и npm-скрипты (например, запуск `app.js`).
- `package-lock.json` — Лок-файл npm с зафиксированными версиями JS-зависимостей.
- `post_processed_results/` — Каталог артефактов после постобработки (финальные CSV/лог-файлы и пр.). 
- `p_quntun.py` — Реализация «quantum/quantum-inspired» варианта алгоритма
- `prep_csv.py` — Подготовка исходных CSV (очистка/нормализация/слияние) перед запуском основного расчёта.
- `quant.py` — Основные утилиты/алгоритмы проекта «quant» (ядро вычислений/модели). 
- `requirements.txt` — Список Python-зависимостей для воспроизводимой установки.
- `result_quant/input/` — Входные/промежуточные данные для серии экспериментов «result_quant». 
- `result_quant.zip` — Архив с результатами/артефактами запуска «result_quant».
- `results/processed_files.json` — Журнал/метаданные обработанных файлов (статусы, время, пути). 
- `routes.txt` — Описание маршрутов/путей для графовых задач (или список тестовых кейсов). 
- `server/data.csv` — Датасет для серверной части/демо-сервера (используется `app.js` или иным сервисом). 
- `start_all.py` — Оркестратор полного конвейера: последовательный запуск скриптов подготовки/расчёта/визуализации/экспорта.
- `submission.csv` — Итоговый CSV-файл для сабмита (например, соревнование/Kaggle).
- `submission_inspired.csv` — Вариант сабмита для «inspired» конфигурации/алгоритма. 
- `total_time.csv` — Сводка времени выполнения этапов/экспериментов (профилирование).
- `total_time_inspired.csv` — Аналогичная сводка времени для «inspired» варианта.
- `uploads/data.csv` — Загруженные пользователем данные (через веб/интерфейс). 
- `visualised_qf/` — Каталог PNG-визуализаций графов для варианта «qf» (файлы изображений опущены).
- `visualization_graph.py` — Скрипт построения графов и экспорта визуализаций (чтение данных → построение → сохранение PNG). 
- `visualizition_graph_quant.py` — Визуализация графов для «quant» варианта (орфография файла сохранена). 

## Быстрый старт

```bash
# 1) Зависимости
# Вариант A: Docker/Compose (рекомендуется)
docker compose up -d     # Требуется Docker Engine + Compose; сервисы и порты — см. docker-compose.yml (TODO)

# Вариант B: локально (пример, уточните под проект)
# Backend (Python)
cd back
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt                    # если есть; иначе заполнить pyproject.toml (TODO)
# пример запуска (уточните точный модуль/фреймворк):
# uvicorn app.main:app --reload  # TODO: скорректировать

# Frontend (Vue)
cd ../front
npm ci       # или: pnpm i / yarn install (TODO)
npm run dev  # или: npm run serve / pnpm dev / yarn dev (TODO)
```
## Деплой и эксплуатация

### Образы и сборка

```bash
# Бэкенд: сборка локального образа
docker build -f back/Dockerfile -t quant-back:local back

# Фронтенд: пример (если есть Dockerfile во front/)
docker build -f front/Dockerfile -t quant-front:local front  # TODO: подтвердить наличие
```

### Docker Compose

```bash
# Запуск всех сервисов (точные сервисы/порты — см. docker-compose.yml)
docker compose up --build

# Вход в контейнер
docker-compose up

# Удаление контейнеров
docker-compose down

# В случае ошибки прав доступа при работе на linux - перед docker или docker-compose пропишите sudo.

# Просмотр логов
docker compose logs -f --tail=200
```

## FAQ / Траблшутинг

- **Сервис не стартует в Docker**  
    Проверьте версии Docker/Compose и свободны ли порты из `docker-compose.yml`
    
- **Фронтенд не видит API**  
    Проверьте `API_BASE_URL` в env/конфиге фронтенда.
    
- **Импорт библиотек падает**  
    Установите зависимости (`pip install -r back/requirements.txt` или `npm ci` в `front/`) — **TODO** подтвердить точные файлы.
    
