# app.py
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jokes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Joke model
class Joke(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50))
    joke_type = db.Column(db.String(50))
    joke = db.Column(db.Text)  # For "single" type jokes
    setup = db.Column(db.Text)  # For "twopart" type jokes
    delivery = db.Column(db.Text)  # For "twopart" type jokes
    nsfw = db.Column(db.Boolean)
    political = db.Column(db.Boolean)
    sexist = db.Column(db.Boolean)
    safe = db.Column(db.Boolean)
    lang = db.Column(db.String(10))

# Initialize the database
with app.app_context():
    db.create_all()

JOKE_API_URL = 'https://v2.jokeapi.dev/joke/Any?type=single,twopart&lang=en&amount=100'

def fetch_and_store_jokes():
    response = requests.get(JOKE_API_URL)
    jokes_data = response.json()

    # Process jokes and store in the database
    for joke in jokes_data['jokes']:
        # Process joke fields
        category = joke.get('category', '')
        joke_type = joke.get('type', '')
        nsfw = joke.get('flags', {}).get('nsfw', False)
        political = joke.get('flags', {}).get('political', False)
        sexist = joke.get('flags', {}).get('sexist', False)
        safe = joke.get('safe', False)
        lang = joke.get('lang', '')

        if joke_type == 'single':
            joke_text = joke.get('joke', '')
            setup = None
            delivery = None
        elif joke_type == 'twopart':
            joke_text = None
            setup = joke.get('setup', '')
            delivery = joke.get('delivery', '')
        else:
            continue  # Skip unsupported types

        joke_obj = Joke(
            category=category,
            joke_type=joke_type,
            joke=joke_text,
            setup=setup,
            delivery=delivery,
            nsfw=nsfw,
            political=political,
            sexist=sexist,
            safe=safe,
            lang=lang
        )
        db.session.add(joke_obj)

    db.session.commit()


@app.route('/jokes', methods=['GET'])
def get_jokes():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        jokes = Joke.query.paginate(page=page, per_page=per_page, error_out=False)
        
        if not jokes.items:
            return jsonify({"error": "No jokes found in database. Fetch jokes first!"}), 404

        joke_list = [{
            'id': joke.id,
            'category': joke.category,
            'type': joke.joke_type,
            'joke': joke.joke,
            'setup': joke.setup,
            'delivery': joke.delivery,
            'nsfw': joke.nsfw,
            'political': joke.political,
            'sexist': joke.sexist,
            'safe': joke.safe,
            'lang': joke.lang
        } for joke in jokes.items]

        return jsonify({
            'total': jokes.total,
            'pages': jokes.pages,
            'current_page': jokes.page,
            'jokes': joke_list
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Show the real error in response

@app.route('/fetch-jokes', methods=['POST'])
def fetch_jokes():
    fetch_and_store_jokes()
    return jsonify({"message": "Jokes fetched and stored successfully!"}), 200


