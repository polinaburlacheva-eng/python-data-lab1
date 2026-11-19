import pandas as pd
import numpy as np
import time

def get_target_summary(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    Рассчитывает сводку распределения целевой переменной.
    Возвращает DataFrame формата 'Показатель' — 'Значение' для Таблицы 1.
    """
    series = df[target_col]
    valid = series.dropna()

    count = int(valid.count())
    missing = int(series.isna().sum())
    minimum = float(valid.min())
    q1 = float(valid.quantile(0.25))
    median = float(valid.median())
    mean = float(valid.mean())
    q3 = float(valid.quantile(0.75))
    maximum = float(valid.max())

    # Определяем направление скошенности по соотношению среднего и медианы
    skew_val = float(valid.skew())
    if mean > median and skew_val > 0.1:
        skew_label = "Вправо (положительная)"
    elif mean < median and skew_val < -0.1:
        skew_label = "Влево (отрицательная)"
    else:
        skew_label = "Близко к симметричному"

    summary_rows = [
        ("Число наблюдений", count),
        ("Число пропусков", missing),
        ("Минимум", round(minimum, 2)),
        ("Первый квартиль", round(q1, 2)),
        ("Медиана", round(median, 2)),
        ("Среднее", round(mean, 2)),
        ("Третий квартиль", round(q3, 2)),
        ("Максимум", round(maximum, 2)),
        ("Скошенность", skew_label),
    ]

    return pd.DataFrame(summary_rows, columns=["Показатель", "Значение"])

def get_date_dynamics(
    df: pd.DataFrame, date_col: str, target_col: str, freq: str = "MS"
) -> pd.DataFrame:

    temp = df[[date_col, target_col]].copy()

    temp[date_col] = pd.to_datetime(
        temp[date_col], format="mixed", errors="coerce"
    )

    temp = temp.dropna(subset=[date_col])

    temp["period"] = temp[date_col].dt.to_period("M").dt.to_timestamp()

    grouped = (
        temp.groupby("period")
        .agg(
            record_count=(date_col, "size"),
            median_target=(target_col, "median"),
            mean_target=(target_col, "mean"),
        )
    )

    full_range = pd.date_range(
        start=temp["period"].min(),
        end=temp["period"].max(),
        freq=freq,
    )

    result = grouped.reindex(full_range)

    result["record_count"] = result["record_count"].fillna(0).astype(int)
    result["median_target"] = result["median_target"].round(2)
    result["mean_target"] = result["mean_target"].round(2)

    result = result.reset_index().rename(
        columns={
            "index": "Период",
            "record_count": "Число записей",
            "median_target": "Медиана цели",
            "mean_target": "Среднее цели",
        }
    )

    result["Период"] = result["Период"].dt.strftime("%Y-%m")

    return result

def get_group_aggregates(df, group_col, target_col):
    temp = df[[group_col, target_col]].copy()

    temp[target_col] = pd.to_numeric(
        temp[target_col], errors="coerce"
    )

    temp[group_col] = (
        temp[group_col].astype("object").fillna("Не указано")
    )

    result = (
        temp.groupby(group_col, observed=True)
        .agg(
            Число_записей=(target_col, "size"),
            Медиана=(target_col, "median"),
            Среднее=(target_col, "mean"),
            Доля_пропусков=(
                target_col,
                lambda x: x.isna().mean() * 100
            )
        )
        .reset_index()
        .sort_values("Число_записей", ascending=False)
    )

    result = result.rename(columns={
        "Число_записей": "Число записей",
        "Доля_пропусков": "Доля пропусков, %"
    })

    result[["Медиана", "Среднее", "Доля пропусков, %"]] = (
        result[["Медиана", "Среднее", "Доля пропусков, %"]].round(2)
    )

    return result

def get_group_period_pivot(df, group_col, target_col, date_col):
    temp = df[[group_col, target_col, date_col]].copy()

    temp[group_col] = (
        temp[group_col].astype("object").fillna("Не указано")
    )

    temp[target_col] = pd.to_numeric(
        temp[target_col], errors="coerce"
    )

    temp[date_col] = pd.to_datetime(
        temp[date_col], errors="coerce"
    )

    temp["Год"] = temp[date_col].dt.year

    pivot = temp.pivot_table(
        index=group_col,
        columns="Год",
        values=target_col,
        aggfunc="median",
        observed=True
    )

    return pivot

import logging

logger = logging.getLogger(__name__)


def detect_anomalies(df: pd.DataFrame, target_col: str) -> dict:
    """
    Шаг 6: Находит аномалии по двум заранее заданным правилам:
      1) Межквартильный размах: выход за [Q1 - 1.5*IQR; Q3 + 1.5*IQR].
      2) Статистическое правило Z-оценки: |z| > 3.
    Исходный DataFrame и clean.parquet не изменяются.
    Возвращает словарь с булевыми масками и числом отмеченных строк.
    """
    series = df[target_col]
    valid = series.dropna()

    # Правило 1: межквартильный размах (IQR)
    q1 = float(valid.quantile(0.25))
    q3 = float(valid.quantile(0.75))
    iqr = q3 - q1
    lower_iqr = q1 - 1.5 * iqr
    upper_iqr = q3 + 1.5 * iqr
    mask_iqr = (series < lower_iqr) | (series > upper_iqr)
    count_iqr = int(mask_iqr.sum())

    # Правило 2: модуль z-оценки > 3
    mean_val = float(valid.mean())
    std_val = float(valid.std())
    if std_val > 0:
        z_scores = (series - mean_val) / std_val
        mask_z = z_scores.abs() > 3
    else:
        mask_z = pd.Series(False, index=df.index)
    count_z = int(mask_z.sum())

    # Пересечение двух списков
    mask_both = mask_iqr & mask_z
    count_both = int(mask_both.sum())

    # Запись в журнал
    log_msg = (
        f"[Шаг 6 | Аномалии по '{target_col}'] "
        f"Правило 1 (IQR, границы [{lower_iqr:.2f}; {upper_iqr:.2f}]): {count_iqr} строк; "
        f"Правило 2 (|z| > 3, порог > {mean_val + 3 * std_val:.2f}): {count_z} строк; "
        f"Пересечение: {count_both} строк."
    )
    logger.info(log_msg)
    print(log_msg)

    return {
        "mask_iqr": mask_iqr,
        "count_iqr": count_iqr,
        "mask_z": mask_z,
        "count_z": count_z,
        "mask_both": mask_both,
        "count_both": count_both,
    }


def mean_loop(values):
    total = 0.0
    count = 0
    for value in values:
        if value == value:  # пропуск не равен себе
            total += float(value)
            count += 1
    return total / count

def mean_numpy(values):
    array = np.asarray(values, dtype="float64")
    return float(np.nanmean(array))

def median_seconds(func, values):
    func(values)  # первый прогон разогревает кэш
    marks = []
    for _ in range(3):
        started = time.perf_counter()
        func(values)
        marks.append(time.perf_counter() - started)
    marks.sort()
    return marks[1]