from flask import Flask, request, jsonify, g, render_template, make_response, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sessions import login, verify_access_token, refresh_access_token, register, Getuser_role, logout, logout_all, generate_temp_mfa_token, verify_temp_mfa_token, GenerateSession, CreateRefreshToken
from DBManager import Adduser_role, DeleteUser, change_username, change_email, change_password, activate_mfa, init_mfa, check_mfa, verify_mfa, verify_password, username_taken, deactivate_mfa, is_email_valid, get_userid
from antyBot import generate_captcha
from functools import wraps
import hashlib
import hmac
import secrets
import datetime
from redis import Redis
from email_api import send_password_reset
from functools import wraps
import random

app = Flask(__name__)

r = Redis(host='localhost', port=6379, db=3)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/0",
    app=app,
    default_limits=["120 per minute"]
)

SECRET_KEY = "secret"

def set_tokens_response(resp, access_token=None, refresh_token=None,
                        access_exp=30*60, refresh_exp=7*24*60*60,
                        path='/', domain=None):
    resp = make_response(resp)

    if access_token:
        resp.set_cookie(
            "access_token",
            value=access_token,
            httponly=True,
            secure=False,          # -> True w produkcji
            samesite="Strict",     
            max_age=access_exp,
            path=path,
            domain=domain
        )
    if refresh_token:
        resp.set_cookie(
            "refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,          # -> True w produkcji
            samesite="Strict",
            max_age=refresh_exp,
            path=path,
            domain=domain
        )
    return resp

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        access_token = request.cookies.get("access_token")
        payload, status = verify_access_token(access_token) if access_token else (None, 401)

        if status == 200:
            g.user = payload
            return f(*args, **kwargs)

        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            return redirect(url_for('unauthorized', msg="missing_refresh_token"))

        new_access, expired, refresh, new_refresh_token = refresh_access_token(refresh_token)
        if expired:
            return redirect(url_for('unauthorized', msg="session_expired"))
        if not new_access:
            return redirect(url_for('unauthorized', msg="invalid_refresh_token"))

        payload, status = verify_access_token(new_access)
        if status != 200:
            return redirect(url_for('unauthorized', msg="invalid_access_token"))

        g.user = payload
        g.new_access_token = new_access

        response = make_response(f(*args, **kwargs))

        if refresh:

            response = set_tokens_response(response, access_token=new_access, refresh_token=new_refresh_token)
            print("x")
        else:
            response = set_tokens_response(response, access_token=new_access)

        return response
    return decorated


@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/mfa")
def mfa():
    return render_template("mfa.html")

@app.route("/dashboard")
@require_auth
def dashboard():
    return render_template("dashboard.html")

@app.route("/mfa_activation")
@require_auth
def mfa_activ():
    return render_template("mfa_activation.html")

@app.route("/settings")
@require_auth
def settings():
    return render_template("settings.html")

@app.route('/unauthorized')
def unauthorized():
    msg = request.args.get('msg', 'unknown')
    messages = {
        "missing_access_token": "Missing session token. Please log in again.",
        "missing_refresh_token": "Missing session token. Please log in again.",
        "invalid_refresh_token": "Session token is invalid or expired.",
        "invalid_access_token": "Failed to verify session token.",
        "session_expired": "Session Expired.",
        "unknown": "Unknown reason for redirection."
    }
    user_msg = messages.get(msg, messages["unknown"])
    return render_template("unauthorized.html", message=user_msg)

@app.route('/check')
def check():
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    if access_token:
        payload, status = verify_access_token(access_token)
        if status == 200:
            return jsonify({"msg": "Access granted", "user": payload.get("user_id")}), 200

    if refresh_token:
        new_access = refresh_access_token(refresh_token)
        if new_access:
            payload, status = verify_access_token(new_access)
            if status == 200:
                return jsonify({"msg": "Access granted (token refreshed)", "user_id": payload.get("user_id")}), 200

    return jsonify({"msg": "Forbidden"}), 403

