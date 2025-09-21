from flask import Flask, flash, request, render_template, url_for, redirect, session
import bcrypt
import imageio
from io import BytesIO
import base64
import moviepy.editor as mpy
import time
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
load_dotenv()
import math
from contextlib import contextmanager

app = Flask(__name__, static_folder='./static')
app.secret_key = os.environ.get('SECRET_KEY')

# DB connection string (put in env var in production)
DB_URL = os.environ.get('DATABASE_URL')

SCREEN_SIZE = (1920, 1080)  # (width, height)

def connect_to_database():
    """Return a new connection. Caller must close or use contextmanager below."""
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)

@contextmanager
def get_cursor(commit=False):
    """
    Context manager to get a cursor and auto-handle connection close/reconnect.
    Use: with get_cursor(commit=True) as cur: cur.execute(...)
    """
    conn = None
    try:
        conn = connect_to_database()
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        # re-raise so caller can decide to flash/log
        raise
    finally:
        if conn:
            conn.close()

def ensure_tables_exist():
    # Use consistent table names: users, photos
    create_users = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(40) NOT NULL,
        email VARCHAR(255) UNIQUE,
        password VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    create_photos = """
    CREATE TABLE IF NOT EXISTS photos (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        photo_name VARCHAR(255),
        photo BYTEA,
        photo_dimensions VARCHAR(255),
        created_at TIMESTAMPTZ DEFAULT now()
    )
    """
    create_videos = """
    CREATE TABLE IF NOT EXISTS videos (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        filename VARCHAR(255) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT now()
    )
    """
    try:
        with get_cursor(commit=True) as cur:
            # Create tables if they don't exist
            cur.execute(create_users)
            cur.execute(create_photos)
            cur.execute(create_videos)

            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='photos' AND column_name='created_at';
            """)
            if cur.fetchone() is None:
                app.logger.info("Adding missing created_at column to photos table")
                cur.execute("""
                    ALTER TABLE photos
                    ADD COLUMN created_at TIMESTAMPTZ DEFAULT now();
                """)
    except Exception as e:
        app.logger.error("Failed to ensure tables exist or update schema: %s", e)
        raise

ensure_tables_exist()

class User:
    def __init__(self, id_, name, email, password_hash):
        self.id = id_
        self.name = name
        self.email = email
        self.password_hash = password_hash

    def check_password(self, password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False

def get_user_by_email(email):
    """Return User or None."""
    if not email:
        return None
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name, email, password FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if row:
                return User(row['id'], row['name'], row['email'], row['password'])
    except Exception as e:
        app.logger.error("DB error in get_user_by_email: %s", e)
    return None

def clipGenerator(base64_string, screen_size, clip_duration):
    """
    Convert a single base64 dataURI or raw base64 string into a moviepy ImageClip.
    base64_string can be: "data:image/png;base64,AAAA..." or plain base64.
    Returns an ImageClip with correct sizing.
    """
    # Normalize: strip data URI prefix if present
    if base64_string is None:
        raise ValueError("Empty base64 string provided")

    if ';base64,' in base64_string:
        base64_string = base64_string.split(';base64,', 1)[1]

    try:
        raw = base64.b64decode(base64_string)
    except Exception as e:
        raise ValueError(f"Base64 decode failed: {e}")

    # read image into numpy array using imageio (use BytesIO)
    try:
        img = imageio.imread(BytesIO(raw))
    except Exception as e:
        raise ValueError(f"Failed to read image bytes: {e}")

    # moviepy wants (w,h) size; we will resize to match screen width while preserving aspect
    clip = mpy.ImageClip(img)
    clip = clip.set_position(('center', 'center')).resize(width=screen_size[0])
    clip = clip.set_duration(clip_duration)
    return clip

def VideoCreator(audio_filename, vdl_links, duration_per_image=3):
    """
    vdl_links: a string with base64 images separated by "$" and ending with "$" or not.
    audio_filename: stored under static/audio/<audio_filename>
    Returns True on success, raises on failure.
    """
    # parse input
    if not vdl_links:
        raise ValueError("No image links provided")

    input_items = [s for s in vdl_links.split("$") if s.strip()]
    if not input_items:
        raise ValueError("No valid image items after splitting")

    audio_path = os.path.join("static", "audio", audio_filename)
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # prepare clips
    clips = []
    clip_duration = duration_per_image
    for item in input_items:
        clip = clipGenerator(item, SCREEN_SIZE, clip_duration)
        clips.append(clip)

    # concatenate
    finalclip = mpy.concatenate_videoclips(clips, method="compose")

    # audio repeat / trim to video length
    audio_clip = mpy.AudioFileClip(audio_path)
    video_duration = clip_duration * len(input_items)
    audio_duration = audio_clip.duration if audio_clip else 0.0

    if audio_duration <= 0:
        # set no audio
        finalclip = finalclip.set_audio(None)
    else:
        repeat_count = math.ceil(video_duration / audio_duration)
        repeated_audio_clip = mpy.concatenate_audioclips([audio_clip] * repeat_count)
        repeated_audio_clip = repeated_audio_clip.subclip(0, video_duration)
        finalclip = finalclip.set_audio(repeated_audio_clip)

    # write: ensure output dir exists
    output_dir = os.path.join("static", "videos")
    os.makedirs(output_dir, exist_ok=True)
    # Use timestamp for unique filename
    timestamp = int(time.time())
    output_path = os.path.join(output_dir, f"slideshow_{timestamp}.mp4")

    # write with error handling
    try:
        # fps kept low to reduce processing time; adjust as needed
        finalclip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    except Exception as e:
        app.logger.error("Failed to write video file: %s", e)
        raise

    return f"slideshow_{timestamp}.mp4"

@app.route('/')
def index():
    user_logged_in = 'mail' in session
    return render_template('index.html', user_logged_in=user_logged_in)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'mail' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = (request.form.get('email') or "").strip().lower()
        password = request.form.get('password') or ""

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return redirect(url_for('login'))

        try:
            user = get_user_by_email(email)
            if not user:
                flash('User not found. Please register.', 'warning')
                return redirect(url_for('login'))

            if not user.check_password(password):
                flash('Invalid email or password. Please try again.', 'error')
                return redirect(url_for('login'))

            session['mail'] = email
            flash("Logged in successfully.", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.exception("Login error")
            flash("Internal error during login. Try again.", "error")
            return redirect(url_for('login'))

    return render_template('auth.html', mode='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = (request.form.get('name') or "").strip()
        email = (request.form.get('email') or "").strip().lower()
        password = request.form.get('password') or ""

        if not name or not email or not password:
            flash("Please provide name, email and password.", "error")
            return redirect(url_for('register'))

        try:
            with get_cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    flash('A user with this email already exists. Please log in or use a different email.', 'warning')
                    return redirect(url_for('register'))

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            with get_cursor(commit=True) as cur:
                cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))

            session['mail'] = email
            flash("Registration successful! You are now logged in.", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.exception("Registration failed")
            flash("An internal error occurred while registering. Please try again.", "error")
            return redirect(url_for('register'))

    return render_template('auth.html', mode='register')

@app.route('/dashboard')
def dashboard():
    email = session.get('mail')
    if not email:
        flash("Please login to access the dashboard.", "warning")
        return redirect(url_for('login'))

    user = get_user_by_email(email)
    if not user:
        session.pop('mail', None)
        flash("Session expired or user no longer exists. Please log in again.", "error")
        return redirect(url_for('login'))

    # Get user's photos and videos count
    try:
        with get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM photos WHERE username = %s", (email,))
            photo_count = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) as count FROM videos WHERE username = %s", (email,))
            video_count = cur.fetchone()['count']
    except Exception:
        photo_count = 0
        video_count = 0

    return render_template('dashboard.html', user={'id': user.id, 'name': user.name, 'email': user.email}, photo_count=photo_count, video_count=video_count)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == "POST":
        data = request.form.get('data')  # expected to be "$"-joined base64 items
        if not data:
            flash("No image data received.", "error")
            return redirect(url_for("upload"))

        # split items and keep non-empty
        links = [s for s in data.split("$") if s.strip()]
        if not links:
            flash("No valid images found in submitted data.", "error")
            return redirect(url_for("upload"))

        username = session.get('mail')
        if not username:
            flash("Please login before uploading images.", "error")
            return redirect(url_for('login'))

        try:
            with get_cursor(commit=True) as cur:
                for b64 in links:
                    # normalize and decode base64; store as BYTEA
                    if ';base64,' in b64:
                        b64 = b64.split(';base64,', 1)[1]
                    try:
                        blob = base64.b64decode(b64)
                    except Exception:
                        app.logger.warning("Skipping invalid base64 item for user %s", username)
                        continue
                    photo_name = "uploaded_image"
                    photo_dimensions = "default"
                    cur.execute("INSERT INTO photos (username, photo_name, photo, photo_dimensions) VALUES (%s, %s, %s, %s)",
                                (username, photo_name, psycopg2.Binary(blob), photo_dimensions))
            flash("Images uploaded successfully.", "success")
            return redirect(url_for("gallery"))
        except Exception as e:
            app.logger.exception("Failed to save images")
            flash("Failed to save images. Try again.", "error")
            return redirect(url_for("upload"))

    return render_template('upload.html')

@app.route('/gallery')
def gallery():
    username = session.get('mail')
    if not username:
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login'))

    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, photo FROM photos WHERE username = %s ORDER BY created_at DESC", (username,))
            rows = cur.fetchall()
        
        # convert each row's bytea to base64 data URI
        images = []
        for r in rows:
            blob = r['photo']
            if blob is None:
                continue
            b64 = base64.b64encode(blob).decode('utf-8')
            data_uri = f"data:image/png;base64,{b64}"
            images.append({'id': r['id'], 'data_uri': data_uri})
        
        return render_template('gallery.html', images=images)
    except Exception as e:
        app.logger.exception("Failed to fetch photos for gallery")
        flash("Failed to load photos. Try again.", "error")
        return redirect(url_for('dashboard'))

@app.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    username = session.get('mail')
    if not username:
        flash('Please login to delete images.', 'error')
        return redirect(url_for('login'))
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM photos WHERE id = %s AND username = %s", (image_id, username))
        flash('Image deleted successfully.', 'success')
    except Exception as e:
        app.logger.exception("Failed to delete image")
        flash('Failed to delete image.', 'error')
    return redirect(url_for('gallery'))

@app.route('/create_video', methods=['POST'])
def create_video():
    username = session.get('mail')
    if not username:
        flash('Please login to create videos.', 'error')
        return redirect(url_for('login'))

    selected_images = request.form.getlist('selected_images')
    audio_file = request.form.get('audio_file', 'default.mp3')
    duration = int(request.form.get('duration', 3))

    if not selected_images:
        flash('Please select at least one image.', 'error')
        return redirect(url_for('gallery'))

    try:
        # Get selected images from database
        with get_cursor() as cur:
            placeholders = ','.join(['%s'] * len(selected_images))
            cur.execute(f"SELECT photo FROM photos WHERE id IN ({placeholders}) AND username = %s ORDER BY id", 
                       selected_images + [username])
            rows = cur.fetchall()

        # Convert to base64 string
        image_data = []
        for r in rows:
            blob = r['photo']
            if blob:
                b64 = base64.b64encode(blob).decode('utf-8')
                image_data.append(f"data:image/png;base64,{b64}")

        if not image_data:
            flash('No valid images found.', 'error')
            return redirect(url_for('gallery'))

        # Create video
        image_string = "$".join(image_data)
        video_filename = VideoCreator(audio_file, image_string, duration)
        # Record video creation in DB
        with get_cursor(commit=True) as cur:
            cur.execute("INSERT INTO videos (username, filename) VALUES (%s, %s)", (username, video_filename))
        flash('Video created successfully!', 'success')
        return redirect(url_for('video_player', filename=video_filename))
    except Exception as e:
        app.logger.exception("Failed to create video")
        flash('Failed to create video. Please try again.', 'error')
        return redirect(url_for('gallery'))

@app.route('/video/<filename>')
def video_player(filename):
    return render_template('video.html', video_filename=filename)

@app.route('/admin')
def admin():
    email = session.get('mail')
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    if not email or email != ADMIN_EMAIL:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name, email, created_at FROM users ORDER BY created_at DESC")
            users = cur.fetchall()
            cur.execute("SELECT COUNT(*) as count FROM users")
            user_count = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) as count FROM photos")
            photo_count = cur.fetchone()['count']
    except Exception as e:
        app.logger.exception("Failed to fetch admin data")
        users = []
        user_count = 0
        photo_count = 0

    return render_template('admin.html', users=users, user_count=user_count, photo_count=photo_count)

@app.route('/logout')
def logout():
    session.pop('mail', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('index'))

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
