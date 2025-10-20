import mysql.connector
from argon2 import PasswordHasher, exceptions
import pyotp
import qrcode
import io
import base64
import json
import time
ph = PasswordHasher()

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="login",
        port=3306
    )

def VerifyLogin(email, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT user_id, user_password, username FROM user_auth WHERE email=%s",
            (email,)
        )
        user = cursor.fetchone()
        if not user:
            return False, 0, None
        db_password = user['user_password']
        try:
            ph.verify(db_password, password)
            if ph.check_needs_rehash(db_password):
                new_hash = ph.hash(password)
                cursor.execute(
                    "UPDATE user_auth SET user_password=%s WHERE user_id=%s",
                    (new_hash, user['user_id'])
                )
                conn.commit()
            return True, user['user_id'], user['username']
        except exceptions.VerifyMismatchError:
            return False, 1, None
    finally:
        cursor.close()
        conn.close()

def verify_password(user_id: int, password: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT user_password FROM user_auth WHERE user_id=%s",
            (user_id,)
        )
        user = cursor.fetchone()
        if not user:
            return False
        try:
            ph.verify(user['user_password'], password)
            return True
        except exceptions.VerifyMismatchError:
            return False
    finally:
        cursor.close()
        conn.close()

def Getuser_role(userID: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_role FROM user_auth WHERE user_id = %s", (userID,))
        result = cursor.fetchone()
        return result['user_role'] if result else ""
    finally:
        cursor.close()
        conn.close()

def is_email_valid(email: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT username FROM user_auth WHERE email = %s", (email,))
        result = cursor.fetchone()
        return True, result['username'] if result else False
    finally:
        cursor.close()
        conn.close()

def SaveRefreshToken(user_id: int, token_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO refresh_tokens (token_id, user_id) VALUES (%s, %s)",
            (token_id, user_id)
        )
        cursor.execute(
            "SELECT token_id FROM refresh_tokens WHERE user_id = %s ORDER BY created_at ASC",
            (user_id,)
        )
        tokens = [row[0] for row in cursor.fetchall()]
        if len(tokens) > 5:
            tokens_to_delete = tokens[:-5]
            placeholders = ",".join(["%s"] * len(tokens_to_delete))
            cursor.execute(
                f"DELETE FROM refresh_tokens WHERE token_id IN ({placeholders})",
                tokens_to_delete
            )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def CheckRefreshToken(user_id: int, token_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM refresh_tokens WHERE user_id = %s AND token_id = %s",
            (user_id, token_id)
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()

def LockRefreshToken(user_id: int, token_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM refresh_tokens WHERE user_id = %s AND token_id = %s",
            (user_id, token_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def LockRefreshTokens(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM refresh_tokens WHERE user_id = %s",
            (user_id,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def Adduser_role(user_identifier, new_user_role):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, user_role FROM user_auth WHERE user_id = %s", (user_identifier,))
        result = cursor.fetchone()
        if not result:
            return False, "User not found"
        user_id = result['user_id']
        user_role = result['user_role']
        role_list = user_role.split(",") if user_role else []
        if new_user_role in role_list:
            return False, "user_role already exists"
        role_list.append(new_user_role)
        cursor.execute(
            "UPDATE user_auth SET user_role=%s WHERE user_id=%s",
            (",".join(role_list), user_id)
        )
        conn.commit()
        return True, f"user_role '{new_user_role}' added to user '{user_identifier}'"
    finally:
        cursor.close()
        conn.close()

def DeleteUser(user_identifier, by_username=True):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if by_username:
            cursor.execute("SELECT user_id, username FROM user_auth WHERE username=%s", (user_identifier,))
        else:
            cursor.execute("SELECT user_id, username FROM user_auth WHERE user_id=%s", (user_identifier,))
        result = cursor.fetchone()
        if not result:
            return False, "User not found"
        user_id = result['user_id']
        username = result['username']
        cursor.execute("SELECT user_role FROM user_auth WHERE user_id=%s", (user_id,))
        role_result = cursor.fetchone()
        user_role = role_result['user_role'] if role_result else ""
        if "admin" in user_role.split(","):
            return False, "Cannot delete admin user"
        cursor.execute("DELETE FROM user_auth WHERE user_id=%s", (user_id,))
        conn.commit()
        return True, f"User '{username}' deleted successfully"
    finally:
        cursor.close()
        conn.close()

def GetUsername(userID: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT username FROM user_auth WHERE user_id=%s", (userID,))
        result = cursor.fetchone()
        return result['username'] if result else None
    finally:
        cursor.close()
        conn.close()

default_user_role = ["free_user"]

def CreateUser(email, password, username, user_role=None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_role is None:
        user_role = default_user_role
    user_role_str = ",".join(user_role)
    try:
        cursor.execute(
            "INSERT INTO user_auth (email, user_password, username, user_role) VALUES (%s, %s, %s, %s)",
            (email, password, username, user_role_str)
        )
        conn.commit()
        return {"success": True, "user_id": cursor.lastrowid}
    except mysql.connector.IntegrityError as e:
        msg = str(e.msg).lower()
        if "email" in msg:
            return {"success": False, "error": "Email already exists"}
        elif "username" in msg:
            return {"success": False, "error": "Username is already taken"}
        return {"success": False, "error": "Database integrity error"}
    finally:
        cursor.close()
        conn.close()

def check_permission(user_role: str, required_role: str = None, required_permission: str = None) -> bool:
    if required_role is None and required_permission is None:
        return False
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT role_index, role_permission FROM roles WHERE role_name=%s", (user_role,))
        user_data = cursor.fetchone()
        if not user_data:
            return False
        user_index = user_data['role_index']
        if required_role:
            cursor.execute("SELECT role_index FROM roles WHERE role_name=%s", (required_role,))
            req = cursor.fetchone()
            if not req or user_index > req['role_index']:
                return False
        if required_permission:
            cursor.execute("SELECT role_permission FROM roles WHERE role_index <= %s", (user_index,))
            roles = cursor.fetchall()
            for r in roles:
                permissions = json.loads(r['role_permission'])
                if permissions.get(required_permission, False):
                    return True
            return False
        return True
    finally:
        cursor.close()
        conn.close()

def username_taken(username):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM user_auth WHERE username=%s", (username,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()

def change_username(user_id: int, new_username: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM user_auth WHERE username=%s", (new_username,))
        if cursor.fetchone():
            return False, {"msg": "Username already taken"}, 409
        cursor.execute("UPDATE user_auth SET username=%s WHERE user_id=%s", (new_username, user_id))
        conn.commit()
        return True, {"msg": "Username changed successfully"}, 200
    finally:
        cursor.close()
        conn.close()

def change_email(user_id: int, new_email: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM user_auth WHERE email=%s", (new_email,))
        if cursor.fetchone():
            return False, {"msg": "Email already in use"}, 409
        cursor.execute("UPDATE user_auth SET email=%s WHERE user_id=%s", (new_email, user_id))
        conn.commit()
        return True, {"msg": "Email changed successfully"}, 200
    finally:
        cursor.close()
        conn.close()

def change_password(user_id: int, old_password: str, new_password: str, ignore_old: bool):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if not ignore_old:
            if not verify_password(user_id, old_password):
                return False, {"msg": "Current password is incorrect"}, 401
        hashed_new_password = ph.hash(new_password)
        cursor.execute(
            "UPDATE user_auth SET user_password=%s WHERE user_id=%s",
            (hashed_new_password, user_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return False, {"msg": "User not found"}, 404
        conn.commit()
        return True, {"msg": "Password changed successfully"}, 200
    finally:
        cursor.close()
        conn.close()

def activate_mfa(user_id: int, code: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT mfa_secret FROM user_auth WHERE user_id=%s", (user_id,))
        result = cursor.fetchone()
        if not result or not result['mfa_secret']:
            return False, {"msg": "No MFA setup found"}, 400
        totp = pyotp.TOTP(result['mfa_secret'])
        if totp.verify(code, valid_window=1):
            cursor.execute("UPDATE user_auth SET mfa_enabled=%s WHERE user_id=%s", (True, user_id))
            conn.commit()
            return True, {"msg": "MFA successfully enabled"}, 200
        return False, {"msg": "Invalid MFA code"}, 401
    finally:
        cursor.close()
        conn.close()

def check_mfa(user_id) -> bool:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT mfa_enabled FROM user_auth WHERE user_id=%s", (user_id,))
        result = cursor.fetchone()
        return bool(result and result.get('mfa_enabled', 0))
    finally:
        cursor.close()
        conn.close()

def init_mfa(user_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT mfa_secret FROM user_auth WHERE user_id=%s", (user_id,))
        result = cursor.fetchone()
        if not result or not result['mfa_secret']:
            secret = pyotp.random_base32()
        else:
            secret = result['mfa_secret']
        cursor.execute("UPDATE user_auth SET mfa_secret=%s, mfa_enabled=%s WHERE user_id=%s", (secret, False, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    username = GetUsername(user_id)
    uri = pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="MyApp")
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    return {"qr_code_data": f"data:image/png;base64,{img_b64}", "uri": uri}

def deactivate_mfa(user_id: int, password: str):
    if not verify_password(user_id, password):
        return False, {"msg": "Password is incorrect"}, 401
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE user_auth SET mfa_secret=%s, mfa_enabled=%s WHERE user_id=%s", (None, False, user_id))
        conn.commit()
        return True, {"msg": "MFA successfully disabled"}, 200
    finally:
        cursor.close()
        conn.close()

def verify_mfa(code: str, user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT mfa_secret FROM user_auth WHERE user_id=%s", (user_id,))
        result = cursor.fetchone()
        if not result or not result['mfa_secret']:
            return False
        totp = pyotp.TOTP(result['mfa_secret'])
        return totp.verify(str(code).strip(), valid_window=1)
    finally:
        cursor.close()
        conn.close()

def get_userid(email: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM user_auth WHERE email=%s", (email,))
        result = cursor.fetchone()
        if not result:
            return None
        return result.get('user_id')
    finally:
        cursor.close()
        conn.close()