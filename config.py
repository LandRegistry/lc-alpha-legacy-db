import os


class Config(object):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'db2')
    DATABASE_USER = os.getenv('DATABASE_USER', 'lc-db2-mock')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'lcalpha')
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}/{}".format(DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME)
    ALLOW_DEV_ROUTES = True
    IMAGE_DIRECTORY = '/home/vagrant/'


class PreviewConfig(Config):
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'db2')
    DATABASE_USER = os.getenv('DATABASE_USER', 'lc-db2-mock')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'lcalpha')
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}/{}".format(DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME)
    ALLOW_DEV_ROUTES = True
    IMAGE_DIRECTORY = "~/"
