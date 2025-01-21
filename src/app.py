"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, session
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planets, FavoritePlanets, FavoritePeople

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user')
def get_user():
    all_users = User.query.all()
    all_users_serialized = []
    for user in all_users:
        all_users_serialized.append(user.serialize())
    print (all_users)
    return jsonify({'msg': 'get user ok', 'data': all_users_serialized})

@app.route('/people')
def get_people():
    all_people = People.query.all()
    all_people_serialized = []
    for person in all_people:
        all_people_serialized.append(person.serialize())
    print (all_people)
    return jsonify({'msg': 'get people ok', 'data': all_people_serialized})

@app.route('/people/<int:people_id>')
def get_single_person(people_id):
    person = People.query.get(people_id)
    if person is None:
        return jsonify ({'msg': f'El personaje con id {people_id} no existe'}), 400
    print(person)
    return jsonify({'msg': person.serialize()})

@app.route('/planets')
def get_planets():
    all_planets= Planets.query.all()
    all_planets_serialized = []
    for planet in all_planets:
        all_planets_serialized.append(planet.serialize())
    print(all_planets)
    return jsonify({'msg': 'get planet ok', 'data': all_planets_serialized})

@app.route('/planets/<int:planets_id>')
def get_single_planet(planets_id):
    planet = Planets.query.get(planets_id)
    planet_serialized = planet.serialize()
    for person in planet.people:
        planet_serialized['people'].append.serialize()
    if planet is None:
        return jsonify ({'msg': f'El planeta con id {planets_id} no existe'}), 400
    print(planet)
    return jsonify({'msg': planet.serialize()})

@app.route('/users/favorites', methods=['GET'])
def get_all_favorites():
    planet_favorites = FavoritePlanets.query.all()
    planet_favorites_serialized = [
        {
            "user_id": favorite.user_id,
            "planet": favorite.planets_favorites.serialize()
        }
        for favorite in planet_favorites
    ]
    people_favorites = FavoritePeople.query.all()
    people_favorites_serialized = [
        {
            "user_id": favorite.user_id,
            "person": favorite.people_favorites.serialize()
        }
        for favorite in people_favorites
    ]
    return jsonify({
        "planets_favorites": planet_favorites_serialized,
        "people_favorites": people_favorites_serialized
    }), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'msg': 'Debes proporcionar el user_id en el cuerpo de la solicitud'}), 400
    planet = Planets.query.get(planet_id)
    if not planet:
        return jsonify({'msg': f'El planeta con id {planet_id} no existe'}), 404
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': f'El usuario con id {user_id} no existe'}), 404
    existing_favorite = FavoritePlanets.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if existing_favorite:
        return jsonify({'msg': f'El planeta con id {planet_id} ya está en favoritos del usuario {user_id}'}), 400
    new_favorite = FavoritePlanets(user_id=user_id, planet_id=planet_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify({'msg': f'El planeta con id {planet_id} se ha añadido a favoritos del usuario {user_id}'}), 201


@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'msg': 'Debes proporcionar el user_id en el cuerpo de la solicitud'}), 400
    person = People.query.get(people_id)
    if not person:
        return jsonify({'msg': f'El personaje con id {people_id} no existe'}), 404
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': f'El usuario con id {user_id} no existe'}), 404
    existing_favorite = FavoritePeople.query.filter_by(user_id=user_id, people_id=people_id).first()
    if existing_favorite:
        return jsonify({'msg': f'El personaje con id {people_id} ya está en favoritos del usuario {user_id}'}), 400
    new_favorite = FavoritePeople(user_id=user_id, people_id=people_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify({'msg': f'El personaje con id {people_id} se ha añadido a favoritos del usuario {user_id}'}), 201


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def remove_favorite_planet(planet_id):
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'msg': 'Debes proporcionar el user_id en el cuerpo de la solicitud'}), 400
    favorite = FavoritePlanets.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if not favorite:
        return jsonify({'msg': f'No se encontró el planeta con id {planet_id} en favoritos del usuario {user_id}'}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({'msg': f'El planeta con id {planet_id} se ha eliminado de los favoritos del usuario {user_id}'}), 200


@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def remove_favorite_person(people_id):
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'msg': 'Debes proporcionar el user_id en el cuerpo de la solicitud'}), 400
    favorite = FavoritePeople.query.filter_by(user_id=user_id, people_id=people_id).first()
    if not favorite:
        return jsonify({'msg': f'No se encontró el personaje con id {people_id} en favoritos del usuario {user_id}'}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({'msg': f'El personaje con id {people_id} se ha eliminado de los favoritos del usuario {user_id}'}), 200


if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
