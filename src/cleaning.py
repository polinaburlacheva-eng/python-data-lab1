import logging
from pathlib import Path
import numpy as np
import pandas as pd

log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)
# ЖУРНАЛ 
logging.basicConfig(
    filename=log_dir / "pipeline.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """1. Приведение имён столбцов к нижнему регистру и замена пробелов."""
    df = df.copy()
    initial_cols = df.columns.tolist()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    logging.info(
        f"Имена столбцов приведены к стандарту snake_case. Обработано столбцов: {len(initial_cols)}"
    )
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """2. Выявление скрытых пропусков и их приведение к NaN."""
    df = df.copy()
    initial_nulls = df.isna().sum().sum()

    missing_placeholders = [
        "none",
        "null",
        "n/a",
        "-",
        "unknown",
        "no data",
        "",
    ]

    for col in df.select_dtypes(include=["object", "category", "string"]):
        df[col] = df[col].replace(missing_placeholders, np.nan)

    new_nulls = df.isna().sum().sum()
    logging.info(
        f"Скрытые пропуски обработаны. Найдено и заменено пропусков: {new_nulls - initial_nulls}"
    )
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """3. Удаление полных дубликатов и дубликатов по ключу appid."""
    df = df.copy()
    initial_rows = len(df)

    df = df.drop_duplicates()
    after_full_dups = len(df)

    if "appid" in df.columns:
        if "release_date" in df.columns:
            df["release_date_dt"] = pd.to_datetime(
                df["release_date"], errors="coerce"
            )
            df = df.sort_values("release_date_dt").drop_duplicates(
                subset=["appid"], keep="last"
            )
            df = df.drop(columns=["release_date_dt"])
        else:
            df = df.drop_duplicates(subset=["appid"], keep="last")

    removed = initial_rows - len(df)
    logging.info(
        f"Дубликаты удалены. Было: {initial_rows}, стало: {len(df)}, удалено: {removed}"
    )
    return df


def normalize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """4. Нормализация категориальных и текстовых полей."""
    df = df.copy()
    text_cols = ["developers", "publishers", "genres"]

    for col in text_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .replace({"nan": np.nan, "None": np.nan})
            )

    logging.info("Категориальные столбцы очищены от лишних пробелов.")
    return df


def validate_and_filter_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """5. Проверка предметных ограничений и выявление выбросов (IQR)."""
    df = df.copy()
    initial_rows = len(df)


    if "price" in df.columns:
        df = df[df["price"] >= 0]
    if "positive" in df.columns:
        df = df[df["positive"] >= 0]
    if "negative" in df.columns:
        df = df[df["negative"] >= 0]

  
    if "price" in df.columns:
        q99 = df["price"].quantile(0.99)
        df = df[df["price"] <= q99 * 2]  

    removed = initial_rows - len(df)
    logging.info(
        f"Валидация и удаление выбросов завершены. Удалено аномальных строк: {removed}"
    )
    return df


def clean_pipeline(input_path: Path, output_path: Path) -> pd.DataFrame:
    """Сквозной процесс очистки с сохранением результата."""
    logging.info(f"Начало очистки данных из файла: {input_path}")

    #Загрузка
    df_raw = pd.read_parquet(input_path)
    initial_count = len(df_raw)

   
    df = normalize_column_names(df_raw)
    df = handle_missing_values(df)
    df = remove_duplicates(df)
    df = normalize_categories(df)
    df = validate_and_filter_outliers(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(output_path, compression="zstd")

    final_count = len(df)
    loss_pct = (initial_count - final_count) / initial_count * 100

    logging.info("=== СВОДКА ОЧИСТКИ ДАННЫХ ===")
    logging.info(f"Исходное количество строк: {initial_count}")
    logging.info(f"Итоговое количество строк:  {final_count}")
    logging.info(f"Удалено строк:             {initial_count - final_count}")
    logging.info(f"Доля потерянных записей:   {loss_pct:.2f}%")
    logging.info(f"Сохранено в:               {output_path}")
    
    return df

if __name__ == "__main__":
    in_file = Path("data/interim/games_typed.parquet")
    out_file = Path("data/processed/clean.parquet")
    clean_pipeline(in_file, out_file)

