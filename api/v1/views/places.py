#!/usr/bin/python3
"""Create a view for Place"""

from flask import jsonify, request, abort, make_response
from api.v1.views import app_views
from models import storage
from models.city import City
from models.place import Place


@app_views.route('/cities/<city_id>/places', methods=['GET'],
                 strict_slashes=False)
def get_places_by_city(city_id):
    """Retrieves the list of all Place objects of a city"""
    city = storage.get("City", city_id)
    if not city:
        abort(404)
    return jsonify([place.to_dict() for place in city.places])


@app_views.route('/places/<place_id>', methods=['GET'], strict_slashes=False)
def get_place(place_id):
    """Retrieves a place object by ID"""
    place = storage.get("Place", place_id)
    if place is None:
        abort(404)
    return jsonify(place.to_dict())


@app_views.route('/places/<place_id>', methods=['DELETE'],
                 strict_slashes=False)
def delete_place(place_id):
    """Deletes a Place object by ID"""
    place = storage.get("Place", place_id)
    if place is None:
        abort(404)
    place.delete()
    storage.save()
    return make_response(jsonify({}), 200)


@app_views.route('/cities/<city_id>/places', methods=['POST'],
                 strict_slashes=False)
def create_place(city_id):
    """Creates a Place object"""
    city = storage.get("City", city_id)
    if not city:
        abort(404)
    data = request.get_json()
    if not data:
        abort(400, 'Not a JSON')
    if 'user_id' not in data:
        abort(400, 'Missing user_id')
    user = storage.get("User", data["user_id"])
    if not user:
        abort(404)
    if 'name' not in data:
        abort(400, 'Missing name')
    place = Place(**data)
    setattr(place, 'city_id', city_id)
    storage.new(place)
    storage.save()
    return make_response(jsonify(place.to_dict()), 201)


@app_views.route('/places/<place_id>', methods=['PUT'],
                 strict_slashes=False)
def update_place(place_id):
    """Updates a Place object by ID"""
    place = storage.get("Place", place_id)
    if place is None:
        abort(404)
    data = request.get_json()
    if not data:
        abort(400, 'Not a JSON')

    # Update the State object's attributes based on the JSON data
    for key, value in data.items():
        if key not in ['id', 'user_id', 'city_id', 'created_at', 'updated_at']:
            setattr(place, key, value)
    storage.save()
    return make_response(jsonify(place.to_dict()), 200)


@app.views.route("/places_search", methods=['POST'], strict_slashes=False)
def places_search():
    """Retreive place object based JSON file available"""
    # check if request has valid json
    if request.get_json() is None:
        abort(400, message="Not a JSON")
    data = request.get_json()

    if data and len(data):
        states = data.get("states", None)
        cities = data.get("cities", None)
        amenities = data.get("amenities", None)

    # no criteria provided, retreive all places
    if not data or not len(data) or (
            not states and
            not cities and
            not amaneities):
        places = storage.alla(Places).values()

        list_palces = []
        for place in places:
            list_places.append(place.to_dict())
        return jsonify(list_places)

    list_places = []
    # filter and retreive places upon states criteria
    if states:
        states_obj = [storage.get(State, s_id) for s_id in states]
        for state in states_obj:
            if state:
                for city in state.cities:
                    if city:
                        for place in city.places:
                            list_places.append(place)

    # filter and retreive places upon cities criteria
    if cities:
        cities_obj = [storage.get(City, c_id) for c_id in cities]
        for city in cities_obj:
            if city:
                for place in city.places:
                    if place not in list_places:
                        list_places.append(place)

    # filter and retreive places upon amenities criteria
    if amenities:
        if not list_places:
            list_palces = storage.all(Place).values()
        amenities_obj = [storage.get(Amenity, a_id) for a_id in amenities]

        list_places = [place for place in list_places
                       if all([am in place.amenities
                               for am in amenities_obj])]

        places = []
        for p in list_places:
            dp = p.to_dict()
            dp.pop("amenities", None)
            places.append(dp)
        return jsonify(places)
