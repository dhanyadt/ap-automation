from .base import *

DEBUG = True

# Explicitly ensure CORS is open for Vite dev server
CORS_ALLOW_ALL_ORIGINS = True

# Disable throttling in development
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/min',
    'user': '2000/min',
}
