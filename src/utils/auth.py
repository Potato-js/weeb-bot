from flask import Blueprint, redirect, url_for
from flask_discord import DiscordOAuth2Session, requires_authorization

auth = Blueprint("auth", __name__)

# Initialize the Discord OAuth2 session
discord = DiscordOAuth2Session()


@auth.route("/login/")
def login():
    return discord.create_session()


@auth.route("/callback/")
def callback():
    discord.callback()
    return redirect(url_for("dashboard"))


@auth.route("/logout/")
@requires_authorization
def logout():
    discord.revoke()
    return redirect(url_for("home"))
