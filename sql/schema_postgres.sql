-- DDL Схема данных PostgreSQL (Steam Games Dataset - 3NF)
-- Удаляем старые таблицы в правильном порядке
DROP TABLE IF EXISTS games_pg CASCADE;
DROP TABLE IF EXISTS publishers CASCADE;
DROP TABLE IF EXISTS genres CASCADE;
-- 1. Справочник издателей
CREATE TABLE publishers (
    publisher_id SERIAL PRIMARY KEY,
    publisher_name TEXT UNIQUE NOT NULL
);
-- 2. Справочник жанров
CREATE TABLE genres (
    genre_id SERIAL PRIMARY KEY,
    genre_name TEXT UNIQUE NOT NULL
);

-- 3. Основная таблица игр
CREATE TABLE games_pg (
    appid VARCHAR(255) PRIMARY KEY,
    name TEXT NOT NULL,
    release_date TIMESTAMP,
    estimated_owners TEXT,
    peak_ccu INTEGER,
    required_age DOUBLE PRECISION,
    price NUMERIC(10, 2),
    discountdlc_count INTEGER,
    about_the_game TEXT,
    supported_languages TEXT,
    full_audio_languages TEXT,
    reviews TEXT,
    header_image TEXT,
    website TEXT,
    support_url TEXT,
    support_email TEXT,
    windows BOOLEAN,
    mac BOOLEAN,
    linux BOOLEAN,
    metacritic_score DOUBLE PRECISION,
    metacritic_url TEXT,
    user_score DOUBLE PRECISION,
    positive INTEGER,
    negative INTEGER,
    score_rank DOUBLE PRECISION,
    achievements INTEGER,
    recommendations INTEGER,
    notes TEXT,
    average_playtime_forever DOUBLE PRECISION,
    average_playtime_two_weeks DOUBLE PRECISION,
    median_playtime_forever DOUBLE PRECISION,
    median_playtime_two_weeks DOUBLE PRECISION,
    screenshots TEXT,
    movies DOUBLE PRECISION,
    publisher_id INTEGER,
    genre_id INTEGER,

    CONSTRAINT fk_publisher
        FOREIGN KEY (publisher_id)
        REFERENCES publishers(publisher_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_genre
        FOREIGN KEY (genre_id)
        REFERENCES genres(genre_id)
        ON DELETE SET NULL
);


-- 4. Индекс для ускорения выборок по дате выпуска
CREATE INDEX idx_pg_release_date
ON games_pg(release_date);