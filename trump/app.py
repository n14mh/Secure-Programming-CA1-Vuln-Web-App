import os
import sqlite3
from flask import Flask, render_template, request, Response, redirect, url_for, flash, session, send_from_directory, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


app = Flask(__name__)
app.secret_key = 'trump123'  # Set a secure secret key

# Configure the SQLite database
db_path = os.path.join(os.path.dirname(__file__), 'trump.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Example Model (Table)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Function to run the SQL script if database doesn't exist
def initialize_database():
    if not os.path.exists('trump.db'):
        with sqlite3.connect('trump.db') as conn:
            cursor = conn.cursor()
            with open('trump.sql', 'r') as sql_file:
                sql_script = sql_file.read()
            cursor.executescript(sql_script)
            print("Database initialized with script.")

# Existing routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quotes')
def quotes():
    return render_template('quotes.html')

@app.route('/sitemap')
def sitemap():
    return render_template('sitemap.html')
    
@app.route('/admin_panel')
def admin_panel():
    return render_template('admin_panel.html')

# Route to handle redirects based on the destination query parameter
@app.route('/redirect', methods=['GET'])
def redirect_handler():
    destination = request.args.get('destination')

    if destination:
        return redirect(destination)
    else:
        return "Invalid destination", 400


@app.route('/comments', methods=['GET', 'POST'])
def comments():
    if request.method == 'POST':
        username = request.form['username']
        comment_text = request.form['comment']

        # Insert comment into the database
        insert_comment_query = text("INSERT INTO comments (username, text) VALUES (:username, :text)")
        db.session.execute(insert_comment_query, {'username': username, 'text': comment_text})
        db.session.commit()
        return redirect(url_for('comments'))

    # Retrieve all comments to display
    comments_query = text("SELECT username, text FROM comments")
    comments = db.session.execute(comments_query).fetchall()
    return render_template('comments.html', comments=comments)

@app.route('/download', methods=['GET'])
def download():
    # Get the filename from the query parameter
    file_name = request.args.get('file', '')

    # Set base directory to where your docs folder is located
    base_directory = os.path.join(os.path.dirname(__file__), 'docs')

    # Construct the file path to attempt to read the file
    file_path = os.path.abspath(os.path.join(base_directory, file_name))

    # Ensure that the file path is within the base directory
    #if not file_path.startswith(base_directory):
     #   return "Unauthorized access attempt!", 403

    # Try to open the file securely
    try:
        with open(file_path, 'rb') as f:
            response = Response(f.read(), content_type='application/octet-stream')
            response.headers['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
    except FileNotFoundError:
        return "File not found", 404
    except PermissionError:
        return "Permission denied while accessing the file", 403
        
@app.route('/downloads', methods=['GET'])
def download_page():
    return render_template('download.html')


@app.route('/profile/<int:user_id>', methods=['GET'])
def profile(user_id):
    query_user = text(f"SELECT * FROM users WHERE id = {user_id}")
    user = db.session.execute(query_user).fetchone()

    if user:
        query_cards = text(f"SELECT * FROM carddetail WHERE id = {user_id}")
        cards = db.session.execute(query_cards).fetchall()
        return render_template('profile.html', user=user, cards=cards)
    else:
        return "User not found or unauthorized access.", 403
from flask import request

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    return render_template('search.html', query=query)

@app.route('/forum')
def forum():
    return render_template('forum.html')

# Add login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        query = text(f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'")
        user = db.session.execute(query).fetchone()

        if user:
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('profile', user_id=user.id))
        else:
            error = 'Invalid Credentials. Please try again.'
            return render_template('login.html', error=error)

    return render_template('login.html')





# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user session
    flash('You were successfully logged out', 'success')
    return redirect(url_for('index'))
    
from flask import session


if __name__ == '__main__':
    initialize_database()  # Initialize the database on application startup if it doesn't exist
    with app.app_context():
        db.create_all()  # Create tables based on models if they don't already exist
    app.run(debug=True)
