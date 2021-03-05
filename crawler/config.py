

class Config(object):
    # SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5437/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # LANGUAGES = ['en', 'vi']