@app.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login_route():
    data = request.json
    if not data:
        return jsonify({"msg": "No data"}), 400

    user_data = f"{data.get('email')}{data.get('password')}{data.get('score')}"
    if hashlib.sha256(user_data.encode()).hexdigest() != data.get("hash"):
        return jsonify({"msg": "Data integrity check failed"}), 400

    if data.get("score") is None:
        return jsonify({"msg": "No score"}), 400

    captcha_verified = False
    if data.get("answer") and data.get("captcha_answer"):
        expected_hmac = hmac.new(SECRET_KEY.encode(), str(data.get("answer")).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_hmac, data.get("captcha_answer")):
            return jsonify({"msg": "Captcha answer is incorrect"}), 403
        captcha_verified = True

    if ((data.get("score") > 70) and not captcha_verified) or random.randint(1, 5) == 1:
        answer, img = generate_captcha()
        captcha_hmac = hmac.new(SECRET_KEY.encode(), str(answer).encode(), hashlib.sha256).hexdigest()
        return jsonify({
            "captcha_required": True,
            "captcha_img": img,
            "captcha_answer": captcha_hmac
        }), 403

    if(len(data.get("email")) > 32 or len(data.get("password")) > 64):
        return jsonify({"msg": "Input too long"}), 400

    result = login(data.get("email"), data.get("password"))
    errortext = result.get('error') or ""
    if len(errortext) > 1:
        return jsonify({"msg": errortext}), 403

    if result.get('access_token') or result.get('refresh_token'):
        userid = result.get('user_id')
        if check_mfa(userid):
            response = generate_temp_mfa_token(userid)
            return jsonify({"temp_token": response, "mfa_required": True})

        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")
        if not access_token or not refresh_token:
            return jsonify({"msg": "Tokens not generated"}), 401

        resp = make_response(jsonify({"mfa_required": False}))
        resp = set_tokens_response(resp, access_token, refresh_token)
        return resp, 200

    return jsonify({"msg": "Incorrect email or password"}), 401

@app.route("/login_mfa", methods=["POST"])
@limiter.limit("8 per minute")
def mfa_login_route():
    data = request.json
    if not data:
        return jsonify({"msg": "No data"}), 400
    code = data.get('code')
    token = data.get('temp_token')
    valid, payload = verify_temp_mfa_token(token)
    if not valid:
        return jsonify({"msg": "You have to log in again"}), 403

    if code is None or token is None:
        return jsonify({"msg": "Missing code or token"}), 400

    if payload.get('mfa_required'):
        if verify_mfa(code, payload.get('user_id')):
            access_token, refresh_token = GenerateSession(payload.get('user_id'))
            if not access_token or not refresh_token:
                return jsonify({"msg": "Tokens not generated"}), 401
            resp = make_response(jsonify({"mfa_required": False}))
            resp = set_tokens_response(resp, access_token, refresh_token)
            return resp, 200
        else:
            return jsonify({"msg": "Incorrect code"}), 400
    else:
        return jsonify({"msg": "Error"}), 401

def dynamic_register_limit():
    username = request.json.get("username") if request.json else ""
    if username and username_taken(username):
        return "5 per 5 minutes"
    return "3 per 5 minutes"

@app.route("/register", methods=["POST"])
@limiter.limit(dynamic_register_limit)
def register_route():
    data = request.json
    if not data:
        return jsonify({"msg": "No data provided"}), 400
    if(len(data.get("email")) > 32 or len(data.get("password")) > 64):
        return jsonify({"msg": "Input too long"}), 400

    email = data.get("email")
    username = data.get("username")
    password = data.get("password")

    user_data = f"{email}{username}{password}{data.get('score')}"
    if hashlib.sha256(user_data.encode()).hexdigest() != data.get("hash"):
        return jsonify({"msg": "Data integrity check failed"}), 400

    if data.get("score") is None:
        return jsonify({"msg": "No score"}), 400

    captcha_verified = False
    if data.get("answer") and data.get("captcha_answer"):
        expected_hmac = hmac.new(SECRET_KEY.encode(), str(data.get("answer")).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_hmac, data.get("captcha_answer")):
            return jsonify({"msg": "Captcha answer is incorrect"}), 403
        captcha_verified = True

    if ((data.get("score") > 70) and not captcha_verified) or random.randint(1, 5) == 1:
        answer, img = generate_captcha()
        captcha_hmac = hmac.new(SECRET_KEY.encode(), str(answer).encode(), hashlib.sha256).hexdigest()
        return jsonify({
            "captcha_required": True,
            "captcha_img": img,
            "captcha_answer": captcha_hmac
        }), 403

    if not email or not username or not password:
        return jsonify({"msg": "Missing fields"}), 400

    result = register(email, password, username)
    errortext = result.get('error') or ""
    if len(errortext) > 1:
        return jsonify({"msg": errortext}), 403

    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")
    resp = set_tokens_response(access_token, refresh_token)
    return resp, 201

@app.route("/logout", methods=["POST"])
@require_auth
def logout_route():
    rt = request.cookies.get("refresh_token")
    logout(rt)

    resp = make_response(jsonify({"msg": "Logged out"}))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.set_cookie("access_token", "", expires=0, httponly=True, samesite='Strict')
    resp.set_cookie("refresh_token", "", expires=0, httponly=True, samesite='Strict')
    return resp, 200

@app.route("/logout_all", methods=["POST"])
@require_auth
def logout_all_route():
    rt = request.cookies.get("refresh_token")
    logout_all(rt)

    resp = make_response(jsonify({"msg": "Logged out"}))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.set_cookie("access_token", "", expires=0, httponly=True, samesite='Strict')
    resp.set_cookie("refresh_token", "", expires=0, httponly=True, samesite='Strict')
    return resp, 200

