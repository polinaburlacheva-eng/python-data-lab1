import time
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

#Пути к файлам 
input_csv = Path("data/raw/Steam Games Dataset/games.csv")
dir_interim = Path("data/interim")
dir_interim.mkdir(parents=True, exist_ok=True)

path_pickle = dir_interim / "games.pkl"
path_feather = dir_interim / "games.feather"
path_parquet = dir_interim / "games.parquet"

df = pd.read_csv(input_csv, index_col=False)
csv_read_time = time.perf_counter()
#Перезамер для чистоты 
start = time.perf_counter()
pd.read_csv(input_csv, index_col=False)
csv_read_time = time.perf_counter() - start
csv_size = input_csv.stat().st_size / 1024 / 1024


#Функция для точного замера времени 
def measure_time(func, *args, repeats=3, **kwargs):
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        func(*args, **kwargs)
        times.append(time.perf_counter() - start)
    return sorted(times)[len(times) // 2]  # медиана


start = time.perf_counter()
df.to_pickle(path_pickle)
pickle_write_time = time.perf_counter() - start
pickle_size = path_pickle.stat().st_size / 1024 / 1024
pickle_read_time = measure_time(pd.read_pickle, path_pickle)

start = time.perf_counter()
df.to_feather(path_feather)
feather_write_time = time.perf_counter() - start
feather_size = path_feather.stat().st_size / 1024 / 1024
feather_read_time = measure_time(pd.read_feather, path_feather)

start = time.perf_counter()
df.to_parquet(path_parquet, compression="snappy")
parquet_write_time = time.perf_counter() - start
parquet_size = path_parquet.stat().st_size / 1024 / 1024
parquet_read_time = measure_time(pd.read_parquet, path_parquet)

cols_to_read = ["AppID", "Name", "Price"]
parquet_3cols_time = measure_time(pd.read_parquet, path_parquet, columns=cols_to_read)

# Вывод результатов 
print("\n" + "=" * 85)
print(f"{'Формат':<20} | {'Объём, МБ':<12} | {'Запись, с':<12} | {'Чтение, с':<12} | {'Отношение к CSV':<15}")
print("-" * 85)

results = [
    ("CSV (исходный)", csv_size, 0.0, csv_read_time, 1.0),
    ("Pickle", pickle_size, pickle_write_time, pickle_read_time, csv_read_time / pickle_read_time if pickle_read_time > 0 else 0),
    ("Feather", feather_size, feather_write_time, feather_read_time, csv_read_time / feather_read_time if feather_read_time > 0 else 0),
    ("Parquet (snappy)", parquet_size, parquet_write_time, parquet_read_time, csv_read_time / parquet_read_time if parquet_read_time > 0 else 0),
    ("Parquet, 3 столбца", "-", "-", parquet_3cols_time, csv_read_time / parquet_3cols_time if parquet_3cols_time > 0 else 0),
]

for fmt, size, write_t, read_t, ratio in results:
    s_str = f"{size:.2f}" if isinstance(size, float) else str(size)
    w_str = f"{write_t:.2f}" if isinstance(write_t, float) else str(write_t)
    r_str = f"{read_t:.2f}" if isinstance(read_t, float) else str(read_t)
    print(f"{fmt:<20} | {s_str:<12} | {w_str:<12} | {r_str:<12} | {ratio:<15.2f}")

print("=" * 85)

# Построение диаграммы времени чтения
formats = ['CSV', 'Pickle', 'Feather', 'Parquet', 'Parquet (3 col)']
read_times = [csv_read_time, pickle_read_time, feather_read_time, parquet_read_time, parquet_3cols_time]

plt.figure(figsize=(9, 4.5))
bars = plt.bar(formats, read_times, color=['#d9534f', '#f0ad4e', '#5bc0de', '#5cb85c', '#0275d8'], alpha=0.85, edgecolor='black')

plt.ylabel("Время чтения, секунды")
plt.title("Сравнение времени чтения различных форматов")
plt.grid(axis='y', linestyle='--', alpha=0.5)

for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.05, f"{height:.2f}с",
             ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.show()