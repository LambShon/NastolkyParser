CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    price INTEGER NOT NULL,
    link TEXT NOT NULL UNIQUE,
    tags_num TEXT,
    tags TEXT
);