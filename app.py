from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymongo
from bson.binary import Binary
import os
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, ImageOps
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.permanent_session_lifetime = timedelta(minutes=5)

# MongoDB connection setup
MONGO_URI = os.environ.get('MONGO_URI')
MONGO_DB_NAME = os.environ.get('MONGO_DB')

mongo_client = None
db = None

if MONGO_URI:
    try:
        mongo_client = MongoClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=5000, # 5 seconds max timeout
            connectTimeoutMS=5000
        )
        db = mongo_client[MONGO_DB_NAME] # <-- This is where your code was failing
    except Exception as e:
        print(f"Initial MongoDB connection failed: {e}")
else:
    print("WARNING: MONGO_URI environment variable is missing!")

def init_db():
    try:
        # Create indexes
        db.users.create_index("username", unique=True)
        db.posts.create_index("category")
        db.posts.create_index("date_posted")
        db.post_images.create_index("post_id")
    except Exception as e:
        print(f"Error initializing DB indexes: {e}")


# កូដសម្រាប់ពិនិត្យ និងបង្កើត Collection 'counters' ពេល App ចាប់ផ្តើមដំណើរការ
def initialize_counters():
    # ពិនិត្យមើលថាតើមាន Collection ឈ្មោះ 'counters' ឬនៅ
    if "counters" not in db.list_collection_names():
        print("រកមិនឃើញ Collection counters ទេ! កំពុងបង្កើត...")
        
        # នេះជាការបង្កើត Collection និងបញ្ចូលទិន្នន័យដំបូងដើម្បីឲ្យវាដឹងថា id ចាប់ផ្តើមពីលេខ 0
        db["counters"].insert_one({
            "_id": "userid",  # ឈ្មោះ key សម្រាប់ចំណាំ
            "seq": 0         # លេខរៀងដំបូង
        })
        print("បង្កើត Collection counters រួចរាល់!")
    else:
        print("Collection counters មានរួចរាល់ហើយ។")

# រត់ function ខាងលើដើម្បីបង្កើតវាការពារមុន
if MONGO_URI:
    initialize_counters()

# Initialize database indexes
init_db()

# Auto-increment helper
def get_next_sequence_value(sequence_name):
    result = db.counters.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=pymongo.ReturnDocument.AFTER
    )
    return result['sequence_value']

# Helper for image compression
def compress_image(image_file, max_size=(1200, 1200), quality=75):
    img = Image.open(image_file)
    
    # Handle EXIF orientation
    try:
        img = ImageOps.exif_transpose(img)
    except Exception as e:
        print(f"Error handling EXIF orientation: {e}")
        
    # Convert RGBA/LA or Palette with transparency to RGB with white background
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'RGBA':
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img.convert('RGBA'), mask=img.convert('RGBA').split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
        
    # Resize keeping aspect ratio if dimensions exceed maximum
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Compress and save to bytes
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    return output.read()

# Auth Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('សូមចូលគណនីជាមុនសិន! Please log in first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_category_posts(category_name):
    try:
        posts = list(db.posts.find({'category': category_name}).sort('date_posted', -1))
        posts_with_images = []
        for post in posts:
            post['id'] = post['_id']
            images = list(db.post_images.find({'post_id': post['_id']}, {'_id': 1}))
            post['images'] = [img['_id'] for img in images]
            posts_with_images.append(post)
        return posts_with_images
    except Exception as e:
        print(f"Error fetching category posts: {e}")
        return []

