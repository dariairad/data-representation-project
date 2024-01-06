from flask import Flask, jsonify, request, make_response, render_template, redirect, url_for
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

def search_movies(query, page=1):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(search_url)

    if response.status_code == 200:
        search_results = response.json()['results']
        return [{
            'movie_id': movie['id'],
            'title': movie['title'],
            'year': movie['release_date'].split('-')[0] if movie['release_date'] else 'N/A',
            'description': movie['overview'],
        } for movie in search_results]
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
        with get_db_connection() as db:
            cursor = db.cursor()
            query = "SELECT user_id, username, password_hash FROM Users WHERE username = %s"
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            if row:
                user = User(*row)
            else:
                user = None
            cursor.close()
        return user
    
    @staticmethod
    def find_by_id(user_id):
        with get_db_connection() as db:
            cursor = db.cursor()
            query = "SELECT user_id, username, password_hash FROM Users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            if row:
                user = User(*row)
            else:
                user = None
            cursor.close()
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

@app.route('/auth')
def auth_page():
    return render_template('auth.html')

# User registration endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    hashed_password = generate_password_hash(password)

    with get_db_connection() as db:
        cursor = db.cursor()
        try:
            # Check if user already exists
            cursor.execute("SELECT * FROM Users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({"message": "Username already exists"}), 400

            # Insert new user
            cursor.execute("INSERT INTO Users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
            db.commit()
            return jsonify({'message': 'Registration successful'}), 200

        except Exception as e:
            # Handle any exceptions that occur during database operations
            return jsonify({'message': 'Registration failed', 'error': str(e)}), 500
        finally:
            cursor.close()

    # Redirect to the auth page after successful registration
    return redirect(url_for('auth_page'))

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    user = User.find_by_username(username)
    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=user.user_id)
        # Return the access token to the client
        return jsonify(access_token=access_token), 200
    else:
        # Return an error message to the client
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
    page = request.args.get('page', 1, type=int)
    if query:
        movies = search_movies(query, page)
        return jsonify(movies)
    return jsonify({"message": "No movies found"}), 404

def get_movie_details(movie_id):
    """Fetch movie details from TMDB API based on movie_id."""
    base_url = "https://api.themoviedb.org/3/movie/"
    api_key = TMDB_API_KEY  
    url = f"{base_url}{movie_id}?api_key={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        movie_data = response.json()
        return {
            'title': movie_data.get('title'),
            'release_date': movie_data.get('release_date'),
            'description': movie_data.get('overview'),
        }
    else:
        # Handle errors or return None if the API call fails
        print(f"Failed to retrieve movie details: {response.status_code}")
        return None

@app.route('/add_recommendation', methods=['POST'])
@jwt_required()
def add_recommendation():
    user_id = get_jwt_identity()
    movie_id = request.json.get('movie_id')

    with get_db_connection() as db:
        cursor = db.cursor()
        try:
            # Check if the movie exists in the Movies table
            cursor.execute("SELECT movie_id FROM Movies WHERE movie_id = %s", (movie_id,))
            movie_exists = cursor.fetchone()

            if not movie_exists:
                # Fetch and insert movie details if the movie doesn't exist
                movie_details = get_movie_details(movie_id)
                if movie_details:
                    cursor.execute("INSERT INTO Movies (movie_id, title, release_date, description, recommendation_count) VALUES (%s, %s, %s, %s, 1)",
                                   (movie_id, movie_details['title'], movie_details['release_date'], movie_details['description']))
                else:
                    return jsonify({"message": "Failed to fetch movie details"}), 400
            else:
                # Increment recommendation count if the movie already exists
                cursor.execute("UPDATE Movies SET recommendation_count = recommendation_count + 1 WHERE movie_id = %s", (movie_id,))

            # Insert recommendation
            cursor.execute("INSERT INTO Recommendations (user_id, movie_id) VALUES (%s, %s)", (user_id, movie_id))
            db.commit()
            return jsonify({"message": "Recommendation added successfully"}), 201

        except mysql.connector.Error as err:
            db.rollback()
            return jsonify({"message": "An error occurred", "error": str(err)}), 500
        finally:
            cursor.close()


@app.route('/recommended_movies')
def recommended_movies():
    with get_db_connection() as db:
        cursor = db.cursor()
        query = """
        SELECT movie_id, title, recommendation_count, description
        FROM Movies
        ORDER BY recommendation_count DESC
        """
        cursor.execute(query)
        movies = [{"movie_id": row[0], "title": row[1], "recommendation_count": row[2], "description": row[3]} for row in cursor.fetchall()]
        cursor.close()
    return jsonify(movies)

# Index route
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
    


