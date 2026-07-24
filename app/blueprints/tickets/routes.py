from sqlalchemy import select
from flask import jsonify, request
from marshmallow import ValidationError
from app.models import Customer, Inventory, Mechanic, Ticket, TicketInventory, db
from app.extensions import limiter, cache
from .schemas import ticket_schema, tickets_schema, return_ticket_schema, edit_ticket_schema, add_part_schema
from . import tickets_bp
from app.utils.util import mechanic_token_required, token_required

# CREATE NEW SERVICE TICKET
@tickets_bp.route("/", methods=['POST'])
@limiter.limit("30 per hour")
def create_ticket():
    try:
        ticket_data = ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    customer = db.session.get(Customer, ticket_data['customer_id'])
    if not customer:
        return jsonify({"error": "Customer not found."}), 404
    
    new_ticket = Ticket(**ticket_data)
    db.session.add(new_ticket)
    db.session.commit()
    return ticket_schema.jsonify(new_ticket), 201

# GET ALL TICKETS
# This is now a route for the logged in customer to get all of their service tickets, rather than an employee getting them for a certain customer
@tickets_bp.route("/my-tickets", methods=['GET'])
@token_required
@limiter.limit("50 per hour")
def get_tickets(customer_id):
    query = select(Ticket).where(Ticket.customer_id == customer_id)
    tickets = db.session.execute(query).scalars().all()
    
    return tickets_schema.jsonify(tickets)

# EDIT MECHANIC(S) ASSOCIATED TO TICKET
@tickets_bp.route("/<int:ticket_id>/edit", methods=['PUT'])
def edit_ticket(ticket_id):
    try:
        ticket_edits = edit_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    
    query = select(Ticket).where(Ticket.id == ticket_id)
    ticket = db.session.execute(query).scalars().first()
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404
    
    for mechanic_id in ticket_edits['add_ids']:
        query = select(Mechanic).where(Mechanic.id == mechanic_id)
        mechanic = db.session.execute(query).scalars().first()
        
        if mechanic and mechanic not in ticket.mechanics:
            ticket.mechanics.append(mechanic)
            
    for mechanic_id in ticket_edits['remove_ids']:
        query = select(Mechanic).where(Mechanic.id == mechanic_id)
        mechanic = db.session.execute(query).scalars().first()
        
        if mechanic and mechanic in ticket.mechanics:
            ticket.mechanics.remove(mechanic)
            
    db.session.commit()
    return return_ticket_schema.jsonify(ticket)

# ADD INVENTORY PART TO TICKET
@tickets_bp.route("/<int:ticket_id>/add-part/<int:inventory_id>", methods=['PUT'])
@mechanic_token_required
@limiter.limit("30 per hour")
def add_part_to_ticket(_logged_in_mechanic_id, ticket_id, inventory_id): # leading underscore added to logged_in_mechanic_id to signify that it's required by the call pattern, but intentionally unused here (handled by @mechanic_token_required)
    try:
        part_data = add_part_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404
    
    inventory_part = db.session.get(Inventory, inventory_id)
    if not inventory_part:
        return jsonify({"error": "Inventory part not found."}), 404
    
    query = select(TicketInventory).where(
        TicketInventory.ticket_id == ticket_id,
        TicketInventory.inventory_id == inventory_id
    )
    ticket_inventory = db.session.execute(query).scalars().first()
    
    if ticket_inventory:
        ticket_inventory.quantity += part_data['quantity']
    else:
        ticket_inventory = TicketInventory(
            ticket_id=ticket_id,
            inventory_id=inventory_id,
            quantity=part_data['quantity']
        )
        db.session.add(ticket_inventory)
    
    db.session.commit()
    return return_ticket_schema.jsonify(ticket), 200

# GET SPECIFIC TICKET
@tickets_bp.route("/<int:ticket_id>", methods=['GET'])
@limiter.limit("60 per hour")
@cache.cached(timeout=60)
def get_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    
    if ticket:
        return ticket_schema.jsonify(ticket), 200
    return jsonify({"error": "Ticket not found."}), 404

# UPDATE SPECIFIC TICKET
@tickets_bp.route("/<int:ticket_id>", methods=['PUT'])
@limiter.limit("60 per hour")
def update_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404
    
    try:
        ticket_data = ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    customer = db.session.get(Customer, ticket_data['customer_id'])
    if not customer:
        return jsonify({"error": "Customer not found."}), 404
    
    for key, value in ticket_data.items():
        setattr(ticket, key, value)
        
    db.session.commit()
    return ticket_schema.jsonify(ticket), 200

# DELETE SPECIFIC TICKET <---assignment is saying you don't need to delete a service ticket, becuase "why would you want to, you always want to retain service tickets, but you could've created a wrong one that needs to be deleted (I can see many legitimate reasons to need to delete a ticket, so leaving this in here)"
@tickets_bp.route("/<int:ticket_id>", methods=['DELETE'])
@mechanic_token_required
@limiter.limit("20 per hour")
def delete_ticket(_logged_in_mechanic_id, ticket_id): # leading underscore added to logged_in_mechanic_id to signify that it's required by the call pattern, but intentionally unused here (handled by @mechanic_token_required)
    ticket = db.session.get(Ticket, ticket_id)
    
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404
    
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"message": f'Ticket id: {ticket_id}, successfully deleted.'}), 200
