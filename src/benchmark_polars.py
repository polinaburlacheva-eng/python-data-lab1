import time
from pathlib import Path
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt

path_parquet = Path("data/interim/games_typed.parquet")

# 1. Чтение Parquet
start = time.perf_counter()
pdf = pd.read_parquet(path_parquet)
time_pd_read = time.perf_counter() - start

start = time.perf_counter()
pldf = pl.read_parquet(path_parquet)
time_pl_read = time.perf_counter() - start


# 2. Фильтрация
start = time.perf_counter()
pdf_filtered = pdf[(pdf["Price"] > 10) & (pdf["Positive"] > 1000)]
time_pd_filter = time.perf_counter() - start

start = time.perf_counter()
pldf_filtered = pldf.filter(
    (pl.col("Price") > 10) & (pl.col("Positive") > 1000)
)
time_pl_filter = time.perf_counter() - start


# 3. Группировка и агрегирование
start = time.perf_counter()
pdf_grouped = pdf.groupby("Genres")["Price"].median().reset_index()
time_pd_group = time.perf_counter() - start

start = time.perf_counter()
pldf_grouped = (
    pldf.group_by("Genres").agg(pl.col("Price").median()).to_pandas()
)
time_pl_group = time.perf_counter() - start


# 4.Сортировка
start = time.perf_counter()
pdf_sorted = pdf.sort_values(by="Price", ascending=False)  # <-- Заменили pdf_grouped на pdf
time_pd_sort = time.perf_counter() - start

start = time.perf_counter()
pldf_sorted = pldf.sort("Price", descending=True)  # <-- Заменили pldf_grouped на pldf и поставили нативный метод Polars
time_pl_sort = time.perf_counter() - start


# 5. Соединение таблиц 
ref_data = pd.DataFrame(
    {"Genres": pdf["Genres"].dropna().unique()[:10], "Category_Type": "Standard"}
)
ref_pl = pl.from_pandas(ref_data)

start = time.perf_counter()
pdf_merged = pd.merge(pdf, ref_data, on="Genres", how="left")
time_pd_merge = time.perf_counter() - start

start = time.perf_counter()
pldf_merged = pldf.join(ref_pl, on="Genres", how="left")
time_pl_merge = time.perf_counter() - start


# 6. Цепочка операций в ленивом режиме (только Polars)
start = time.perf_counter()
lazy_result = (
    pl.scan_parquet(path_parquet)
    .filter((pl.col("Price") > 10) & (pl.col("Positive") > 1000))
    .group_by("Genres")
    .agg(pl.col("Price").median())
    .sort("Price", descending=True)
    .collect()
)
time_pl_lazy = time.perf_counter() - start


# Вывод результатов
print("\n" + "=" * 80)
print(f"{'Операция':<35} | {'Pandas, с':<12} | {'Polars, с':<12} | {'Ускорение':<12}")
print("-" * 80)

operations = [
    ("Чтение Parquet", f"{time_pd_read:.4f}", f"{time_pl_read:.4f}", f"{time_pd_read / time_pl_read:.1f}x"),
    ("Фильтрация", f"{time_pd_filter:.4f}", f"{time_pl_filter:.4f}", f"{time_pd_filter / time_pl_filter:.1f}x"),
    ("Группировка и агрегирование", f"{time_pd_group:.4f}", f"{time_pl_group:.4f}", f"{time_pd_group / time_pl_group:.1f}x"),
    ("Сортировка", f"{time_pd_sort:.4f}", f"{time_pl_sort:.4f}", f"{time_pd_sort / time_pl_sort:.1f}x"),
    ("Соединение таблиц", f"{time_pd_merge:.4f}", f"{time_pl_merge:.4f}", f"{time_pd_merge / time_pl_merge:.1f}x"),
    ("Цепочка операций (Lazy)", "-", f"{time_pl_lazy:.4f}", "-"),
]

for op, t_pd, t_pl, speedup in operations:
    print(f"{op:<35} | {t_pd:<12} | {t_pl:<12} | {speedup:<12}")

print("=" * 80)

# Построение диаграммы сравнения производительности
op_names = [item[0] for item in operations]
pd_times = [time_pd_read, time_pd_filter, time_pd_group, time_pd_sort, time_pd_merge, 0]
pl_times = [time_pl_read, time_pl_filter, time_pl_group, time_pl_sort, time_pl_merge, time_pl_lazy]

x = range(len(op_names))
width = 0.35

plt.figure(figsize=(10, 5))
plt.bar([i - width/2 for i in x], pd_times, width, label='Pandas', color='#d9534f', alpha=0.85, edgecolor='black')
plt.bar([i + width/2 for i in x], pl_times, width, label='Polars', color='#5cb85c', alpha=0.85, edgecolor='black')

plt.ylabel("Время выполнения, секунды")
plt.title("Сравнение производительности Pandas и Polars")
plt.xticks(x, op_names, rotation=15, ha='right')
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout() 
plt.show()