##Схема оптимизированных типов данных 
STEAM_SCHEMA = {
    "AppID": "string",
    "Name": "string",
    "Release date": "datetime64[ns]",  
    "Estimated owners": "string", 
    "Peak CCU": "int32",
    "Required age": "float32", 
    "Price": "float32",  
    "DiscountDLC count": "int16",
    "Windows": "boolean",
    "Mac": "boolean",
    "Linux": "boolean",
    "Metacritic score": "float32",
    "User score": "float32",
    "Positive": "int32",
    "Negative": "int32",
    "Achievements": "int32",
    "Recommendations": "int32",
    "Average playtime forever": "float32",
    "Average playtime two weeks": "float32",
    "Median playtime forever": "float32",
    "Median playtime two weeks": "float32",
    "Developers": "category",  # повторяющиеся разработчики в категорию
    "Publishers": "category",  # повторяющиеся издатели в категорию
    "Genres": "category",      # жанры в категорию
}