# Routes
@app.route('/')
def home():
    try:
        posts = list(db.posts.find().sort('date_posted', -1))
        posts_with_images = []
        for post in posts:
            post['id'] = post['_id']
            images = list(db.post_images.find({'post_id': post['_id']}, {'_id': 1}))
            post['images'] = [img['_id'] for img in images]
            posts_with_images.append(post)
    except Exception as e:
        print(f"Home route error: {e}")
        posts_with_images = []
    return render_template('index.html', posts=posts_with_images)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        user_count = db.users.count_documents({})
    except Exception as e:
        print(f"Database error checking user count: {e}")
        user_count = 0

    if user_count == 0:
        return redirect(url_for('register'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = db.users.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id'] = user['_id']
            session['username'] = user['username']
            session['role'] = user.get('role', 'admin')
            flash('បានចូលគណនីដោយជោគជ័យ! Logged in successfully!')
            return redirect(url_for('admin'))
        else:
            flash('ឈ្មោះអ្នកប្រើ ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវទេ! Invalid username or password!')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        user_count = db.users.count_documents({})
    except Exception as e:
        print(f"Database error checking user count: {e}")
        user_count = 0
    
    if user_count > 0:
        flash('ការចុះឈ្មោះត្រូវបានបិទ! Registration is disabled.')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('សូមបំពេញព័ត៌មានទាំងអស់! Please fill in all fields!')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        
        try:
            user_id = get_next_sequence_value('users')
            db.users.insert_one({
                '_id': user_id,
                'username': username,
                'password': hashed_password,
                'role': 'admin'
            })
            flash('គណនីអ្នកគ្រប់គ្រងត្រូវបានបង្កើត! Admin account created. Please log in.')
            return redirect(url_for('login'))
        except pymongo.errors.DuplicateKeyError:
            flash('ឈ្មោះអ្នកប្រើមានរួចហើយ! Username already exists!')
        except Exception as e:
            flash(f'មានបញ្ហាក្នុងការចុះឈ្មោះ: {e}')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    reason = request.args.get('reason')
    session.clear()
    if reason == 'inactivity':
        flash('លោកអ្នកត្រូវបានចាកចេញដោយសារគ្មានសកម្មភាព! You have been logged out due to inactivity!')
    else:
        flash('បានចាកចេញពីគណនីដោយជោគជ័យ! Logged out successfully!')
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        category = request.form.get('category')
        event_name = request.form.get('event_name')
        caption = request.form.get('caption')
        direct_link = request.form.get('direct_link', '')
        images = request.files.getlist('images')

        date_posted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            post_id = get_next_sequence_value('posts')
            db.posts.insert_one({
                '_id': post_id,
                'category': category,
                'event_name': event_name,
                'caption': caption,
                'direct_link': direct_link,
                'date_posted': date_posted
            })
            
            for image in images:
                if image and image.filename != '':
                    try:
                        image_data = compress_image(image)
                        base, _ = os.path.splitext(image.filename)
                        image_filename = f"{base}.jpg"
                    except Exception as e:
                        print(f"Error compressing image: {e}")
                        image.seek(0)
                        image_data = image.read()
                        image_filename = image.filename
                        
                    image_id = get_next_sequence_value('post_images')
                    db.post_images.insert_one({
                        '_id': image_id,
                        'post_id': post_id,
                        'image': Binary(image_data),
                        'image_filename': image_filename
                    })
                    
            flash('Post added successfully!')
        except Exception as e:
            flash(f'Error adding post: {e}')
            
        return redirect(url_for('admin'))

    posts = list(db.posts.find().sort('date_posted', -1))
    posts_with_images = []
    for post in posts:
        post['id'] = post['_id']
        images = list(db.post_images.find({'post_id': post['_id']}, {'_id': 1, 'image_filename': 1}))
        post['images'] = []
        for img in images:
            img['id'] = img['_id']
            post['images'].append(img)
        posts_with_images.append(post)
        
    users = list(db.users.find().sort('username', 1))
    for user in users:
        user['id'] = user['_id']
        
    return render_template('admin.html', posts=posts_with_images, users=users)

@app.route('/admin/create_user', methods=['POST'])
@login_required
def create_user():
    if session.get('role') != 'admin':
        flash('អ្នកគ្មានសិទ្ធិបង្កើតគណនីទេ! You do not have permission to create accounts!')
        return redirect(url_for('admin'))

    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    
    if not username or not password or not role:
        flash('សូមបំពេញព័ត៌មានទាំងអស់! Please fill in all fields!')
        return redirect(url_for('admin'))
        
    hashed_password = generate_password_hash(password)
    
    try:
        user_id = get_next_sequence_value('users')
        db.users.insert_one({
            '_id': user_id,
            'username': username,
            'password': hashed_password,
            'role': role
        })
        flash(f'គណនី "{username}" ត្រូវបានបង្កើតដោយជោគជ័យ! User "{username}" created successfully!')
    except pymongo.errors.DuplicateKeyError:
        flash('ឈ្មោះអ្នកប្រើមានរួចហើយ! Username already exists!')
    except Exception as e:
        flash(f'មានបញ្ហាក្នុងការបង្កើតគណនី: {e}')
        
    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if session.get('role') != 'admin':
        flash('អ្នកគ្មានសិទ្ធិលុបគណនីទេ! You do not have permission to delete accounts!')
        return redirect(url_for('admin'))

    user_to_delete = db.users.find_one({'_id': user_id})
    
    if not user_to_delete:
        flash('រកមិនឃើញអ្នកប្រើប្រាស់! User not found!')
        return redirect(url_for('admin'))
        
    if user_to_delete['username'] == session.get('username'):
        flash('អ្នកមិនអាចលុបគណនីផ្ទាល់ខ្លួនបានទេ! You cannot delete your own account!')
        return redirect(url_for('admin'))
        
    user_count = db.users.count_documents({})
    if user_count <= 1:
        flash('មិនអាចលុបអ្នកប្រើប្រាស់ចុងក្រោយបានទេ! Cannot delete the last user!')
        return redirect(url_for('admin'))
        
    db.users.delete_one({'_id': user_id})
    flash(f'បានលុបអ្នកប្រើប្រាស់ "{user_to_delete["username"]}" ដោយជោគជ័យ! User "{user_to_delete["username"]}" deleted successfully!')
    return redirect(url_for('admin'))

@app.route('/admin/change_password/<int:user_id>', methods=['POST'])
@login_required
def change_password(user_id):
    if session.get('role') != 'admin':
        flash('អ្នកគ្មានសិទ្ធិផ្លាស់ប្តូរព័ត៌មានគណនីទេ! You do not have permission to modify accounts!')
        return redirect(url_for('admin'))

    new_password = request.form.get('new_password')
    role = request.form.get('role', 'user')
    
    user = db.users.find_one({'_id': user_id})
    if not user:
        flash('រកមិនឃើញអ្នកប្រើប្រាស់! User not found!')
        return redirect(url_for('admin'))

    if user['username'] == session.get('username') and role == 'user':
        flash('អ្នកមិនអាចផ្លាស់ប្តូរសិទ្ធិគណនីផ្ទាល់ខ្លួនបានទេ! You cannot change your own account type!')
        return redirect(url_for('admin'))
        
    if new_password:
        hashed_password = generate_password_hash(new_password)
        db.users.update_one({'_id': user_id}, {'$set': {'password': hashed_password, 'role': role}})
        flash(f'បានកែប្រែគណនី "{user["username"]}" ដោយជោគជ័យ! Account "{user["username"]}" updated successfully!')
    else:
        db.users.update_one({'_id': user_id}, {'$set': {'role': role}})
        flash(f'បានកែប្រែសិទ្ធិគណនី "{user["username"]}" ដោយជោគជ័យ! Account permissions for "{user["username"]}" updated successfully!')

    return redirect(url_for('admin'))

@app.route('/post_image/<int:post_id>')
def get_post_image(post_id):
    img = db.post_images.find_one({'post_id': post_id}, {'_id': 1})
    if img:
        return redirect(url_for('get_image', image_id=img['_id']))
    return '', 404

@app.route('/image/<int:image_id>')
def get_image(image_id):
    img = db.post_images.find_one({'_id': image_id}, {'image': 1})
    if img and img.get('image'):
        return app.response_class(img['image'], mimetype='image/jpeg')
    return '', 404

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = db.posts.find_one({'_id': post_id})
    if not post:
        flash('Post not found!')
        return redirect(url_for('admin'))

    post['id'] = post['_id']

    if request.method == 'POST':
        category = request.form.get('category')
        event_name = request.form.get('event_name')
        caption = request.form.get('caption')
        direct_link = request.form.get('direct_link', '')
        images = request.files.getlist('images')

        try:
            db.posts.update_one({'_id': post_id}, {'$set': {
                'category': category,
                'event_name': event_name,
                'caption': caption,
                'direct_link': direct_link
            }})
            
            for image in images:
                if image and image.filename != '':
                    try:
                        image_data = compress_image(image)
                        base, _ = os.path.splitext(image.filename)
                        image_filename = f"{base}.jpg"
                    except Exception as e:
                        print(f"Error compressing image: {e}")
                        image.seek(0)
                        image_data = image.read()
                        image_filename = image.filename
                        
                    image_id = get_next_sequence_value('post_images')
                    db.post_images.insert_one({
                        '_id': image_id,
                        'post_id': post_id,
                        'image': Binary(image_data),
                        'image_filename': image_filename
                    })
                    
            flash('Post updated successfully!')
        except Exception as e:
            flash(f'Error updating post: {e}')
            
        return redirect(url_for('admin'))

    images = list(db.post_images.find({'post_id': post_id}, {'_id': 1, 'image_filename': 1}))
    post['images'] = []
    for img in images:
        img['id'] = img['_id']
        post['images'].append(img)

    return render_template('edit.html', post=post)

@app.route('/delete_image/<int:image_id>', methods=['GET', 'POST'])
@login_required
def delete_image(image_id):
    img = db.post_images.find_one({'_id': image_id}, {'post_id': 1})
    if img:
        post_id = img['post_id']
        db.post_images.delete_one({'_id': image_id})
        flash('Image deleted successfully!')
        return redirect(url_for('edit_post', post_id=post_id))
    return redirect(url_for('admin'))

@app.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    db.post_images.delete_many({'post_id': post_id})
    db.posts.delete_one({'_id': post_id})
    flash('Post deleted successfully!')
    return redirect(url_for('admin'))

@app.route('/culture')
def culture():
    return render_template('culture.html', posts=get_category_posts('វប្បធម៌'))

@app.route('/history')
def history():
    return render_template('history.html', posts=get_category_posts('ប្រវត្តិសាស្ត្រ'))

@app.route('/sports')
def sports():
    return render_template('sports.html', posts=get_category_posts('កីឡា'))

@app.route('/education')
def education():
    return render_template('education.html', posts=get_category_posts('អប់រំ'))

@app.route('/arts')
def arts():
    return render_template('arts.html', posts=get_category_posts('សិល្បៈ'))

@app.route('/technology')
def technology():
    return render_template('technology.html', posts=get_category_posts('បច្ចេកវិទ្យា'))

@app.route('/foreign-affairs')
def foreign_affairs():
    return render_template('foreign_affairs.html', posts=get_category_posts('កិច្ចការបរទេស'))

@app.route('/agriculture')
def agriculture():
    return render_template('agriculture.html', posts=get_category_posts('កសសិកម្ម'))

@app.route('/national-events')
def national_events():
    return render_template('national_events.html', posts=get_category_posts('រួបរួមស្មារតីជាតិ'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
