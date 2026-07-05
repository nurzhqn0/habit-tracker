import os

# Must be set before any `app.*` import: app.main builds the app at import time,
# and the production guard would reject the dev JWT secret otherwise.
os.environ.setdefault("ENVIRONMENT", "development")