@app.route("/change_username", methods=["POST"])
@limiter.limit("4 per minute")
@require_auth
def change_username_route():
    userid = g.user.get("user_id")
    data = request.json
    username = data.get("new_username")
    succesfull, msg, status = change_username(userid, username)
    return jsonify(msg), status

@app.route("/change_email", methods=["POST"])
@limiter.limit("2 per minute")
@require_auth
def change_email_route():
    userid = g.user.get("user_id")
    data = request.json
    username = data["new_email"]
    succesfull, msg, status = change_email(userid, username)
    return jsonify({"msg": msg}), status

@app.route("/change_password", methods=["POST"])
@limiter.limit("5 per minute")
@require_auth
def change_password_route():
    userid = g.user.get("user_id")
    data = request.json
    password = data.get("password")
    new_password = data.get("new_password")
    succesfull, msg, status = change_password(userid, password, new_password, False)
    return jsonify(msg), status

@app.route("/init_mfa", methods=["POST"])
@limiter.limit("5 per minute")
@require_auth
def init_mfa_route():
    user_id = g.user.get("user_id")
    if check_mfa(user_id):
        return jsonify({"mfa": True}), 400
    if not user_id:
        return jsonify({"msg": "Missing user_id"}), 400
    result = init_mfa(user_id)
    return jsonify({
        "qr_code_data": result["qr_code_data"]
    })

@app.route("/verify_mfa", methods=["POST"])
@limiter.limit("5 per minute")
@require_auth
def verify_mfa_route():
    data = request.get_json()
    user_id = g.user.get("user_id")
    code = data.get("code")
    if not user_id or not code:
        return jsonify({"msg": "Missing user_id or code"}), 400
    verified, result, status_code = activate_mfa(user_id, code)
    return jsonify(result), status_code

@app.route("/activate_mfa", methods=["POST"])
@limiter.limit("10 per minute")
@require_auth
def activate_mfa_route():
    try:
        data = request.get_json()
        user_id = g.user.get("user_id")
        code = data.get("code")
        password = data.get("password")
        if not user_id or not code or not password:
            return jsonify({"msg": "Missing user_id or code"}), 400
        if verify_password(user_id, password) == False:
            return jsonify({"msg": "Invalid password"}), 403
        verified, result, status_code = activate_mfa(user_id, code)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"msg": f"Server error: {str(e)}"}), 500

@app.route("/deactivate_mfa", methods=["POST"])
@limiter.limit("5 per minute")
@require_auth
def deactivate_mfa_route():
    try:
        data = request.get_json()
        user_id = g.user.get("user_id")
        password = data.get("password")
        if not user_id or not password:
            return jsonify({"msg": "Missing user_id or password"}), 400
        success, result, status_code = deactivate_mfa(user_id, password)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@app.route("/get_mfa", methods=["POST"])
@limiter.limit("10 per minute")
@require_auth
def get_mfa_route():
    try:
        user_id = g.user.get("user_id")
        if not user_id:
            return jsonify({"msg": "Missing user_id"}), 400
        result = check_mfa(user_id)
        return jsonify({"mfa": result} if result else result), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@app.route("/request-reset", methods=["POST"])
def request_reset():
    data = request.get_json()
    email = data.get("email") if data else None
    if not email:
        return jsonify({"msg": "Missing email"}), 400

    valid, username = is_email_valid(hashlib.sha256(email.encode()).hexdigest())
    if not valid:
        return jsonify({"msg": "If this email exists, you will get a reset link."}), 200
    created = False
    while not created:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        key = f"pwdreset:{token_hash}"
        created = r.set(key, email, ex=900, nx=True)  

    reset_link, code = url_for("reset_password", token=raw_token, _external=True)
    if code != 200:
        return jsonify({"msg": "Error generating reset link"}), 500
    send_password_reset(email, reset_link, user_name=username)

    return jsonify({"msg": "If this email exists, you will get a reset link."}), 200

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "GET":
        token = request.args.get("token")
        if not token:
            return redirect("/")
        return render_template("password_reset.html", token=token)

    data = request.get_json()
    token = data.get("token")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not token or not new_password or not confirm_password:
        return "Missing token or password", 400
    if new_password != confirm_password:
        return "Passwords do not match", 400

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    redis_key = f"pwdreset:{token_hash}"
    email = r.get(redis_key)
    if not email:
        return "Token invalid or expired", 400
    uid = get_userid(hashlib.sha256(email).hexdigest())
    if uid is None:
        return "Token invalid or expired", 400
    r.delete(redis_key)  
    success, message, code = change_password(uid, "", new_password, True)
    return message, code


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
