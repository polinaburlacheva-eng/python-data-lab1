
import io
import time
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
import psycopg2

print("ЗАГРУЗКА В POSTGRESQL")

BASE_DIR = Path(__file__).resolve().parent.parent
parquet_path = BASE_DIR / "data" / "processed" / "clean.parquet"

if not parquet_path.exists():
    raise FileNotFoundError(f"Файл не найден: {parquet_path}")

df = pd.read_parquet(parquet_path)
print(f"Загружено строк из Parquet: {len(df)}")

if "appid" in df.columns:
    df = df.dropna(subset=["appid"])
    df = df[df["appid"].astype(str).str.lower() != "nan"]
    df = df[df["appid"].astype(str).str.strip() != ""]
    df = df.drop_duplicates(subset=["appid"])
    df["appid"] = df["appid"].astype(str).str.slice(0, 255)

for col in df.columns:
    if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
        df[col] = df[col].apply(
            lambda x: str(x) if isinstance(x, (list, dict)) else x
        )

int_columns = [
    "peak_ccu",
    "positive",
    "negative",
    "achievements",
    "recommendations",
    "discountdlc_count"
]

float_columns = [
    "required_age",
    "price",
    "metacritic_score",
    "user_score",
    "score_rank",
    "average_playtime_forever",
    "average_playtime_two_weeks",
    "median_playtime_forever",
    "median_playtime_two_weeks"
]

for col in int_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        ).fillna(0).astype("int64")

for col in float_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

if "publishers" in df.columns:
    df["publisher_name"] = df["publishers"].apply(
        lambda x: str(x).split(",")[0].strip()
        if pd.notna(x) and str(x).strip()
        else None
    )
    df.loc[
        df["publisher_name"].str.lower() == "nan",
        "publisher_name"
    ] = None
    publishers_df = pd.DataFrame({
        "publisher_name": df["publisher_name"].dropna().unique()
    })
else:
    df["publisher_name"] = None
    publishers_df = pd.DataFrame(columns=["publisher_name"])

if "genres" in df.columns:
    df["genre_name"] = df["genres"].apply(
        lambda x: str(x).split(",")[0].strip()
        if pd.notna(x) and str(x).strip()
        else None
    )
    df.loc[
        df["genre_name"].str.lower() == "nan",
        "genre_name"
    ] = None
    genres_df = pd.DataFrame({
        "genre_name": df["genre_name"].dropna().unique()
    })
else:
    df["genre_name"] = None
    genres_df = pd.DataFrame(columns=["genre_name"])

if "genres" in df.columns:
    df["genres"] = df["genres"].fillna("Unknown").astype(str)
    genres_df = pd.DataFrame({
        "genre_name": df["genres"].unique()
    })

print("\nОчистка таблиц в PostgreSQL перед загрузкой...")

try:
    conn_clean = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="secret"
    )
    conn_clean.autocommit = True
    cur_clean = conn_clean.cursor()
    cur_clean.execute(
        "TRUNCATE TABLE games_pg, publishers, genres RESTART IDENTITY CASCADE;"
    )
    cur_clean.close()
    conn_clean.close()
except Exception as e:
    print(f"Информация: таблицы еще не созданы или пусты ({e})")

db_url = "postgresql+psycopg2://postgres:secret@127.0.0.1:5432/postgres"
engine = create_engine(db_url)

print("Загрузка справочников publishers и genres...")

try:
    publishers_df.to_sql(
        "publishers",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=1000
    )

    genres_df.to_sql(
        "genres",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=1000
    )
except Exception as e:
    print(f"\n[ОШИБКА] Не удалось записать справочники: {e}")
    raise e

pub_mapping = pd.read_sql(
    "SELECT publisher_id, publisher_name FROM publishers",
    con=engine
)

genre_mapping = pd.read_sql(
    "SELECT genre_id, genre_name FROM genres",
    con=engine
)

df = df.merge(
    pub_mapping,
    on="publisher_name",
    how="left"
)

df = df.merge(
    genre_mapping,
    on="genre_name",
    how="left"
)

