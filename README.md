# Photo Slideshow App

A Flask-based web application that allows users to upload photos and convert them into video slideshows with background music and customizable settings.

## Features

- **User Authentication**: Secure registration and login system with bcrypt password hashing
- **Photo Upload**: Drag-and-drop interface supporting multiple image formats (JPG, PNG)
- **Video Creation**: Convert photos into MP4 videos using MoviePy
- **Background Music**: Choose from pre-loaded audio tracks or upload custom music
- **Customization Options**: 
  - Set duration per image (1-5 seconds)
  - Select background music
  - Choose image order
- **Gallery Management**: View, select, and delete uploaded photos
- **Admin Dashboard**: User management and system statistics
- **Responsive Design**: Mobile-friendly interface with modern styling

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL (CockroachDB)
- **Video Processing**: MoviePy, ImageIO
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: bcrypt, Flask sessions
- **Styling**: Custom CSS with responsive design

## Prerequisites

- Python 3.8+
- PostgreSQL database

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd photo-slideshow-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file with your database credentials:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/photo_slideshow
   SECRET_KEY=your-secret-key-here
   ```

5. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE photo_slideshow;
   ```

## Running the Application

1. **Start the Flask server**
   ```bash
   python3 app.py
   ```

2. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## Usage

### For Users

1. **Register/Login**: Create an account or sign in
2. **Upload Photos**: Use the drag-and-drop interface to upload images
3. **Create Slideshow**: 
   - Go to Gallery
   - Select photos for your slideshow
   - Choose background music and timing
   - Click "Create Video"
4. **Download**: Once processing is complete, download your MP4 video

### For Administrators

1. **Access Admin Panel**: Login with admin credentials
2. **User Management**: View all registered users
3. **System Statistics**: Monitor photo uploads and user activity

## Project Structure

```
photo-slideshow-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Landing page
│   ├── auth.html         # Login/register
│   ├── dashboard.html    # User dashboard
│   ├── upload.html       # Photo upload
│   ├── gallery.html      # Photo gallery
│   ├── video.html        # Video player
│   └── admin.html        # Admin panel
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   ├── js/
│   │   ├── main.js       # General utilities
│   │   ├── upload.js     # Upload functionality
│   │   └── gallery.js    # Gallery management
│   ├── audio/            # Background music files
│   │   ├── default.mp3
│   │   ├── max.mp3
│   └── videos/           # Generated slideshow videos
```

## Database Schema

The application automatically creates the following tables:

### Users Table
- `id` (SERIAL PRIMARY KEY)
- `name` (VARCHAR(40))
- `email` (VARCHAR(255) UNIQUE)
- `password` (VARCHAR(255)) - bcrypt hashed
- `created_at` (TIMESTAMP)

### Photos Table
- `id` (SERIAL PRIMARY KEY)
- `username` (VARCHAR(255))
- `photo_name` (VARCHAR(255))
- `photo` (BYTEA) - binary image data
- `photo_dimensions` (VARCHAR(255))
- `created_at` (TIMESTAMP)

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Flask session secret key
- `FFMPEG_PATH`: Path to FFmpeg binary (optional)

### Video Settings

- **Resolution**: 1920x1080 (configurable in `app.py`)
- **Frame Rate**: 24 fps
- **Codec**: H.264 (libx264)
- **Audio Codec**: AAC

## API Endpoints

- `GET /` - Landing page
- `GET/POST /login` - User authentication
- `GET/POST /register` - User registration
- `GET /dashboard` - User dashboard
- `GET/POST /upload` - Photo upload
- `GET /gallery` - Photo gallery
- `POST /create_video` - Video generation
- `GET /video/<filename>` - Video player
- `POST /delete_image/<id>` - Delete photo
- `GET /admin` - Admin panel
- `GET /logout` - User logout

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Ensure database exists

2. **Video Generation Fails**
   - Install FFmpeg
   - Check file permissions in static/videos/
   - Verify image formats are supported

3. **Upload Issues**
   - Check file size limits
   - Verify image formats (JPG, PNG)
   - Ensure proper permissions

## Logs

Check Flask console output for detailed error messages and debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request