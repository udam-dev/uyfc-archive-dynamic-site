# Flask Blog with Admin Dashboard

This is a Flask application with MongoDB database for a blog site with an admin dashboard.

## Setup

1. Install dependencies:
   pip install -r requirements.txt

2. Move static assets:
   - Ensure `css/`, `JavaScript/`, `images/` are inside `static/` folder.

3. Run the app:
   python app.py

4. Access:
   - Home: http://localhost:5000/
   - Admin: http://localhost:5000/admin

## Features

- Dynamic blog posts from MongoDB database.
- Admin dashboard to add/delete posts with image upload.
- Glassmorphism UI.

## Database

- MongoDB: `database.db`
- Table: posts (id, title, content, image BLOB, image_filename TEXT, date_posted TEXT)
