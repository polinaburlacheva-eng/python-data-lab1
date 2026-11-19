# Проект обработки и анализа данных Steam Games (Лабораторная работа №1)

Данный проект представляет собой сквозной пайплайн очистки, трансформации и загрузки (ETL) набора данных об играх Steam (`Steam Games Dataset`) в реляционные СУБД (SQLite и PostgreSQL) с проведением бенчмарков производительности форматов хранения и СУБД.


## Системные требования

* Язык программирования: Python 3.12.14
* СУБД: 
  * SQLite (встроена в Python)
  * PostgreSQL `^15.0` (через Docker-контейнер)
* Основные библиотеки Python:
  * `pandas` — первичная обработка и профилирование данных
  * `polars` — высокопроизводительная оптимизированная обработка (Eager & Lazy modes)
  * `pyarrow` — работа с колончатыми форматами Parquet и Feather
  * `sqlalchemy`, `psycopg2-binary` — взаимодействие с СУБД
  * `python-dotenv` — управление конфигурацией среды


## Установка и развёртывание окружения

1. Клонируйте репозиторий и перейдите в папку проекта:
   ```bash
   git clone <https://github.com/polinaburlacheva-eng>
   cd Python_Data_lab1


Создайте и активируйте виртуальное окружение:
python -m venv venv
# Для Windows:
venv\Scripts\activate
# Для Linux/macOS:
source venv/bin/activate

Установите зависимости:
pip install -r requirements.txt

Настройте файл переменных окружения на основе шаблона:
cp .env.example .env

ПОРЯДОК ЗАПУСКА
Запустите основной пайплайн очистки и подготовки данных:
python src/data_cleaning.py

Запустите скрипты загрузки данных и бенчмаркинга для баз данных:
python src/load_sqlite.py
python src/load_postgres.py

## Структура проекта

Python_Data_lab1/
├── data/
│   ├── raw/         # Исходный неподготовленный набор данных (steam.csv)
│   ├── interim/     # Промежуточные форматы для профилирования (pickle, feather, parquet)
│   └── processed/   # Финальные очищенные данные (cleaned_steam.parquet)
├── sql/
│   ├── schema_sqlite.sql    # DDL-схема и индексы для SQLite
│   └── schema_postgres.sql  # DDL-схема и индексы для PostgreSQL
├── src/
│   ├── data_cleaning.py     # Модуль очистки данных и логирования потерь
│   ├── load_sqlite.py       # Пайплайн загрузки и бенчмаркинга SQLite
│   └── load_postgres.py     # Пайплайн загрузки и бенчмаркинга PostgreSQL
├── .env.example             # Шаблон переменных окружения
├── main.py                  # Главный скрипт автоматического запуска сквозного пайплайна
└── README.md                # Документация проекта