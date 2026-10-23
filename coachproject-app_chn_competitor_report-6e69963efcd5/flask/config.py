
import os

class AppConfig:
    # __file__ refers to the file settings.py
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
    APP_STATIC = os.path.join(APP_ROOT, 'app', 'static')

    UPLOAD_FOLDER = os.path.join(APP_STATIC, 'uploads')
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

    # Both cache expiry time and token expiry time will be measured in seconds
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 30 * 60  # Cache expires after 30 minutes

    JWT_EXP_DURATION = 24 * 60 * 60 # 1 day (in seconds)
    API_KEY_NAME = 'Api-Key'

class TestConfig:
    TESTING = True
    JWT_SECRET = "your_secret_key_for_tests"
    API_KEY = "test_api_key"

    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    APP_STATIC = os.path.join(APP_ROOT, 'app', 'static')
    UPLOAD_FOLDER = os.path.join(APP_STATIC, 'uploads')
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 30 * 60  
    JWT_EXP_DURATION = 1 * 60 * 60 
    API_KEY_NAME = 'Api-Key'




