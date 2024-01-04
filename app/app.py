from flask import Flask, jsonify, request, make_response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import datetime
import requests
from contextlib import contextmanager
from config import config as cfg 

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = cfg['flask_secret_key']

TMDB_API_KEY = cfg["tmdb_key"]

# JWT Manager initialization
jwt = JWTManager(app) 

# Database connection configuration
db_config = {
    'user': cfg['db_user'],  
    'password': cfg['db_password'],  
    'host': 'localhost',
    'database': 'movies_db'  
}

@contextmanager
def get_db_connection():
    connection = mysql.connector.connect(**db_config)
    try:
        yield connection
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        raise
    finally:
        connection.close()

# Function to search movies from TMDB API
def search_movies(query):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(search_url)

    if response.status_code == 200:
        search_results = response.json()['results']
        return [{'title': movie['title'],
                 'year': movie['release_date'].split('-')[0] if movie['release_date'] else 'N/A',
                 'description': movie['overview']} for movie in search_results]
    else:
        return None

# User model
class User(object):
    def __init__(self, user_id, username, password_hash):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def find_by_username(username):
        db = get_db_connection()
        cursor = db.cursor()
        query = "SELECT user_id, username, password_hash FROM Users WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row:
            user = User(*row)
        else:
            user = None
        cursor.close()
        db.close()
        return user

    @staticmethod
    def find_by_id(user_id):
        db = get_db_connection()
        cursor = db.cursor()
        query = "SELECT user_id, username, password_hash FROM Users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        if row:
            user = User(*row)
        else:
            user = None
        cursor.close()
        db.close()
        return user

# Authentication handler
def authenticate(username, password):
    user = User.find_by_username(username)
    if user and check_password_hash(user.password_hash, password):
        return user

# Identity handler
def identity(payload):
    user_id = payload['identity']
    return User.find_by_id(user_id)

# User registration endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    hashed_password = generate_password_hash(password)

    with get_db_connection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM Users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"message": "Username already exists"}), 400
        cursor.execute("INSERT INTO Users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
        db.commit()

    return jsonify({"message": "User registered successfully."}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    user = User.find_by_username(username)
    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Bad username or password"}), 401

# Protected route example
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# Flask route to handle movie search
@app.route('/search')
def search():
    query = request.args.get('query')
    if query:
        movies = search_movies(query)
        return jsonify(movies) if movies else jsonify({"message": "No movies found"}), 404
    return jsonify({"message": "Missing query parameter"}), 400

@app.route('/add_recommendation', methods=['POST'])
@jwt_required()
def add_recommendation():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    movie_id = data.get('movie_id')
    comment = data.get('comment', '')

    # Insert the recommendation into the Recommendations table
    # Also, increment the recommendation_count in the Movies table

    # Continue from the previous code snippet
    db = get_db_connection()
    cursor = db.cursor()
    try:
        # Insert recommendation
        insert_query = "INSERT INTO Recommendations (user_id, movie_id, comment) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (current_user_id, movie_id, comment))

        # Update movie recommendation count
        update_query = "UPDATE Movies SET recommendation_count = recommendation_count + 1 WHERE movie_id = %s"
        cursor.execute(update_query, (movie_id,))

        db.commit()
        return jsonify({"message": "Recommendation added successfully"}), 201
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": "An error occurred", "error": str(err)}), 500
    finally:
        cursor.close()
        db.close()

# Index route
@app.route('/')
def index():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(debug=True)
    


