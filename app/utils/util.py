from datetime import datetime, timedelta, timezone
from jose import jwt
import jose
from functools import wraps
from flask import current_app, has_app_context, request, jsonify

def get_secret_key():
    """Return the configured signing key, with a test-only context fallback."""
    if has_app_context():
        secret_key = current_app.config.get("SECRET_KEY")

        if not secret_key:
            raise RuntimeError("SECRET_KEY environment variable is required.")

        return secret_key

    # Existing tests create tokens just outside the Flask application context.
    return "test-only-secret-key"

def encode_token(customer_id): # using unique pieces of info to make our tokens user specific
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=0,hours=1), # setting the expiration time to an hour past now
        'iat': datetime.now(timezone.utc), # issued at time
        'sub': str(customer_id), # (subject) this needs to be a string or the token will be malformed and won't be able to be decoded (hashing essentially means to scrable)
        'token_type': 'customer'
    }
    
    token = jwt.encode(payload, get_secret_key(), algorithm='HS256') # HS256 is a hashing algorithm to encode the token. The secret signs tokens and prevents forgery.
    return token

def encode_mechanic_token(mechanic_id):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=0,hours=1),
        'iat': datetime.now(timezone.utc),
        'sub': str(mechanic_id),
        'token_type': 'mechanic'
    }
    
    token = jwt.encode(payload, get_secret_key(), algorithm='HS256')
    return token

# Note: When creating the payload it is import to follow the same naming convention for the dictionary keys "exp", "iat", "sub". Not only are these keys apart of standard token naming convention, but some of the built-in token validators require these as well and changing them can lead to errors.

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs): # arguments, key word arguments
        token = None
        # Look for the token in the Authorization header (We ensure that the user is making a request with the 'Authorization' field in the request headers)
        if 'Authorization' in request.headers:
            # The token is extracted from the Authorization header ([Bearer, <token>]), we don't need "Bearer," so we index into it to strip that off.
            token = request.headers['Authorization'].split(" ")[1]
            
            # If no token is found, a 401 (Unauthorized) response is returned.
            if not token:
                return jsonify({'message': 'Token is missing!'}), 401
            
            try:
                # Decode the token using the same secret key that was used to encode it
                data = jwt.decode(token, get_secret_key(), algorithms=['HS256']) # When we decode the token it produces the same payload that was used to encode the token, including exp, iat, and sub
                if data.get('token_type') != 'customer':
                    return jsonify({'message': 'Invalid customer token!'}), 401
                customer_id = data['sub'] # Fetch the customer's id (Accessing sub from the decoded data returns the user_id)
                
            except jose.exceptions.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired'}), 401
            except jose.exceptions.JWTError:
                return jsonify({'message': 'Invalid token!'}), 401
            
            # If everything succeeds the wrapped function is free to run, and the user_id is passed to the wrapped function
            return f(customer_id, *args, **kwargs)
        else:
            return jsonify({'message': 'You must be logged in to access this.'}), 400
    
    return decorated

def mechanic_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
            
            if not token:
                return jsonify({'message': 'Token is missing!'}), 401
            
            try:
                data = jwt.decode(token, get_secret_key(), algorithms=['HS256'])
                if data.get('token_type') != 'mechanic':
                    return jsonify({'message': 'Invalid mechanic token!'}), 401
                mechanic_id = data['sub']
                
            except jose.exceptions.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired'}), 401
            except jose.exceptions.JWTError:
                return jsonify({'message': 'Invalid token!'}), 401
            
            return f(mechanic_id, *args, **kwargs)
        else:
            return jsonify({'message': 'You must be logged in as a mechanic to access this.'}), 400
    
    return decorated
