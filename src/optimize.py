import time
from pathlib import Path
import pandas as pd
from config import STEAM_SCHEMA  

path_parquet = Path("data/interim/games.parquet")
path_optimized = Path("data/interim/games_typed.parquet")

# До оптимизации
start = time.perf_counter()
df = pd.read_parquet(path_parquet)
read_time_before = time.perf_counter() - start

mem_before = df.memory_usage(deep=True).sum() / 1024**2
file_size_before = path_parquet.stat().st_size / 1024 / 1024

start = time.perf_counter()
_ = df.groupby("Genres")["Price"].median()
group_time_before = time.perf_counter() - start

cat_cols_before = sum(1 for col in df.columns if str(df[col].dtype) == "category")

active_schema = {
    col: dtype for col, dtype in STEAM_SCHEMA.items() if col in df.columns
}

for col, dtype in active_schema.items():
    if dtype != "category":
        df[col] = df[col].astype(dtype, errors="ignore")
    else:
        df[col] = df[col].astype("category")

if "Release date" in df.columns:
    df["Release date"] = pd.to_datetime(df["Release date"], errors="coerce")

df.to_parquet(path_optimized, compression="zstd")

# После оптимизации
start = time.perf_counter()
df_opt = pd.read_parquet(path_optimized)
df_opt["Developers"] = df_opt["Developers"].astype("category")
read_time_after = time.perf_counter() - start

mem_after = df_opt.memory_usage(deep=True).sum() / 1024**2
file_size_after = path_optimized.stat().st_size / 1024 / 1024

start = time.perf_counter()
_ = df_opt.groupby("Genres")["Price"].median()
group_time_after = time.perf_counter() - start

cat_cols_after = sum(1 for col in df_opt.columns if str(df_opt[col].dtype) == "category")

#Вывод результатов 
print("\n" + "=" * 80)
print(f"{'Показатель':<30} | {'До оптимизации':<16} | {'После':<12} | {'Изменение':<15}")
print("-" * 80)

metrics = [
    ("Объём файла на диске, МБ", file_size_before, file_size_after, f"{(file_size_after - file_size_before):.2f} МБ"),
    ("Объём в памяти, МБ", mem_before, mem_after, f"{(mem_after - mem_before):.2f} МБ"),
    ("Время чтения, с", read_time_before, read_time_after, f"{(read_time_before / read_time_after):.1f}x быстрее" if read_time_after > 0 else "-"),
    ("Время группировки, с", group_time_before, group_time_after, f"{(group_time_before / group_time_after):.1f}x быстрее" if group_time_after > 0 else "-"),
    ("Число столбцов типа category", cat_cols_before, cat_cols_after, f"+{cat_cols_after - cat_cols_before}")
]
for name, val_before, val_after, change in metrics:
    b_str = f"{val_before:.2f}" if isinstance(val_before, float) else str(val_before)
    a_str = f"{val_after:.2f}" if isinstance(val_after, float) else str(val_after)
    print(f"{name:<30} | {b_str:<16} | {a_str:<12} | {change:<15}")

print("=" * 80)
