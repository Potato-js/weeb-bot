import jwt

from datetime import timedelta
from flask import Flask, render_template, redirect, url_for, request, jsonify, session
from flask_discord import DiscordOAuth2Session, Unauthorized
from flask_session import Session
from os import getenv


def create_app():
    app = Flask(__name__)
    app.secret_key = getenv("FLASK_SECRET_KEY", "APP_SECRET_KEY")

    CLIENT_ID = getenv("DISCORD_CLIENT_ID")
    CLIENT_SECRET = getenv("DISCORD_CLIENT_SECRET")
    TOKEN = getenv("TOKEN")
    REDIRECT_URI = getenv("DISCORD_REDIRECT_URI")

    # Flask-Session Storing
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = "/tmp/flask_session"
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    Session(app)

    # Discord OAuth Config
    app.config["DISCORD_CLIENT_ID"] = CLIENT_ID
    app.config["DISCORD_CLIENT_SECRET"] = CLIENT_SECRET
    app.config["DISCORD_REDIRECT_URI"] = REDIRECT_URI
    app.config["DISCORD_BOT_TOKEN"] = TOKEN
    app.config["DISCORD_SCOPES"] = ["identify", "guilds"]

    # Initialize Discord OAuth
    discord = DiscordOAuth2Session(app)

    @app.route("/")
    def home():
        return render_template("index.html", authorized=discord.authorized)

    @app.route("/login/")
    def login():
        return discord.create_session()

    @app.route("/callback/")
    def callback():
        # Validate the 'state' parameter
        state = request.args.get("state")
        if not state:
            return jsonify({"error": "Missing 'state' parameter"}), 400

        # Validate the JWT format of the 'state' parameter
        try:
            if len(state.split(".")) != 3:
                raise ValueError("Malformed JWT token.")
            decoded_state = jwt.decode(
                state, app.secret_key, algorithms=["HS256"]
            )  # Ensure the key and algorithm match
        except (jwt.DecodeError, ValueError) as e:
            return jsonify({"error": f"Invalid JWT token: {str(e)}"}), 400

        # Continue with Discord callback
        try:
            discord.callback()
        except Unauthorized:
            return jsonify({"error": "Unauthorized access."}), 403

        # Fetch user data
        user = discord.fetch_user()
        session["user"] = {"id": user.id, "name": user.name, "avatar": user.avatar_url}

        return redirect(url_for("dashboard"))

    @app.route("/session_data/")
    def session_data():
        return jsonify(session)

    @app.route("/manage/<guild_id>")
    def manage_guild(guild_id):
        return f"Manage guild {guild_id}"

    @app.route("/dashboard/")
    def dashboard():
        if not discord.authorized:
            return redirect(url_for("login"))

        user = session.get("user")
        guilds = discord.fetch_guilds()
        admin_guild = [guild for guild in guilds if guild.permissions.administrator]

        return render_template("dashboard.html", user=user, guilds=admin_guild)

    @app.route("/logout/")
    def logout():
        discord.revoke()
        session.clear()
        return redirect(url_for("home"))

    return app
