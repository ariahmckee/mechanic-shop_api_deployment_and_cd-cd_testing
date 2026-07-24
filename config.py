
import os


class DevelopmentConfig:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:<YOUR MYSQL PASSWORD>@localhost/<YOUR DATABASE>'
    DEBUG = True

DevelopementConfig = DevelopmentConfig
    
class TestingConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///testing.db'
    RATELIMIT_ENABLED = False
    DEBUG = True
    CACHE_TYPE = 'NullCache'

class ProductionConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DEBUG = False
