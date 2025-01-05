import jwt

from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_discord import DiscordOAuth2Session, Unauthorized
from os import getenv


def create_app():
    app = Flask(__name__)
    app.secret_key = getenv("FLASK_SECRET_KEY")

    CLIENT_ID = getenv("DISCORD_CLIENT_ID")
    CLIENT_SECRET = getenv("DISCORD_CLIENT_SECRET")
    TOKEN = getenv("TOKEN")
    REDIRECT_URI = getenv("DISCORD_REDIRECT_URI")

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

        return redirect(url_for("dashboard"))

    @app.route("/dashboard/")
    def dashboard():
        if not discord.authorized:
            return redirect(url_for("login"))

        user = discord.fetch_user()
        guilds = discord.fetch_guilds()

        admin_guild = [guild for guild in guilds if guild.permissions.administrator]

        return render_template("dashboard.html", user=user, guilds=admin_guild)

    @app.route("/logout/")
    def logout():
        discord.revoke()
        return redirect(url_for("home"))

    return app
