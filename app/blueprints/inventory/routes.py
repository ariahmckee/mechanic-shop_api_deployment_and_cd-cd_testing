from sqlalchemy import select
from flask import jsonify, request
from marshmallow import ValidationError
from app.models import Inventory, db
from app.extensions import limiter, cache
from app.utils.util import mechanic_token_required
from .schemas import inventory_schema, inventories_schema
from . import inventory_bp


# CREATE NEW PART IN INVENTORY
@inventory_bp.route("/", methods=['POST'])
@mechanic_token_required
@limiter.limit("30 per hour")
def create_inventory(_logged_in_mechanic_id): # leading underscore added to logged_in_mechanic_id to signify that it's required by the call pattern, but intentionally unused here (handled by @mechanic_token_required)
    try:
        inventory_data = inventory_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_part = Inventory(**inventory_data)
    db.session.add(new_part)
    db.session.commit()
    
    return inventory_schema.jsonify(new_part), 201


# GET ALL PARTS IN INVENTORY
@inventory_bp.route("/", methods=['GET'])
@limiter.limit("50 per hour")
@cache.cached(timeout=60)
def get_inventory():
    query = select(Inventory)
    inventory = db.session.execute(query).scalars().all()
    
    return inventories_schema.jsonify(inventory), 200


# GET SPECIFIC PART IN INVENTORY
@inventory_bp.route("/<int:inventory_id>", methods=['GET'])
@limiter.limit("50 per hour")
@cache.cached(timeout=60)
def get_inventory_part(inventory_id):
    inventory_part = db.session.get(Inventory, inventory_id)
    
    if inventory_part:
        return inventory_schema.jsonify(inventory_part), 200
    return jsonify({"error": "Inventory part not found."}), 404


# UPDATE SPECIFIC PART IN INVENTORY
@inventory_bp.route("/<int:inventory_id>", methods=['PUT'])
@mechanic_token_required
@limiter.limit("30 per hour")
def update_inventory(_logged_in_mechanic_id, inventory_id): # leading underscore added to logged_in_mechanic_id to signify that it's required by the call pattern, but intentionally unused here (handled by @mechanic_token_required)
    inventory_part = db.session.get(Inventory, inventory_id)
    
    if not inventory_part:
        return jsonify({"error": "Inventory part not found."}), 404
    
    try:
        inventory_data = inventory_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    for key, value in inventory_data.items():
        setattr(inventory_part, key, value)
        
    db.session.commit()
    return inventory_schema.jsonify(inventory_part), 200


# DELETE SPECIFIC PART IN INVENTORY
@inventory_bp.route("/<int:inventory_id>", methods=['DELETE'])
@mechanic_token_required
@limiter.limit("20 per hour")
def delete_inventory(_logged_in_mechanic_id, inventory_id): # leading underscore added to logged_in_mechanic_id to signify that it's required by the call pattern, but intentionally unused here (handled by @mechanic_token_required)
    inventory_part = db.session.get(Inventory, inventory_id)
    
    if not inventory_part:
        return jsonify({"error": "Inventory part not found."}), 404
    
    db.session.delete(inventory_part)
    db.session.commit()
    return jsonify({"message": f'Inventory part id: {inventory_id}, successfully deleted.'}), 200
