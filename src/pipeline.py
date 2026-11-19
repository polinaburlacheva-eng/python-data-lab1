import argparse
import logging
from pathlib import Path
import pandas as pd

from cleaning import (
    normalize_column_names,
    handle_missing_values,
    remove_duplicates,
    normalize_categories,
    validate_and_filter_outliers,
)
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=log_dir / "pipeline.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
def run_pipeline(
    input_path: Path, output_path: Path, mode: str = "full", step: str = None
):
    logging.info(f"Запуск пайплайна. Режим: {mode}, Шаг: {step or 'все'}")

    try:
        if not input_path.exists():
            raise FileNotFoundError(
                f"Входной файл не найден по пути: {input_path}"
            )
        df = pd.read_parquet(input_path)

        if mode == "debug":
            df = df.head(1000)
            logging.info("Применен отладочный режим: взята выборка из 1000 строк.")

        initial_count = len(df)

        if step == "normalize_columns" or step is None:
            df = normalize_column_names(df)
        if step == "missing_values" or step is None:
            df = handle_missing_values(df)
        if step == "duplicates" or step is None:
            df = remove_duplicates(df)
        if step == "categories" or step is None:
            df = normalize_categories(df)
        if step == "outliers" or step is None:
            df = validate_and_filter_outliers(df)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, compression="zstd")

        logging.info(f"Пайплайн успешно завершен. Итог строк: {len(df)}")
        return df

    except Exception as e:
        logging.error(f"Ошибка при выполнении пайплайна: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Сквозной пайплайн очистки данных Steam"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/interim/games_typed.parquet",
        help="Путь к входному файлу",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/clean.parquet",
        help="Путь к результату",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["full", "debug"],
        default="full",
        help="Режим работы: полный набор или срез",
    )
    parser.add_argument(
        "--step",
        type=str,
        default=None,
        help="Конкретный этап для запуска (опционально)",
    )

    args = parser.parse_args()
    run_pipeline(
        Path(args.input), Path(args.output), mode=args.mode, step=args.step
    )