for col in ["publisher_id", "genre_id"]:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        ).astype("Int64")
        
df = df.drop(
    columns=[
        "developers",
        "publishers",
        "categories",
        "genres",
        "tags",
        "publisher_name",
        "genre_name"
    ],
    errors="ignore"
)

print("Запуск пакетной вставки основной таблицы games_pg (chunksize=1000)...")

start_time = time.time()

try:
    df.to_sql(
        "games_pg",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=1000
    )
except Exception as e:
    print(f"\n[ОШИБКА] Не удалось записать игры в PostgreSQL: {e}")
    raise e

batch_load_time = time.time() - start_time
print(f"Время пакетной загрузки игр: {batch_load_time:.2f} сек.")

conn_copy = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    dbname="postgres",
    user="postgres",
    password="secret"
)

cur_copy = conn_copy.cursor()
cur_copy.execute("TRUNCATE TABLE games_pg;")
conn_copy.commit()

print("\nЗапуск загрузки методом COPY...")

start_time = time.time()

try:
    buffer = io.StringIO()

    df.to_csv(
        buffer,
        index=False,
        header=False,
        sep="\t",
        na_rep="\\N"
    )

    buffer.seek(0)

    columns = ", ".join(f'"{col}"' for col in df.columns)

    cur_copy.copy_expert(
        f"COPY games_pg ({columns}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '\\N')",
        buffer
    )

    conn_copy.commit()

except Exception as e:
    conn_copy.rollback()
    print(f"\n[ОШИБКА] Не удалось загрузить игры методом COPY: {e}")
    raise e

copy_load_time = time.time() - start_time

print(f"Время загрузки методом COPY: {copy_load_time:.2f} сек.")

cur_copy.close()
conn_copy.close()

print("\nСРАВНЕНИЕ ВРЕМЕНИ ЗАГРУЗКИ")
print(f"Пакетная вставка: {batch_load_time:.2f} сек.")
print(f"Метод COPY: {copy_load_time:.2f} сек.")

if copy_load_time < batch_load_time:
    print("Метод COPY оказался быстрее.")
elif copy_load_time > batch_load_time:
    print("Пакетная вставка оказалась быстрее.")
else:
    print("Время загрузки обоими способами одинаковое.")

conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    dbname="postgres",
    user="postgres",
    password="secret"
)

conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT pg_database_size('postgres');")
size_bytes = cur.fetchone()[0]
size_mb = size_bytes / (1024 * 1024)
print(f"\n[Метрика] Объём хранилища БД: {size_mb:.2f} МБ")

start_time = time.time()

cur.execute("""
    SELECT g.peak_ccu, AVG(g.price), COUNT(*), p.publisher_name
    FROM games_pg g
    LEFT JOIN publishers p ON g.publisher_id = p.publisher_id
    GROUP BY g.peak_ccu, p.publisher_name
    LIMIT 100;
""")

cur.fetchall()
agg_time = time.time() - start_time
print(f"[Запрос] С агрегированием и JOIN: {agg_time:.4f} сек.")

cur.execute("DROP INDEX IF EXISTS idx_pg_release_date;")

query_date = """
SELECT *
FROM games_pg
WHERE release_date BETWEEN '2020-01-01 00:00:00'
AND '2023-12-31 23:59:59';
"""

start_time = time.time()
cur.execute(query_date)
cur.fetchall()
no_idx_time = time.time() - start_time
print(f"[Запрос] Выборка без индекса: {no_idx_time:.4f} сек.")

cur.execute(
    "CREATE INDEX IF NOT EXISTS idx_pg_release_date ON games_pg(release_date);"
)

start_time = time.time()
cur.execute(query_date)
cur.fetchall()
with_idx_time = time.time() - start_time
print(f"[Запрос] Выборка с индексом: {with_idx_time:.4f} сек.")

cur.close()
conn.close()

print("\nВСЕ ТЕСТЫ И ЗАМЕРЫ ДЛЯ POSTGRESQL УСПЕШНО ЗАВЕРШЕНЫ")
