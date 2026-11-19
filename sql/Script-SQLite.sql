DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS publishers;
DROP TABLE IF EXISTS genres;

-- Справочник издателей
CREATE TABLE publishers (
    publisher_id INTEGER PRIMARY KEY AUTOINCREMENT,
    publisher_name TEXT UNIQUE NOT NULL
);

-- Справочник жанров
CREATE TABLE genres (
    genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_name TEXT UNIQUE NOT NULL
);

-- Главная таблица игр со ссылками на справочники
CREATE TABLE games (
    appid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    release_date TIMESTAMP,
    estimated_owners TEXT,
    peak_ccu INTEGER,
    required_age REAL,
    price REAL,
    discountdlc_count INTEGER,
    about_the_game TEXT,
    supported_languages TEXT,
    full_audio_languages TEXT,
    reviews TEXT,
    header_image TEXT,
    website TEXT,
    support_url TEXT,
    support_email TEXT,
    windows INTEGER,
    mac INTEGER,
    linux INTEGER,
    metacritic_score REAL,
    metacritic_url TEXT,
    user_score REAL,
    positive INTEGER,
    negative INTEGER,
    score_rank REAL,
    achievements INTEGER,
    recommendations INTEGER,
    notes TEXT,
    average_playtime_forever REAL,
    average_playtime_two_weeks REAL,
    median_playtime_forever REAL,
    median_playtime_two_weeks REAL,
    screenshots TEXT,
    movies REAL,
    publisher_id INTEGER,
    genre_id INTEGER,
    FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id) ON DELETE SET NULL,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE SET NULL
);

CREATE INDEX idx_release_date ON games(release_date);