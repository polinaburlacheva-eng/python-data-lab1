import sqlite3
import time
from pathlib import Path
import pandas as pd


def run_sqlite_benchmark():
    db_path = Path("data/processed/games.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    parquet_path = Path("data/processed/clean.parquet")
    df = pd.read_parquet(parquet_path)

    print("1. ЗАГРУЗКА В SQLITE И НОРМАЛИЗАЦИЯ")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    num_cols = ["appid", "required_age", "peak_ccu", "positive", "negative", "achievements", "recommendations", "average_playtime_forever", "average_playtime_two_weeks", "median_playtime_forever", "median_playtime_two_weeks", "discountdlc_count", "price"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            if col != "appid" and col != "price":
                df[col] = df[col].astype(int)

    if "appid" in df.columns:
        df = df.dropna(subset=["appid"])
        df = df[df["appid"].astype(str).str.lower() != "nan"]
        df = df[df["appid"].astype(str).str.strip() != ""]
        df = df.drop_duplicates(subset=["appid"])
        df["appid"] = df["appid"].astype(str)

    start = time.perf_counter()

    if "publishers" in df.columns:
        pubs = []
        for val in df["publishers"].dropna():
            vals = [v.strip() for v in str(val).split(",") if v.strip() and v.strip().lower() != "nan"]
            if vals:
                pubs.append(vals[0])
        
        unique_pubs = pd.DataFrame({"publisher_name": list(set(pubs))})
        unique_pubs.to_sql("publishers", conn, if_exists="replace", index=False)
        
        cursor.execute("CREATE TABLE IF NOT EXISTS publishers_temp AS SELECT publisher_name FROM publishers;")
        cursor.execute("DROP TABLE publishers;")
        cursor.execute("""
            CREATE TABLE publishers (
                publisher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                publisher_name TEXT UNIQUE NOT NULL
            );
        """)
        cursor.execute("INSERT INTO publishers (publisher_name) SELECT publisher_name FROM publishers_temp;")
        cursor.execute("DROP TABLE publishers_temp;")
        conn.commit()

        ref_pubs = pd.read_sql("SELECT publisher_id, publisher_name FROM publishers", conn)
        pub_map = dict(zip(ref_pubs["publisher_name"], ref_pubs["publisher_id"]))
        
        df["publisher_id"] = df["publishers"].apply(lambda x: pub_map.get(str(x).split(",")[0].strip()) if pd.notna(x) else None)

    if "genres" in df.columns:
        gens = []
        for val in df["genres"].dropna():
            vals = [v.strip() for v in str(val).split(",") if v.strip() and v.strip().lower() != "nan"]
            if vals:
                gens.append(vals[0]) 
        
        unique_gens = pd.DataFrame({"genre_name": list(set(gens))})
        unique_gens.to_sql("genres", conn, if_exists="replace", index=False)
        
        cursor.execute("CREATE TABLE IF NOT EXISTS genres_temp AS SELECT genre_name FROM genres;")
        cursor.execute("DROP TABLE genres;")
        cursor.execute("""
            CREATE TABLE genres (
                genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
                genre_name TEXT UNIQUE NOT NULL
            );
        """)
        cursor.execute("INSERT INTO genres (genre_name) SELECT genre_name FROM genres_temp;")
        cursor.execute("DROP TABLE genres_temp;")
        conn.commit()

        ref_gens = pd.read_sql("SELECT genre_id, genre_name FROM genres", conn)
        genre_map = dict(zip(ref_gens["genre_name"], ref_gens["genre_id"]))
        
        df["genre_id"] = df["genres"].apply(lambda x: genre_map.get(str(x).split(",")[0].strip()) if pd.notna(x) else None)

    games_df = df.drop(columns=["developers", "publishers", "categories", "genres", "tags"], errors="ignore")
    games_df.to_sql("games", conn, if_exists="replace", index=False, chunksize=10000)

    load_time = time.perf_counter() - start
    file_size_mb = db_path.stat().st_size / (1024 * 1024)
    
    print(f"Время загрузки: {load_time:.2f} сек")
    print(f"Объём файла БД на диске: {file_size_mb:.2f} МБ")

    print("\n2. КОНТРОЛЬНЫЕ ЗАПРОСЫ")

    start = time.perf_counter()
    cursor.execute(
        "SELECT g.genre_name, AVG(gm.price) FROM genres g JOIN games gm ON g.genre_id = gm.genre_id GROUP BY g.genre_name LIMIT 10;"
    )
    _ = cursor.fetchall()
    agg_time = time.perf_counter() - start
    print(f"Запрос с агрегированием: {agg_time:.4f} сек")

    if "release_date" in df.columns:
        start = time.perf_counter()
        cursor.execute(
            "SELECT COUNT(*) FROM games WHERE release_date BETWEEN '2020-01-01' AND '2022-12-31';"
        )
        _ = cursor.fetchone()
        date_time_no_idx = time.perf_counter() - start
        print(f"Выборка по датам БЕЗ индекса: {date_time_no_idx:.4f} сек")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_release_date ON games(release_date);")
        conn.commit()

        start = time.perf_counter()
        cursor.execute(
            "SELECT COUNT(*) FROM games WHERE release_date BETWEEN '2020-01-01' AND '2022-12-31';"
        )
        _ = cursor.fetchone()
        date_time_idx = time.perf_counter() - start
        print(f"Выборка по датам С индексом: {date_time_idx:.4f} сек")
    else:
        date_time_no_idx, date_time_idx = 0.0, 0.0

    conn.close()
    return load_time, file_size_mb, agg_time, date_time_no_idx, date_time_idx


if __name__ == "__main__":
    run_sqlite_benchmark()