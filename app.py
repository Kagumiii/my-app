import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, g, request, redirect, url_for
import sqlite3
from color_utils import get_dominant_color, get_color_scheme, rgb_to_hex
import json

app = Flask(__name__)
DATABASE = "database.db"

UPLOAD_FOLDER = "static/audio"
ALLOWED_EXTENSIONS = {"mp3"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

COVER_FOLDER = "static/covers"
ALLOWED_COVERS = {"png", "jpg", "jpeg"}

app.config["COVER_FOLDER"] = COVER_FOLDER

if not os.path.exists(COVER_FOLDER):
    os.makedirs(COVER_FOLDER)

def allowed_cover(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_COVERS

# Добавьте в app.py после создания папок для covers
REVIEWS_IMAGE_FOLDER = "static/review_images"
app.config["REVIEWS_IMAGE_FOLDER"] = REVIEWS_IMAGE_FOLDER

if not os.path.exists(REVIEWS_IMAGE_FOLDER):
    os.makedirs(REVIEWS_IMAGE_FOLDER)

ALLOWED_REVIEW_IMAGES = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_review_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_REVIEW_IMAGES


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.route("/add_game", methods=["GET", "POST"])
def add_game():
    if request.method == "POST":
        # Получаем данные из формы
        title = request.form["title"]
        genre = request.form["genre"]
        year = request.form["year"]
        description = request.form["description"]
        playtime = request.form.get("playtime", "")

        # Конвертируем playtime в число или NULL
        try:
            playtime_value = int(playtime) if playtime and playtime.strip() else None
        except ValueError:
            playtime_value = None

        # Обработка обложки - ВАЖНО: определяем переменную здесь
        cover_file = request.files["cover"]
        cover_filename = None  # ИНИЦИАЛИЗИРУЕМ как None

        if cover_file and cover_file.filename != "" and allowed_cover(cover_file.filename):
            cover_filename = secure_filename(cover_file.filename)
            cover_path = os.path.join(app.config["COVER_FOLDER"], cover_filename)
            cover_file.save(cover_path)
        else:
            # Если файл не загружен или невалидный, оставляем cover_filename как None
            cover_filename = None

        # Добавляем игру в базу
        db = get_db()
        db.execute(
            """
            INSERT INTO games (title, genre, year, description, cover, playtime)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, genre, year, description, cover_filename, playtime_value)
        )
        db.commit()

        return redirect(url_for("index"))

    return render_template("add_game.html")


@app.route("/add_track/<int:game_id>", methods=["POST"])
def add_track(game_id):


    name = request.form["name"]
    file = request.files["file"]

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        db = get_db()
        db.execute(
            "INSERT INTO tracks (game_id, name, file) VALUES (?, ?, ?)",
            (game_id, name, filename)
        )
        db.commit()

    return redirect(url_for("game", game_id=game_id))


@app.route("/edit_game/<int:game_id>", methods=["GET", "POST"])
def edit_game(game_id):
    db = get_db()
    game = db.execute(
        "SELECT * FROM games WHERE id = ?",
        (game_id,)
    ).fetchone()

    if request.method == "POST":
        title = request.form["title"]
        genre = request.form["genre"]
        year = request.form["year"]
        description = request.form["description"]
        playtime = request.form.get("playtime", "")

        # Конвертируем playtime
        try:
            playtime_value = int(playtime) if playtime and playtime.strip() else None
        except ValueError:
            playtime_value = None

        # Начинаем с текущей обложки
        cover_filename = game["cover"]

        # Обработка новой обложки
        cover_file = request.files["cover"]

        if cover_file and cover_file.filename != "" and allowed_cover(cover_file.filename):
            # Удаляем старую обложку если она есть
            if game["cover"]:
                old_path = os.path.join(app.config["COVER_FOLDER"], game["cover"])
                if os.path.exists(old_path):
                    os.remove(old_path)

            # Сохраняем новую
            cover_filename = secure_filename(cover_file.filename)
            cover_path = os.path.join(app.config["COVER_FOLDER"], cover_filename)
            cover_file.save(cover_path)

        # Обновляем игру
        db.execute("""
            UPDATE games
            SET title=?, genre=?, year=?, description=?, cover=?, playtime=?
            WHERE id=?
        """, (title, genre, year, description, cover_filename, playtime_value, game_id))
        db.commit()

        return redirect(url_for("game", game_id=game_id))

    # Получаем треки
    tracks = db.execute(
        "SELECT * FROM tracks WHERE game_id = ?",
        (game_id,)
    ).fetchall()

    return render_template(
        "edit_game.html",
        game=game,
        tracks=tracks
    )


@app.teardown_appcontext
def close_db(error):
    if "db" in g:
        g.db.close()


@app.route("/")
def index():
    db = get_db()
    games = db.execute("SELECT * FROM games").fetchall()

    # Получаем цвета для всех игр
    games_with_colors = []
    for game in games:
        game_dict = dict(game)
        color_scheme = None

        if game["cover"]:
            try:
                cover_path = os.path.join(app.config["COVER_FOLDER"], game["cover"])
                if os.path.exists(cover_path):
                    dominant_color = get_dominant_color(cover_path)
                    color_scheme = get_color_scheme(dominant_color)
            except Exception as e:
                print(f"Ошибка при получении цвета для игры {game['id']}: {e}")

        game_dict['color_scheme'] = color_scheme
        games_with_colors.append(game_dict)

    return render_template("index.html", games=games_with_colors)

@app.route("/game/<int:game_id>")
def game(game_id):
    db = get_db()
    game = db.execute(
        "SELECT * FROM games WHERE id = ?", (game_id,)
    ).fetchone()

    tracks = db.execute(
        "SELECT * FROM tracks WHERE game_id = ?", (game_id,)
    ).fetchall()

    reviews = db.execute(
        """
        SELECT * FROM reviews 
        WHERE game_id = ? 
        ORDER BY created_at DESC
        """,
        (game_id,)
    ).fetchall()

    avg_rating = db.execute(
        """
        SELECT AVG(rating) as avg_rating 
        FROM reviews 
        WHERE game_id = ?
        """,
        (game_id,)
    ).fetchone()["avg_rating"]

    avg_rating = round(avg_rating, 1) if avg_rating else 0

    # Получаем цветовую схему из обложки
    color_scheme = None
    if game["cover"]:
        try:
            cover_path = os.path.join(app.config["COVER_FOLDER"], game["cover"])
            if os.path.exists(cover_path):
                dominant_color = get_dominant_color(cover_path)
                color_scheme = get_color_scheme(dominant_color)
        except Exception as e:
            print(f"Ошибка при получении цветовой схемы: {e}")

    return render_template(
        "game.html",
        game=game,
        tracks=tracks,
        reviews=reviews,
        avg_rating=avg_rating,
        color_scheme=color_scheme
    )
@app.route("/delete_game/<int:game_id>", methods=["POST"])
def delete_game(game_id):


    db = get_db()
    db.execute("DELETE FROM tracks WHERE game_id = ?", (game_id,))
    db.execute("DELETE FROM games WHERE id = ?", (game_id,))
    db.commit()
    return redirect(url_for("index"))


@app.route("/delete_track/<int:track_id>/<int:game_id>", methods=["POST"])
def delete_track(track_id, game_id):
    db = get_db()

    # Сначала получим информацию о треке для удаления файла
    track = db.execute(
        "SELECT * FROM tracks WHERE id = ?",
        (track_id,)
    ).fetchone()

    if track:
        # Удаляем файл из файловой системы
        try:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], track["file"])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Ошибка при удалении файла: {e}")

    # Удаляем запись из базы данных
    db.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    db.commit()

    return redirect(url_for("game", game_id=game_id))

@app.route("/search")
def search():
    q = request.args.get("q", "")
    db = get_db()
    games = db.execute(
        "SELECT * FROM games WHERE title LIKE ?",
        (f"%{q}%",)
    ).fetchall()
    return render_template("index.html", games=games)


@app.route("/add_review/<int:game_id>", methods=["POST"])
def add_review(game_id):
    rating = int(request.form["rating"])
    text = request.form["text"]

    db = get_db()

    # Обработка изображения (необязательно)
    image_file = request.files.get("image")
    image_filename = None

    if image_file and image_file.filename != "" and allowed_review_image(image_file.filename):
        image_filename = secure_filename(image_file.filename)
        # Добавляем префикс с ID игры и временем для уникальности
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"game_{game_id}_{timestamp}_{image_filename}"

        image_path = os.path.join(app.config["REVIEWS_IMAGE_FOLDER"], image_filename)
        image_file.save(image_path)

    db.execute(
        """
        INSERT INTO reviews (game_id, rating, text, image)
        VALUES (?, ?, ?, ?)
        """,
        (game_id, rating, text, image_filename)
    )
    db.commit()

    return redirect(url_for("game", game_id=game_id))


@app.route("/delete_review/<int:review_id>/<int:game_id>", methods=["POST"])
def delete_review(review_id, game_id):
    db = get_db()

    # Сначала получаем информацию о заметке
    review = db.execute(
        "SELECT * FROM reviews WHERE id = ?",
        (review_id,)
    ).fetchone()

    # Удаляем файл изображения если он есть
    if review and review["image"]:
        try:
            file_path = os.path.join(app.config["REVIEWS_IMAGE_FOLDER"], review["image"])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Ошибка при удалении файла: {e}")

    # Удаляем запись из базы данных
    db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    db.commit()

    return redirect(url_for("game", game_id=game_id))

if __name__ == "__main__":
    app.run(debug=True)
