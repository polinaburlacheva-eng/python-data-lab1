import pandas as pd
from pathlib import Path

input_file = Path("data/raw/Steam Games Dataset/games.csv")
output_file = Path("data/interim/games.csv")

df = pd.read_csv(input_file, nrows=200_000, index_col=False)

df.to_csv(output_file, index=False, encoding="utf-8")

print("Строк:", len(df))
print("Файл:", output_file)
print("Количество строк в срезе:", len(df))
print("Количество столбцов:", len(df.columns))