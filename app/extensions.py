from flask_marshmallow import Marshmallow
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]) # Creating and instance of Limiter
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'}) # Adding caching to existing extensions

ma = Marshmallow()
