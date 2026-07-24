from sqlalchemy import select
from flask import jsonify, request
from marshmallow import ValidationError
from app.models import Customer, db
from app.extensions import limiter, cache
from .schemas import customer_schema, customers_schema, login_schema
from . import customers_bp
from app.utils.util import encode_token, token_required

# CUSTOMER LOGIN
@customers_bp.route("/login", methods=['POST'])
@limiter.limit("10 per minute") # probably look to tighten for production
def login():
    try:
        credentials = login_schema.load(request.get_json() or {})
        email = credentials['email']
        password = credentials['password']
    except ValidationError as e:
        return jsonify(e.messages), 400
        
    query = select(Customer).where(Customer.email == email)
    customer = db.session.execute(query).scalar_one_or_none()
    
    if customer and customer.password == password:
        auth_token = encode_token(customer.id)
        
        response = {
            "status": "success",
            "message": "Successfully Logged In",
            "auth_token": auth_token
        }
        return jsonify(response), 200
    
    return jsonify({'message': 'Invalid email or password'}), 401


# CREATE NEW CUSTOMER
@customers_bp.route("/", methods=['POST'])
@limiter.limit("30 per hour") # Presumably this is an internal system, so maybe danger of DDOS attack isn't as siginificant, but, for the lesson, adding as if these were public facing
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    # If validation fails, a ValidationError is raised and handled with a 400 response.
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    # We then check our database for a customer who is already using the email that was passed in.
    query = select(Customer).where(Customer.email == customer_data['email']) # checking our db for a customer with this email
    existing_customer = db.session.execute(query).scalars().all()
    if existing_customer:
        return jsonify({"error": "Email already associated with an account."}), 400
    
    # If the email in not in use, a new customer is created, saved to the database, and returned as JSON.
    new_customer = Customer(**customer_data)
    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201

# GET ALL CUSTOMERS
@customers_bp.route("/", methods=['GET'])
@limiter.limit("50 per hour")
def get_customers(): 
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        return jsonify({"error": "page and per_page must be integers."}), 400
    
    if page < 1 or per_page < 1:
        return jsonify({"error": "page and per_page must be positive integers."}), 400
    
    query = select(Customer)
    customers = db.paginate(query, page=page, per_page=per_page, error_out=False)
    
    return customers_schema.jsonify(customers.items), 200

# GET SPECIFIC CUSTOMER
@customers_bp.route("/<int:customer_id>", methods=['GET'])
@limiter.limit("50 per hour")
@cache.cached(timeout=60)
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    
    if customer:
        return customer_schema.jsonify(customer), 200
    return jsonify({"error": "Customer not found."}), 404

# UPDATE SPECIFIC CUSTOMER
@customers_bp.route("/", methods=['PUT'])
@token_required
@limiter.limit("20 per hour")
def update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    
    if not customer:
        return jsonify({"error:" "Customer not found."}), 404
    
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    for key, value in customer_data.items():
        setattr(customer, key, value)
        
    db.session.commit()
    return customer_schema.jsonify(customer), 200

# DELETE SPECIFIC CUSTOMER
@customers_bp.route('/', methods=['DELETE'])
@token_required
def delete_customer(customer_id): # recieving customer_id from the token
    query = select(Customer).where(Customer.id == customer_id)
    customer = db.session.execute(query).scalars().first()
    
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f'Customer id: {customer_id}, successfully deleted.'}), 200
