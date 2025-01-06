import jwt
import sqlite3
import requests

from datetime import timedelta
from flask import Flask, render_template, redirect, url_for, request, jsonify, session
from flask_discord import DiscordOAuth2Session, Unauthorized
from flask_session import Session
from os import getenv, path, getcwd
from src.utils.logger import setup_logger
from src.bot import bot

logger = setup_logger()


def create_app():
    app = Flask(__name__)
    app.secret_key = getenv("FLASK_SECRET_KEY", "APP_SECRET_KEY")

    CLIENT_ID = getenv("DISCORD_CLIENT_ID")
    CLIENT_SECRET = getenv("DISCORD_CLIENT_SECRET")
    TOKEN = getenv("TOKEN")
    REDIRECT_URI = getenv("DISCORD_REDIRECT_URI")

    # Flask-Session Storing
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = path.join(getcwd(), "flask_session")
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
        state = discord.create_session()
        logger.debug(f"OAuth2 Session created with state: {state}")
        return state

    @app.route("/callback/")
    def callback():
        # Validate the 'state' parameter
        state = request.args.get("state")
        logger.debug(f"OAuth2 Session received with state: {state}")

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

    @app.route("/manage/<int:guild_id>")
    def manage_guild(guild_id):
        features = [
            {"name": "Fake Permissions", "route": f"fakeperms/{guild_id}"},
        ]

        try:
            # Fetch all guilds the bot is in
            guilds = discord.fetch_guilds()

            # Find the specific guild by ID
            guild = next((g for g in guilds if g.id == guild_id), None)

            if guild:
                guild_name = guild.name
            else:
                guild_name = "Unknown Guild"
        except Exception as e:
            logger.error(f"Error fetching guild: {e}")
            guild_name = "Error fetching guild"

        # Render the template with guild name and features
        return render_template(
            "server_dashboard.html", features=features, guild=guild_name
        )

    @app.route("/fakeperms/<int:guild_id>", methods=["GET", "POST"])
    def manage_fakeperms(guild_id):
        try:
            # Fetch roles using Discord API
            url = f"https://discord.com/api/v10/guilds/{guild_id}/roles"
            headers = {"Authorization": f"Bot {TOKEN}"}
            response = requests.get(url, headers=headers)

            if response.status_code == 403:
                return (
                    jsonify(
                        {
                            "error": "Bot does not have permission to access this guild's roles."
                        }
                    ),
                    403,
                )
            elif response.status_code == 404:
                return jsonify({"error": "Guild not found."}), 404
            elif response.status_code != 200:
                return (
                    jsonify(
                        {"error": f"Failed to fetch roles: {response.status_code}"}
                    ),
                    response.status_code,
                )

            # Process roles
            roles = [
                {"id": role["id"], "name": role["name"]} for role in response.json()
            ]

            # Permissions (example data; replace with your actual permissions)
            permissions = {
                "kick_members": "Kick Members",
                "ban_members": "Ban Members",
                "manage_channels": "Manage Channels",
                "manage_roles": "Manage Roles",
                "administrator": "Administrator",
            }

            # Fetch current role permissions from the database
            conn = sqlite3.connect("./src/databases/fakeperms.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role_id, permissions FROM role_permissions WHERE guild_id = ?",  # TODO: add the guild_id parameter in fakeperms.db
                (guild_id,),
            )
            current_role_perms = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()

            if request.method == "POST":
                role_id = int(request.form.get("role_id"))
                selected_perms = request.form.getlist("permissions")
                new_permission_value = sum(int(perm) for perm in selected_perms)

                # Update database with new permissions
                conn = sqlite3.connect("./src/databases/fakeperms.db")
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO role_permissions (guild_id, role_id, permissions)
                    VALUES (?, ?, ?)
                    ON CONFLICT(guild_id, role_id) DO UPDATE SET permissions = excluded.permissions
                    """,
                    (guild_id, role_id, new_permission_value),
                )
                conn.commit()
                conn.close()

                return redirect(url_for("manage_fakeperms", guild_id=guild_id))

            # Render the template with roles and permissions
            return render_template(
                "fakeperms.html",
                guild={"id": guild_id, "name": f"Guild {guild_id}"},  # Mock guild name
                roles=roles,
                permissions=permissions,
                current_role_perms=current_role_perms,
            )
        except Exception as e:
            logger.error(f"Error in FakePerms route: {e}")
            return jsonify({"error": "An error occurred."}), 500

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
