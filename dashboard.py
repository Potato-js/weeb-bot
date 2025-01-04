import os

from dashboard.app import create_app

if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # REMOVE THIS LINE IN PRODUCTION
    app = create_app()
    app.run(debug=True)
