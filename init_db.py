import sqlite3
import os

# Удаляем старую базу если есть
if os.path.exists("database.db"):
    print("⚠️  Удаляю старую базу данных...")
    os.remove("database.db")

conn = sqlite3.connect("database.db")
cur = conn.cursor()

print("🔄 Создаю таблицы...")

# 1. Таблица игр с полем playtime
cur.execute("""
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    genre TEXT NOT NULL,
    year INTEGER NOT NULL,
    description TEXT NOT NULL,
    cover TEXT,
    playtime INTEGER  -- новое поле: время прохождения в часах
)
""")
print("✅ Таблица 'games' создана")

# 2. Таблица треков
cur.execute("""
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    file TEXT NOT NULL,
    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE
)
""")
print("✅ Таблица 'tracks' создана")

# 3. Таблица заметок с изображениями
cur.execute("""
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    text TEXT NOT NULL,
    image TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE
)
""")
print("✅ Таблица 'reviews' создана")

# Добавляем пример игры с временем прохождения
print("🔄 Добавляю примеры данных...")
cur.execute("""
INSERT INTO games (title, genre, year, description, playtime)
VALUES ('Undertale', 'RPG', 2015, 'Инди-RPG с сильным сюжетом', 8)
""")

cur.execute("""
INSERT INTO tracks (game_id, name, file)
VALUES (1, 'Megalovania', 'megalovania.mp3')
""")

cur.execute("""
INSERT INTO reviews (game_id, rating, text)
VALUES 
    (1, 5, 'Невероятная игра! Музыка просто потрясающая. Megalovania - лучший трек.'),
    (1, 4, 'Очень атмосферно. OST добавляет много эмоций к игре.')
""")

conn.commit()
conn.close()
print("🎉 База данных успешно создана!")
print("📊 Структура:")
print("   - Таблица 'games' с полем 'playtime'")
print("   - Таблица 'tracks'")
print("   - Таблица 'reviews' с полем 'image'")