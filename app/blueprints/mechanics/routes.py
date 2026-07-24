from sqlalchemy import select
from flask import jsonify, request
from marshmallow import ValidationError
from app.models import Mechanic, db
from app.extensions import limiter, cache
from .schemas import mechanic_schema, mechanics_schema, mechanic_login_schema
from . import mechanics_bp
from app.utils.util import encode_mechanic_token, mechanic_token_required

# MECHANIC LOGIN
@mechanics_bp.route("/login", methods=['POST'])
@limiter.limit("10 per minute") # probably look to tighten for production
def login():
    try:
        credentials = mechanic_login_schema.load(request.get_json() or {})
        email = credentials['email']
        password = credentials['password']
    except ValidationError as e:
        return jsonify(e.messages), 400
        
    query = select(Mechanic).where(Mechanic.email == email)
    mechanic = db.session.execute(query).scalar_one_or_none()
    
    if mechanic and mechanic.password == password:
        auth_token = encode_mechanic_token(mechanic.id)
        
        response = {
            "status": "success",
            "message": "Successfully Logged In",
            "auth_token": auth_token
        }
        return jsonify(response), 200
    
    return jsonify({'message': 'Invalid email or password'}), 401

# CREATE NEW MECHANIC
@mechanics_bp.route("/", methods=['POST'])
@limiter.limit("3 per hour")
def create_mechanic():
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    # We then check our database for a mechanic who is already using the email or phone that was passed in.
    query = select(Mechanic).where(
        (Mechanic.email == mechanic_data['email']) |
        (Mechanic.phone == mechanic_data['phone'])
    )
    existing_mechanic = db.session.execute(query).scalars().all()
    if existing_mechanic:
        return jsonify({"error": "Email or phone already associated with a mechanic."}), 400
    
    # If the email in not in use, a new mechanic is created, saved to the database, and returned as JSON.
    new_mechanic = Mechanic(**mechanic_data)
    db.session.add(new_mechanic)
    db.session.commit()
    return mechanic_schema.jsonify(new_mechanic), 201

# GET ALL MECHANICS
@mechanics_bp.route("/", methods=['GET'])
@limiter.limit("50 per hour")
def get_mechanics():
    
    try:
        page = int(request.args.get('page'))
        per_page = int(request.args.get('per_page'))
        query = select(Mechanic)
        mechanics = db.paginate(query, page=page, per_page=per_page) 
        return mechanics_schema.jsonify(mechanics), 200
    except:
        query = select(Mechanic)
        mechanics = db.session.execute(query).scalars().all()
    
    return mechanics_schema.jsonify(mechanics), 200

# GET SPECIFIC MECHANIC
@mechanics_bp.route("/<int:mechanic_id>", methods=['GET'])
@limiter.limit("50 per hour")
@cache.cached(timeout=60)
def get_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    
    if mechanic:
        return mechanic_schema.jsonify(mechanic), 200
    return jsonify({"error": "Mechanic not found."}), 404

# UPDATE SPECIFIC MECHANIC
@mechanics_bp.route("/<int:mechanic_id>", methods=['PUT'])
@mechanic_token_required
@limiter.limit("20 per hour")
def update_mechanic(logged_in_mechanic_id, mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    
    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404
    
    if int(logged_in_mechanic_id) != mechanic_id:
        return jsonify({"error": "You can only update your own mechanic profile."}), 403
    
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    query = select(Mechanic).where(
        Mechanic.id != mechanic_id,
        (
            (Mechanic.email == mechanic_data['email']) |
            (Mechanic.phone == mechanic_data['phone'])
        )
    )
    existing_mechanic = db.session.execute(query).scalars().all()
    if existing_mechanic:
        return jsonify({"error": "Email or phone already associated with a mechanic."}), 400
    
    for key, value in mechanic_data.items():
        setattr(mechanic, key, value)
        
    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200

# DELETE SPECIFIC MECHANIC
@mechanics_bp.route("/<int:mechanic_id>", methods=['DELETE'])
@mechanic_token_required
def delete_mechanic(logged_in_mechanic_id, mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    
    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404
    
    if int(logged_in_mechanic_id) != mechanic_id:
        return jsonify({"error": "You can only delete your own mechanic profile."}), 403
    
    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": f'Mechanic id: {mechanic_id}, successfully deleted.'}), 200


# SORT BY MOST EXPERIENCED MECHANICS
@mechanics_bp.route("/experience", methods=['GET'])
def experienced_mechanics():
    query = select(Mechanic)
    mechanics = db.session.execute(query).scalars().all()
    
    mechanics.sort(key = lambda mechanic: len(mechanic.tickets), reverse=True)
    
    return mechanics_schema.jsonify(mechanics)
    
# SEARCH FOR MECHANICS
@mechanics_bp.route("/search", methods=['GET'])
def search_mechanic():
    name = request.args.get("name")
    
    query = select(Mechanic).where(Mechanic.name.like(f'%{name}%'))
    mechanics = db.session.execute(query).scalars().all()
    
    return mechanics_schema.jsonify(mechanics)
