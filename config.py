import os


class DevelopmentConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get('MY_DATABASE_URI') # use: 'mysql+mysqlconnector://root:<YOUR MYSQL PASSWORD>@localhost/<YOUR DATABASE>'
    DEBUG = True

DevelopementConfig = DevelopmentConfig
    
class TestingConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///testing.db'
    RATELIMIT_ENABLED = False
    DEBUG = True
    CACHE_TYPE = 'NullCache'

class ProductionConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DEBUG = False
    CACHE_TYPE = "SimpleCache"
