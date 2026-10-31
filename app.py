from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, timedelta, date
import json  # For storing itinerary data
from init_db import init_db  # Import the function
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import hashlib
from dotenv import dotenv_values, load_dotenv

from functools import wraps
from flask import abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role')
        print(f"admin_required check: session role = {role}")  # Debug print
        if 'username' not in session or role != 'admin':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Initialize the scheduler
scheduler = BackgroundScheduler()
app = Flask(__name__)
app.secret_key = 'your_secret_key'

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'YOUR_GOOGLE_MAPS_API_KEY_HERE')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.6-flash')

# Cache for itineraries
itinerary_cache = {}

def geocode_address(address):
    """
    Geocode an address string to (lat, lon) using Nominatim OpenStreetMap API.
    Returns (lat, lon) tuple or None if failed.
    """
    import requests
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "TripPlannerApp/1.0"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            location = data[0]
            return (float(location['lat']), float(location['lon']))
        else:
            return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None

# Custom Jinja2 filter to convert string to datetime.date
def todatetime(value):
    try:
        if isinstance(value, (datetime, date)):
            return value
        return datetime.strptime(value, '%Y-%m-%d')
    except Exception:
        return value

app.jinja_env.filters['todatetime'] = todatetime

# Add timedelta to Jinja2 environment globals for template use
import re
def strip_html(value):
    """Remove HTML tags from a string."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', value)

app.jinja_env.filters['strip_html'] = strip_html

# Initialize database
init_db()  # Call the function from the separate file

# Add timedelta to Jinja2 environment globals for template use
from datetime import timedelta
app.jinja_env.globals['timedelta']=timedelta

def move_past_trips_to_history(username):
    today = date.today()
    try:
        with sqlite3.connect('users.db', timeout=10) as con:
            cur = con.cursor()
            # Convert today to string in YYYY-MM-DD format for comparison
            today_str = today.strftime('%Y-%m-%d')
            cur.execute("UPDATE trips SET is_present = 0 WHERE username = ? AND is_present = 1 AND end_date < ?", (username, today_str))
            updated_rows = cur.rowcount
            con.commit()
            print(f"move_past_trips_to_history: Updated {updated_rows} trips for user {username} on {today_str}")
    except sqlite3.OperationalError as e:
        print(f"Database locked error in move_past_trips_to_history for user {username}: {e}")

def move_all_past_trips_to_history():
    today = date.today()
    try:
        with sqlite3.connect('users.db', timeout=10) as con:
            cur = con.cursor()
            # Get all usernames with active trips
            cur.execute("SELECT DISTINCT username FROM trips WHERE is_present = 1")
            users = cur.fetchall()
            
            for user in users:
                username = user[0]
                move_past_trips_to_history(username)
    except sqlite3.OperationalError as e:
        print(f"Database locked error in move_all_past_trips_to_history: {e}")

# Add a call to move_all_past_trips_to_history in the main route to ensure trips are moved on user interaction
@app.before_request
def before_request_func():
    if 'username' in session:
        move_past_trips_to_history(session['username'])

# Schedule the job to run daily
scheduler.add_job(move_all_past_trips_to_history, 'interval', days=1)
scheduler.start()

@app.route('/trigger_move_past_trips')
def trigger_move_past_trips():
    if 'username' in session:
        move_all_past_trips_to_history()
        return "Triggered move_all_past_trips_to_history manually."
    else:
        return "User not logged in.", 401

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('users.db') as con:
            cur = con.cursor()
            cur.execute("SELECT username, email, password, role FROM users WHERE username = ?", (username,))
            user = cur.fetchone()
            if user and check_password_hash(user[2], password):
                print(f"Login success for user: {username}, role: {user[3] if len(user) > 3 else 'user'}")  # Debug print
                session['username'] = username
                session['role'] = user[3] if len(user) > 3 else 'user'
                return redirect(url_for('main'))
            else:
                print(f"Login failed for user: {username}")  # Debug print
                flash("Incorrect Username or Password")
                return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('signup'))

        if len(password) < 6:  # Example: Minimum password length
            flash("Password must be at least 6 characters long!")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        with sqlite3.connect('users.db') as con:
            try:
                cur = con.cursor()
                cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                            (username, email, hashed_password))
                con.commit()
                flash("Account created successfully! Please login.")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Username already exists!")
                return redirect(url_for('signup'))
    return render_template('signup.html')

# Additional imports
import sqlite3

def get_user_interests(username):
    with sqlite3.connect('users.db') as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT interest FROM user_interests WHERE username = ?", (username,))
        interests = [row['interest'] for row in cur.fetchall()]
    return interests

def update_user_interests(username, interests):
    with sqlite3.connect('users.db') as con:
        cur = con.cursor()
        # Delete existing interests
        cur.execute("DELETE FROM user_interests WHERE username = ?", (username,))
        # Insert new interests
        for interest in interests:
            cur.execute("INSERT INTO user_interests (username, interest) VALUES (?, ?)", (username, interest))
        con.commit()

@app.route('/update_interests', methods=['POST'])
def update_interests():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    interests = request.form.getlist('interests')
    update_user_interests(username, interests)
    flash("Interests updated successfully.")
    return redirect(url_for('main'))

from collections import Counter

def analyze_feedback_for_recommendations(username, cur):
    # Fetch feedback for user's past trips
    cur.execute('''
        SELECT tf.trip_id, tf.star_rating, tf.enjoyed_most, tf.could_be_better, tf.recommend_friend, tf.issues
        FROM trip_feedback tf
        JOIN trips t ON tf.trip_id = t.id
        WHERE tf.username = ?
    ''', (username,))
    feedbacks = cur.fetchall()

    # Simple heuristic: calculate average star rating per destination
    cur.execute('''
        SELECT t.destination, AVG(tf.star_rating) as avg_rating
        FROM trip_feedback tf
        JOIN trips t ON tf.trip_id = t.id
        WHERE tf.username = ?
        GROUP BY t.destination
    ''', (username,))
    avg_ratings = {row['destination']: row['avg_rating'] for row in cur.fetchall()}

    # Destinations with high average rating (>=4) are preferred
    preferred_destinations = {dest for dest, rating in avg_ratings.items() if rating >= 4}

    return preferred_destinations

@app.route('/main', methods=['GET', 'POST'])
def main():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']

    if request.method == 'POST':
        # Check if updating interests
        if 'interests' in request.form:
            interests = request.form.getlist('interests')
            update_user_interests(username, interests)
            flash("Interests updated successfully.")
            return redirect(url_for('main'))

    # Existing feedback handling
    feedback_text = request.form.get('feedback_text')
    star_rating = request.form.get('star_rating')
    if feedback_text is not None:
        if not feedback_text.strip():
            flash("Feedback cannot be empty.")
            return redirect(url_for('main'))
        if not star_rating:
            flash("Please provide a star rating.")
            return redirect(url_for('main'))
        try:
            with sqlite3.connect('users.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO feedback (username, feedback_text, created_at) VALUES (?, ?, ?)",
                            (username, feedback_text, datetime.now()))
                con.commit()
            flash("Thank you for your feedback!")
            return redirect(url_for('main'))
        except Exception as e:
            print(f"Error saving feedback: {e}")  # Log the specific error
            flash("An error occurred while saving your feedback. Please try again.")
            return redirect(url_for('main'))

    with sqlite3.connect('users.db') as con:
        con.row_factory = sqlite3.Row  # To access columns by name
        cur = con.cursor()

        # Fetch the user's present trips (all)
        cur.execute("SELECT * FROM trips WHERE username = ? AND is_present = 1", (username,))
        present_trips = cur.fetchall()

        # Fetch the user's trip history
        cur.execute("SELECT * FROM trips WHERE username = ? AND is_present = 0 ORDER BY start_date DESC", (username,))
        trip_history = cur.fetchall()

        # Fetch user interests
        cur.execute("SELECT interest FROM user_interests WHERE username = ?", (username,))
        user_interests = [row['interest'] for row in cur.fetchall()]

        # Analyze feedback to get preferred destinations
        preferred_destinations = analyze_feedback_for_recommendations(username, cur)

        # Generate recommendations based on past trips, interests, and feedback
        past_destinations = {trip['destination'] for trip in trip_history}
        popular_destinations = {
            "Paris": {"image": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Paris_Night.jpg", "region": "Europe", "tags": ["culture", "history", "art"]},
            "New York": {"image": "https://upload.wikimedia.org/wikipedia/commons/4/4d/Manhattan_from_the_Top_of_the_Rock.jpg", "region": "North America", "tags": ["city", "shopping", "nightlife"]},
            "Tokyo": {"image": "https://upload.wikimedia.org/wikipedia/commons/1/12/Tokyo_Tower_and_around_Skyscrapers.jpg", "region": "Asia", "tags": ["technology", "culture", "food"]},
            "London": {"image": "https://upload.wikimedia.org/wikipedia/commons/c/cd/London_Montage_L.jpg", "region": "Europe", "tags": ["history", "culture", "theatre"]},
            "Rome": {"image": "https://upload.wikimedia.org/wikipedia/commons/5/5a/Colosseum_in_Rome%2C_Italy_-_April_2007.jpg", "region": "Europe", "tags": ["history", "architecture", "food"]},
            "Barcelona": {"image": "https://upload.wikimedia.org/wikipedia/commons/4/4e/Barcelona_Montage_2014.png", "region": "Europe", "tags": ["beach", "art", "culture"]},
            "Sydney": {"image": "https://upload.wikimedia.org/wikipedia/commons/b/b9/Sydney_Opera_House_-_Dec_2008.jpg", "region": "Australia", "tags": ["beach", "nature", "opera"]},
            "Dubai": {"image": "https://upload.wikimedia.org/wikipedia/commons/9/9c/Dubai_skyline_2020.jpg", "region": "Middle East", "tags": ["luxury", "shopping", "desert"]},
            "Singapore": {"image": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Singapore_Skyline_2019.jpg", "region": "Asia", "tags": ["city", "food", "nature"]},
            "Amsterdam": {"image": "https://upload.wikimedia.org/wikipedia/commons/6/6a/Amsterdam_Canal_Houses.jpg", "region": "Europe", "tags": ["culture", "canals", "art"]}
        }

        # Map user's past destinations to regions
        past_regions = []
        for trip in trip_history:
            dest = trip['destination']
            if dest in popular_destinations:
                past_regions.append(popular_destinations[dest]['region'])

        region_counts = Counter(past_regions)
        most_common_regions = [region for region, count in region_counts.most_common()]

        recommended_destinations = []

        # Recommend destinations based on user interests, feedback, and past trips
        for dest, info in popular_destinations.items():
            if dest not in past_destinations:
                # Prioritize destinations with high feedback ratings
                if dest in preferred_destinations:
                    recommended_destinations.append({"name": dest, "image": info['image'], "reason": "Highly rated based on your feedback"})
                # Check if any user interest matches destination tags
                elif any(interest.lower() in info['tags'] for interest in user_interests):
                    recommended_destinations.append({"name": dest, "image": info['image'], "reason": "Matches your interests"})

        # If no recommendations from interests or feedback, fallback to region-based recommendations
        if not recommended_destinations:
            if most_common_regions:
                for region in most_common_regions:
                    for dest, info in popular_destinations.items():
                        if info['region'] == region and dest not in past_destinations and dest not in [d['name'] for d in recommended_destinations]:
                            recommended_destinations.append({"name": dest, "image": info['image'], "reason": "Popular in your preferred region"})
            else:
                recommended_destinations = [
                    {"name": dest, "image": info['image'], "reason": "Popular destination"}
                    for dest, info in popular_destinations.items() if dest not in past_destinations
                ]

    return render_template('main.html', username=username, present_trips=present_trips, trip_history=trip_history, recommendations=recommended_destinations, user_interests=user_interests)

@app.route('/present_trip')
def present_trip():
    if 'username' in session:
        # Logic to fetch and display the user's current present trip details
        with sqlite3.connect('users.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM trips WHERE username = ? AND is_present = 1", (session['username'],))
            present_trips = cur.fetchall()
            # Convert start_date and end_date to datetime.date objects for each trip
            for i, trip in enumerate(present_trips):
                start_date_str = trip['start_date']
                end_date_str = trip['end_date']
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    trip_dict = dict(trip)
                    trip_dict['start_date'] = start_date
                    trip_dict['end_date'] = end_date
                    # Provide default values for from_location and budget if None or empty
                    trip_dict['from_location'] = trip_dict['from_location'] if trip_dict['from_location'] else 'Unknown'
                    trip_dict['budget'] = trip_dict['budget'] if trip_dict['budget'] else 'Not specified'
                    present_trips[i] = trip_dict
                except Exception:
                    # If conversion fails, keep original strings
                    pass
            return render_template('present_trip.html', present_trips=present_trips)
    else:
        return redirect(url_for('login'))

@app.route('/trip_history')
def trip_history():
    if 'username' in session:
        username = session['username']
        with sqlite3.connect('users.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            # Fetch trips in history
            cur.execute("SELECT * FROM trips WHERE username = ? AND is_present = 0 ORDER BY start_date DESC", (username,))
            trip_history_data = cur.fetchall()
            # Fetch trip ids that already have feedback
            cur.execute("SELECT trip_id FROM trip_feedback WHERE username = ?", (username,))
            feedback_trip_ids = {row['trip_id'] for row in cur.fetchall()}
        return render_template('trip_history.html', trip_history=trip_history_data, feedback_trip_ids=feedback_trip_ids)
    else:
        return redirect(url_for('login'))

@app.route('/tripplan', methods=['GET', 'POST'])
def tripplan():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        destinations = request.form.getlist('destinations')
        start_date_str = request.form['startDate']
        duration_str = request.form['duration']
        from_location = request.form.get('from_location', None)

        try:
            duration = int(duration_str)
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = start_date + timedelta(days=duration)
        except ValueError:
            flash("Invalid date format.")
            return render_template('tripplan.html', username=session['username'])

        # Render the template with the itinerary to show the buttons
        return render_template('tripplan.html',
                               username=session['username'],
                             #  itinerary=itinerary_content,
                               startDate=start_date_str,
                               duration=duration)
    return render_template('tripplan.html', username=session['username'])

@app.route('/save_itinerary', methods=['POST'])
def save_itinerary():
    if 'username' not in session:
        return jsonify({"success": False, "message": "User not logged in."})

    destination = request.form.get('destination')
    start_date_str = request.form.get('start_date')
    duration_str = request.form.get('duration')
    itinerary_data = request.form.get('itinerary_content')
    from_location = request.form.get('from_location')
    budget = request.form.get('budget')

    # Validate required fields
    missing_fields = []
    for field_name, field_value in [("destination", destination), ("start_date", start_date_str), ("duration", duration_str), ("itinerary_content", itinerary_data), ("from_location", from_location), ("budget", budget)]:
        if not field_value:
            missing_fields.append(field_name)
    if missing_fields:
        return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing_fields)}"})

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()  # Ensure the correct format
        duration = int(duration_str)  # Convert duration to integer
        end_date = start_date + timedelta(days=duration)  # Calculate end date
    except ValueError as e:
        return jsonify({"success": False, "message": f"Invalid date or duration format: {str(e)}"})

    try:
        with sqlite3.connect('users.db') as con:
            cur = con.cursor()
            cur.execute("INSERT INTO trips (username, destination, start_date, end_date, from_location, budget, itinerary_data, is_present) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (session['username'], destination, start_date, end_date, from_location, budget, itinerary_data, 1))
            con.commit()
        return jsonify({"success": True, "redirect_url": url_for('present_trip')})
    except Exception as e:
        # Log the error for debugging
        print(f"Error saving itinerary: {e}")
        return jsonify({"success": False, "message": "An error occurred while saving the itinerary."})

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

@app.route('/delete_trip', methods=['POST'])
def delete_trip():
    if 'username' not in session:
        return redirect(url_for('login'))
    trip_id = request.form.get('trip_id')
    if not trip_id:
        flash("Invalid trip ID.")
        return redirect(url_for('present_trip'))
    try:
        with sqlite3.connect('users.db') as con:
            cur = con.cursor()
            # Verify the trip belongs to the logged-in user before deleting
            cur.execute("SELECT username FROM trips WHERE id = ?", (trip_id,))
            row = cur.fetchone()
            if row and row[0] == session['username']:
                cur.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
                con.commit()
                flash("Trip deleted successfully.")
            else:
                flash("You are not authorized to delete this trip.")
    except Exception as e:
        flash("An error occurred while deleting the trip.")
    return redirect(url_for('present_trip'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        feedback_text = request.form.get('feedback_text')
        username = session['username']
        if not feedback_text or feedback_text.strip() == '':
            flash("Feedback cannot be empty.")
            return redirect(url_for('feedback'))
        try:
            with sqlite3.connect('users.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO feedback (username, feedback_text, created_at) VALUES (?, ?, ?)",
                            (username, feedback_text, datetime.now()))
                con.commit()
            flash("Thank you for your feedback!")
            return redirect(url_for('tripplan'))
        except Exception as e:
            print(f"Error saving feedback: {e}")  # Log the specific error
            flash("An error occurred while saving your feedback. Please try again.")
            return redirect(url_for('feedback'))

@app.route('/view_feedback')
@admin_required
def view_feedback():
    try:
        with sqlite3.connect('users.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            # Fetch trip-specific feedback joined with trip destination
            cur.execute('''
                SELECT tf.id, tf.username, t.destination, tf.enjoyed_most, tf.could_be_better, tf.recommend_friend, tf.issues, tf.star_rating, tf.created_at
                FROM trip_feedback tf
                JOIN trips t ON tf.trip_id = t.id
                UNION ALL
                SELECT f.id, f.username, 'General Feedback' as destination, f.feedback_text as enjoyed_most, NULL as could_be_better, NULL as recommend_friend, NULL as issues, NULL as star_rating, f.created_at
                FROM feedback f
                ORDER BY created_at DESC
            ''')
            feedback_entries = cur.fetchall()
        return render_template('feedback_list.html', feedback_entries=feedback_entries, username=session['username'])
    except Exception as e:
        flash("Error loading feedback entries.")
        return redirect(url_for('main'))

import hashlib
@app.route('/generate_itinerary', methods=['POST'])
def generate_itinerary():
    if 'username' not in session:
        return jsonify({"success": False, "message": "User not logged in."}), 401

    api_key = GEMINI_API_KEY or dotenv_values(
        os.path.join(os.path.dirname(__file__), '.env')
    ).get('GEMINI_API_KEY', '').strip()
    if not api_key:
        return jsonify({
            "success": False,
            "message": "Gemini API key is not configured. Add GEMINI_API_KEY to the project's .env file."
        }), 503

    data = request.get_json()
    from_location = data.get('from')
    destination = data.get('destination')
    budget = data.get('budget')
    start_date = data.get('startDate')
    duration = data.get('duration')
    travel_type = data.get('travelType')

    # Validate input
    if not all([from_location, destination, budget, start_date, duration, travel_type]):
        return jsonify({"success": False, "message": "Missing required fields."}), 400

    # Generate cache key
    cache_key_str = f"{from_location}|{destination}|{budget}|{start_date}|{duration}|{travel_type}"
    cache_key = hashlib.sha256(cache_key_str.encode('utf-8')).hexdigest()

    # Check cache
    if cache_key in itinerary_cache:
        print("Returning cached itinerary")
        return jsonify({"success": True, "itinerary": itinerary_cache[cache_key]})

    # Gemini API prompt
    message = f"""
    Create a detailed travel itinerary in HTML format using <h1>, <h2>, <p>, <ul>, <li>, <strong>, etc.
    The trip starts on {start_date} for a {travel_type} trip to {destination}, lasting {duration} days, with a {budget} budget.
    Consider cost, distance, and traveler comfort.
    Include:
    - Day-by-day activities with descriptions
    - Transportation options
    - Nearby hospitals or medical facilities
    - Weather forecast during trip
    - Hotel or accommodation recommendations (with links)
    Make sure the HTML is clean and directly displayable on a webpage.
    """

    # Gemini API request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    body = {
        "contents": [
            {
                "parts": [
                    {"text": message}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=60)
        if not response.ok:
            try:
                api_error = response.json().get("error", {}).get("message")
            except ValueError:
                api_error = None
            message = api_error or f"Gemini API returned HTTP {response.status_code}."
            return jsonify({"success": False, "message": message}), 502

        try:
            result = response.json()
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Gemini returned an unreadable response. Please try again."
            }), 502

        # Extract itinerary text safely
        candidates = result.get("candidates", []) if isinstance(result, dict) else []
        first_candidate = candidates[0] if isinstance(candidates, list) and candidates else {}
        content = first_candidate.get("content", {}) if isinstance(first_candidate, dict) else {}
        parts = content.get("parts", []) if isinstance(content, dict) else []
        itinerary_html = (
            parts[0].get("text", "")
            if isinstance(parts, list) and parts and isinstance(parts[0], dict)
            else ""
        )

        if not itinerary_html.strip():
            return jsonify({"success": False, "message": "No itinerary content generated."}), 500

        # Cache the result
        itinerary_cache[cache_key] = itinerary_html

        return jsonify({"success": True, "itinerary": itinerary_html})

    except requests.RequestException as e:
        print(f"Gemini API request failed: {e}")
        return jsonify({
            "success": False,
            "message": "Could not connect to Gemini. Check your internet connection and try again."
        }), 502


@app.route('/trip_feedback/<int:trip_id>', methods=['GET'])
def trip_feedback(trip_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    with sqlite3.connect('users.db') as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        # Verify trip belongs to user and has ended
        cur.execute("SELECT * FROM trips WHERE id = ? AND username = ?", (trip_id, username))
        trip = cur.fetchone()
        if not trip:
            flash("Trip not found.")
            return redirect(url_for('trip_history'))
        # Check if trip has ended
        end_date = datetime.strptime(trip['end_date'], '%Y-%m-%d').date()
        if end_date >= date.today():
            flash("Feedback can only be given after the trip has ended.")
            return redirect(url_for('trip_history'))
        # Check if feedback already exists
        cur.execute("SELECT * FROM trip_feedback WHERE trip_id = ? AND username = ?", (trip_id, username))
        existing_feedback = cur.fetchone()
        if existing_feedback:
            flash("Feedback already submitted for this trip.")
            return redirect(url_for('trip_history'))
    return render_template('trip_feedback.html', trip=trip)

@app.route('/submit_trip_feedback/<int:trip_id>', methods=['POST'])
def submit_trip_feedback(trip_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    enjoyed_most = request.form.get('enjoyed_most')
    could_be_better = request.form.get('could_be_better')
    recommend_friend = request.form.get('recommend_friend')
    issues = request.form.get('issues')
    star_rating = request.form.get('star_rating')

    if not all([enjoyed_most, could_be_better, recommend_friend, star_rating]):
        flash("Please fill in all required fields.")
        return redirect(url_for('trip_feedback', trip_id=trip_id))

    try:
        star_rating_int = int(star_rating)
        if star_rating_int < 1 or star_rating_int > 5:
            raise ValueError
    except ValueError:
        flash("Invalid star rating.")
        return redirect(url_for('trip_feedback', trip_id=trip_id))

    with sqlite3.connect('users.db') as con:
        cur = con.cursor()
        # Verify trip belongs to user
        cur.execute("SELECT * FROM trips WHERE id = ? AND username = ?", (trip_id, username))
        trip = cur.fetchone()
        if not trip:
            flash("Trip not found.")
            return redirect(url_for('trip_history'))
        # Insert trip feedback
        cur.execute('''
            INSERT INTO trip_feedback (trip_id, username, enjoyed_most, could_be_better, recommend_friend, issues, star_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (trip_id, username, enjoyed_most, could_be_better, recommend_friend, issues, star_rating_int))
        con.commit()
    flash("Thanks for your feedback! It helps improve future trip plans.")
    # Optionally, redirect to next trip suggestions page or trip history
    return redirect(url_for('trip_history'))

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    try:
        with sqlite3.connect('users.db') as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            # Fetch all feedback entries
            cur.execute('''
                SELECT tf.id, tf.username, t.destination, tf.enjoyed_most, tf.could_be_better, tf.recommend_friend, tf.issues, tf.star_rating, tf.created_at
                FROM trip_feedback tf
                JOIN trips t ON tf.trip_id = t.id
                ORDER BY tf.created_at DESC
            ''')
            feedback_entries = cur.fetchall()

            # Fetch user activities - example: trips count per user
            cur.execute('''
                SELECT username, COUNT(*) as trip_count FROM trips GROUP BY username
            ''')
            user_trip_counts = cur.fetchall()

        return render_template('admin_dashboard.html', feedback_entries=feedback_entries, user_trip_counts=user_trip_counts, username=session['username'])
    except Exception as e:
        flash("Error loading admin dashboard.")
        return redirect(url_for('main'))

if __name__ == '__main__':
    app.run(debug=True)
