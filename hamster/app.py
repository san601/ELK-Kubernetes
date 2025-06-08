#!/usr/bin/python3
from flask import Flask, make_response, request, render_template, render_template_string, redirect, abort
import db
import jwt
import os
import logging
from pythonjsonlogger import jsonlogger
from elasticapm.contrib.flask import ElasticAPM

app = Flask(__name__)

logger = logging.getLogger("flask-app")
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': os.environ.get('ELASTIC_APM_SERVICE_NAME', 'my-flask-app'),
    'SECRET_TOKEN': os.environ.get('ELASTIC_APM_SECRET_TOKEN', ''),
    'SERVER_URL': os.environ.get('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
    'ENVIRONMENT': os.environ.get('ELASTIC_APM_ENVIRONMENT', 'development'),
    'DEBUG': True
}
apm = ElasticAPM(app, logging=True)

try:
    with open("keys/private.pem", "r") as f:
        private_key = f.read()
    with open("keys/public.pem", "r") as f:
        public_key = f.read()
except FileNotFoundError:
    logger.error("Private or public key file not found. Ensure keys/private.pem and keys/public.pem exist.")
    exit(1)

@app.route('/')
def login_page():
    logger.info("Accessing login page")
    return render_template("login.html")

@app.route('/login', methods=["POST"])
def login():
    username, password = request.form["username"], request.form["password"]
    logger.info(f"Login attempt for user: {username}")
    if user_id := db.login(username, password):
        resp = make_response(redirect('game'))
        resp.set_cookie("session", get_jwt(user_id, username))
        logger.info(f"User {username} (ID: {user_id}) logged in successfully.")
        return resp
    else:
        logger.warning(f"Failed login attempt for user: {username}")
        return render_template("login.html", error=True)

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username, password = request.form["username"], request.form["password"]
        logger.info(f"Registration attempt for user: {username}")
        if db.register(username, password):
            resp = make_response(redirect('/'))
            logger.info(f"User {username} registered successfully.")
            return resp
        else:
            logger.warning(f"Failed registration for user: {username}")
            return render_template("register.html", error=True)
    else:
        return render_template("register.html")

@app.route('/logout', methods=["GET"])
def logout():
    resp = make_response(redirect('/'))
    resp.delete_cookie("session")
    logger.info("User logged out.")
    return resp

@app.route('/game')
def game():
    try:
        session = jwt.decode(request.cookies['session'], public_key, algorithms=['RS256'])
        user_id, username = int(session["user_id"]), session["username"]
        logger.info(f"User {username} accessing game page.")
    except Exception as e:
        logger.error(f"Session decode error or no session: {e}", exc_info=True)
        return make_response(redirect('/logout'))
    score = db.get_user_score(user_id)
    return render_template("game.html", score=score, username=username)

@app.route('/update_score', methods=["POST"])
def update_score():
    try:
        session = jwt.decode(request.cookies['session'], public_key, algorithms=['RS256'])
        user_id = int(session["user_id"])
    except Exception as e:
        logger.error(f"Unauthorized attempt to update score: {e}", exc_info=True)
        abort(401)
    data = request.get_json()
    score_to_add = data["score"]
    old_score = db.get_user_score(user_id)
    new_score = score_to_add + old_score
    db.update_user_score(user_id, new_score)
    logger.info(f"User ID {user_id} updated score. Added: {score_to_add}, New total: {new_score}")
    return "", 200

@app.route('/scoreboard', methods=["GET"])
def get_scoreboard():
    try:
        session = jwt.decode(request.cookies['session'], public_key, algorithms=['RS256'])
        user_id = int(session["user_id"])
        logger.info(f"User ID {user_id} accessing scoreboard.")
    except Exception as e:
        logger.error(f"Unauthorized attempt to access scoreboard: {e}", exc_info=True)
        abort(401)
    return render_template("scoreboard.html", score=db.get_scoreboard())

@app.route('/admin', methods=["GET"])
def admin():
    remote_addr = request.headers.get('X-Real-IP') or request.remote_addr
    logger.info(f"Admin page accessed from IP: {remote_addr}")
    return render_template("admin.html", users=db.get_users())

@app.route('/profile', methods=["GET"])
def get_profile():
    try:
        session = jwt.decode(request.cookies['session'], public_key, algorithms=['RS256'])
        user_id, username = int(session["user_id"]), session["username"]
        logger.info(f"User {username} accessing profile.")
    except Exception as e:
        logger.error(f"Session error accessing profile: {e}", exc_info=True)
        return make_response(redirect('/logout'))
    username_db, score, avatar, recovery = db.get_user_profile(user_id)
    return render_template("profile.html", username=username_db, score=score, avatar=avatar, recovery_code=recovery, user_id=user_id)

@app.route('/update_avatar', methods=['POST'])
def update_avatar():
    try:
        session = jwt.decode(request.cookies['session'], public_key, algorithms=['RS256'])
    except Exception as e:
        logger.error(f"Session error updating avatar: {e}", exc_info=True)
        return make_response(redirect('/logout'))
    form_id = request.form.get("id")
    avatar = request.form.get("avatar")
    db.update_avatar(form_id, avatar)
    logger.info(f"Avatar updated for user ID: {form_id}")
    username_db, score, avatar_db, recovery = db.get_user_profile(form_id)
    return render_template("profile.html", username=username_db, score=score, avatar=avatar_db, recovery_code=recovery, user_id=form_id)

@app.route('/update_recovery', methods=["POST"])
def update_recovery_code():
    try:
        session = jwt.decode(request.cookies['session'], public_key, algorithms=['RS256'])
        user_id, username = int(session["user_id"]), session["username"]
    except Exception as e:
        logger.error(f"Session error updating recovery code: {e}", exc_info=True)
        abort(401)
    recovery_code = request.form["recovery_code"]
    db.update_recovery_code(username, recovery_code)
    logger.info(f"Recovery code updated for user: {username}")
    return make_response(redirect('/profile'))

def get_jwt(user_id, username):
    return jwt.encode({"user_id": user_id, "username": username}, private_key, algorithm="RS256")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8888)
