from pathlib import Path
import pandas as pd

file_path = Path("data/raw/Steam Games Dataset/games.csv")
print("Размер файла:", file_path.stat().st_size / 1024 / 1024, "MB")

with open(file_path, "r", encoding="utf-8") as file:
    row_count = sum(1 for _ in file)

print("Количество строк:", row_count)

df = pd.read_csv(file_path, nrows=100, index_col=False)


print("\nСтолбцы:")
print(df.columns.tolist())

print("\nПервые 100 строк:")
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 20)
print(df)

