"""
Flexia Merchant Chat — backend

Implements every route and Socket.IO event that index.html and admin.html
already call. Storage is SQLite by default; set DATABASE_URL to switch to
Postgres (used automatically by render.yaml once you add a database).
"""

import os
import re
import json
import time
import uuid
import base64
import sqlite3
import hashlib
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, session, abort, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

try:
    from pywebpush import webpush, WebPushException
    HAS_WEBPUSH = True
except ImportError:
    HAS_WEBPUSH = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL) and HAS_PSYCOPG2
SQLITE_PATH = os.path.join(BASE_DIR, "chat.db")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "123456")

VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "mailto:you@example.com")

USER_MESSAGE_RETENTION_DAYS = 2
USER_EXPIRATION_DAYS = 7

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = SECRET_KEY
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


# --------------------------------------------------------------------------
# Database layer — thin wrapper so the rest of the file doesn't care whether
# it's talking to SQLite or Postgres. Placeholders: SQLite uses '?', Postgres
# uses '%s', so `ph()` picks the right one and callers build queries with it.
# --------------------------------------------------------------------------

def get_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def ph():
    return "%s" if USE_POSTGRES else "?"


def init_db():
    conn = get_db()
    c = conn.cursor()

    if USE_POSTGRES:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                device_id TEXT PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                last_seen TIMESTAMP DEFAULT NOW(),
                is_connected BOOLEAN DEFAULT FALSE,
                reply_stage INTEGER DEFAULT 0
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                device_id TEXT,
                sender TEXT,
                message TEXT,
                type TEXT DEFAULT 'text',
                is_admin BOOLEAN DEFAULT FALSE,
                is_auto_reply BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS auto_replies (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                device_id TEXT PRIMARY KEY,
                subscription TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                device_id TEXT PRIMARY KEY,
                username TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                is_connected INTEGER DEFAULT 0,
                reply_stage INTEGER DEFAULT 0
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                sender TEXT,
                message TEXT,
                type TEXT DEFAULT 'text',
                is_admin INTEGER DEFAULT 0,
                is_auto_reply INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS auto_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                device_id TEXT PRIMARY KEY,
                subscription TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

    conn.commit()
    c.close()
    conn.close()


def row_to_dict(row):
    if row is None:
        return None
    if USE_POSTGRES:
        return dict(row)
    return dict(row)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def client_ip():
    # Respect reverse-proxy headers (Render sits behind one).
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or "unknown"


def device_id_for_ip(ip):
    # Deterministic device id derived from IP so a returning visitor from the
    # same address is treated as the same "device" without needing cookies.
    return "dev-" + hashlib.sha256(ip.encode()).hexdigest()[:16]


def now_iso():
    return datetime.utcnow().isoformat() + "Z"


def get_or_create_user(device_id, username="User"):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT * FROM users WHERE device_id = {ph()}", (device_id,))
    user = c.fetchone()
    if user is None:
        c.execute(
            f"INSERT INTO users (device_id, username, is_connected) VALUES ({ph()}, {ph()}, {ph()})",
            (device_id, username, True if USE_POSTGRES else 1),
        )
        conn.commit()
    else:
        c.execute(
            f"UPDATE users SET is_connected = {ph()}, last_seen = {'NOW()' if USE_POSTGRES else 'CURRENT_TIMESTAMP'} WHERE device_id = {ph()}",
            (True if USE_POSTGRES else 1, device_id),
        )
        conn.commit()
    c.close()
    conn.close()


def set_user_connected(device_id, connected):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        f"UPDATE users SET is_connected = {ph()}, last_seen = {'NOW()' if USE_POSTGRES else 'CURRENT_TIMESTAMP'} WHERE device_id = {ph()}",
        (True if connected else False if USE_POSTGRES else (1 if connected else 0), device_id),
    )
    conn.commit()
    c.close()
    conn.close()


def save_message(device_id, sender, message, msg_type="text", is_admin=False, is_auto_reply=False):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        f"""INSERT INTO messages (device_id, sender, message, type, is_admin, is_auto_reply)
            VALUES ({ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()})""",
        (device_id, sender, message, msg_type,
         (is_admin if USE_POSTGRES else int(is_admin)),
         (is_auto_reply if USE_POSTGRES else int(is_auto_reply))),
    )
    conn.commit()
    if USE_POSTGRES:
        c.execute("SELECT lastval() AS id")
        msg_id = c.fetchone()["id"]
        c.execute("SELECT timestamp FROM messages WHERE id = %s", (msg_id,))
        ts = c.fetchone()["timestamp"]
        timestamp = ts.isoformat() + "Z" if hasattr(ts, "isoformat") else str(ts)
    else:
        msg_id = c.lastrowid
        c.execute("SELECT timestamp FROM messages WHERE id = ?", (msg_id,))
        timestamp = c.fetchone()["timestamp"]
    c.close()
    conn.close()
    return {
        "id": msg_id,
        "device_id": device_id,
        "sender": sender,
        "message": message,
        "type": msg_type,
        "is_admin": bool(is_admin),
        "is_auto_reply": bool(is_auto_reply),
        "timestamp": timestamp,
    }


def get_messages_for_device(device_id, since_days=None):
    conn = get_db()
    c = conn.cursor()
    if since_days is not None:
        if USE_POSTGRES:
            c.execute(
                f"""SELECT * FROM messages WHERE device_id = {ph()}
                    AND timestamp >= NOW() - INTERVAL '{since_days} days'
                    ORDER BY timestamp ASC""",
                (device_id,),
            )
        else:
            cutoff = (datetime.utcnow() - timedelta(days=since_days)).isoformat()
            c.execute(
                f"SELECT * FROM messages WHERE device_id = {ph()} AND timestamp >= {ph()} ORDER BY timestamp ASC",
                (device_id, cutoff),
            )
    else:
        c.execute(f"SELECT * FROM messages WHERE device_id = {ph()} ORDER BY timestamp ASC", (device_id,))
    rows = [row_to_dict(r) for r in c.fetchall()]
    c.close()
    conn.close()
    for r in rows:
        r["is_admin"] = bool(r["is_admin"])
        r["is_auto_reply"] = bool(r["is_auto_reply"])
        if hasattr(r["timestamp"], "isoformat"):
            r["timestamp"] = r["timestamp"].isoformat() + "Z"
    return rows


def get_all_users_summary():
    conn = get_db()
    c = conn.cursor()
    if USE_POSTGRES:
        c.execute(
            """SELECT u.*, COUNT(m.id) AS message_count,
                      EXTRACT(EPOCH FROM (NOW() - u.last_seen)) / 3600.0 AS inactive_hours
               FROM users u
               LEFT JOIN messages m ON m.device_id = u.device_id
               WHERE u.created_at >= NOW() - INTERVAL '%s days'
               GROUP BY u.device_id
               ORDER BY u.last_seen DESC""" % USER_EXPIRATION_DAYS
        )
    else:
        cutoff = (datetime.utcnow() - timedelta(days=USER_EXPIRATION_DAYS)).isoformat()
        c.execute(
            """SELECT u.*, COUNT(m.id) AS message_count
               FROM users u
               LEFT JOIN messages m ON m.device_id = u.device_id
               WHERE u.created_at >= ?
               GROUP BY u.device_id
               ORDER BY u.last_seen DESC""",
            (cutoff,),
        )
    rows = [row_to_dict(r) for r in c.fetchall()]
    c.close()
    conn.close()

    result = []
    for r in rows:
        last_seen = r.get("last_seen")
        if isinstance(last_seen, str):
            try:
                last_seen_dt = datetime.fromisoformat(last_seen.replace("Z", ""))
            except ValueError:
                last_seen_dt = datetime.utcnow()
        elif hasattr(last_seen, "timestamp"):
            last_seen_dt = last_seen.replace(tzinfo=None)
        else:
            last_seen_dt = datetime.utcnow()

        inactive_hours = r.get("inactive_hours")
        if inactive_hours is None:
            inactive_hours = (datetime.utcnow() - last_seen_dt).total_seconds() / 3600.0

        result.append({
            "device_id": r["device_id"],
            "username": r.get("username") or "Anonymous",
            "is_connected": bool(r.get("is_connected")),
            "message_count": int(r.get("message_count") or 0),
            "inactive_hours": float(inactive_hours),
        })
    return result


def delete_user_data(device_id):
    conn = get_db()
    c = conn.cursor()
    # Clean up any uploaded image files belonging to this device before
    # wiping the DB rows, so we don't leak files on disk.
    c.execute(f"SELECT message FROM messages WHERE device_id = {ph()} AND type = {ph()}", (device_id, "image"))
    for row in c.fetchall():
        msg = row_to_dict(row)["message"]
        if msg and msg.startswith("/uploads/"):
            fname = msg.split("/uploads/")[-1]
            fpath = os.path.join(UPLOAD_DIR, fname)
            if os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    c.execute(f"DELETE FROM messages WHERE device_id = {ph()}", (device_id,))
    c.execute(f"DELETE FROM users WHERE device_id = {ph()}", (device_id,))
    c.execute(f"DELETE FROM push_subscriptions WHERE device_id = {ph()}", (device_id,))
    conn.commit()
    c.close()
    conn.close()


def get_setting(key, default=None):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT value FROM settings WHERE key = {ph()}", (key,))
    row = c.fetchone()
    c.close()
    conn.close()
    if row is None:
        return default
    return row_to_dict(row)["value"]


def set_setting(key, value):
    conn = get_db()
    c = conn.cursor()
    if USE_POSTGRES:
        c.execute(
            """INSERT INTO settings (key, value) VALUES (%s, %s)
               ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
            (key, value),
        )
    else:
        c.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
    conn.commit()
    c.close()
    conn.close()


def get_auto_replies():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM auto_replies ORDER BY id ASC")
    rows = [row_to_dict(r) for r in c.fetchall()]
    c.close()
    conn.close()
    return [{"id": r["id"], "text": r["text"]} for r in rows]


def add_auto_reply(text):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"INSERT INTO auto_replies (text) VALUES ({ph()})", (text,))
    conn.commit()
    c.close()
    conn.close()


def delete_auto_reply(reply_id):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"DELETE FROM auto_replies WHERE id = {ph()}", (reply_id,))
    conn.commit()
    deleted = c.rowcount > 0
    c.close()
    conn.close()
    return deleted


def save_push_subscription(device_id, subscription):
    conn = get_db()
    c = conn.cursor()
    sub_json = json.dumps(subscription)
    if USE_POSTGRES:
        c.execute(
            """INSERT INTO push_subscriptions (device_id, subscription) VALUES (%s, %s)
               ON CONFLICT (device_id) DO UPDATE SET subscription = EXCLUDED.subscription""",
            (device_id, sub_json),
        )
    else:
        c.execute(
            """INSERT INTO push_subscriptions (device_id, subscription) VALUES (?, ?)
               ON CONFLICT(device_id) DO UPDATE SET subscription = excluded.subscription""",
            (device_id, sub_json),
        )
    conn.commit()
    c.close()
    conn.close()


def get_all_push_subscriptions():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM push_subscriptions")
    rows = [row_to_dict(r) for r in c.fetchall()]
    c.close()
    conn.close()
    return rows


def send_push_notification(title, body):
    if not HAS_WEBPUSH or not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        return
    for sub_row in get_all_push_subscriptions():
        try:
            subscription = json.loads(sub_row["subscription"])
            webpush(
                subscription_info=subscription,
                data=json.dumps({"title": title, "body": body}),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIMS_EMAIL},
            )
        except WebPushException:
            pass
        except Exception:
            pass


# --------------------------------------------------------------------------
# Admin auth (HTTP session, used for the settings/push endpoints)
# --------------------------------------------------------------------------

def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            abort(401)
        return f(*args, **kwargs)
    return wrapper


# --------------------------------------------------------------------------
# HTTP routes
# --------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/admin-manifest.json")
def admin_manifest():
    manifest = {
        "name": "Flexia Admin",
        "short_name": "Admin",
        "start_url": "/admin/launch",
        "display": "standalone",
        "background_color": "#0E1013",
        "theme_color": "#0E1013",
        "icons": [
            {"src": "/static/Icons/admin-icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/Icons/admin-icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    return jsonify(manifest)


@app.route("/admin-sw.js")
def admin_service_worker():
    sw = """
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));

self.addEventListener('push', (event) => {
    let data = {};
    try { data = event.data ? event.data.json() : {}; } catch (e) {}
    const title = data.title || 'New message';
    const options = {
        body: data.body || '',
        icon: '/static/Icons/admin-icon-192.png',
        badge: '/static/Icons/admin-icon-192.png',
        tag: 'flexia-push-' + Date.now(),
        requireInteraction: true
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
            for (const client of clients) {
                if (client.url.includes('/admin') && 'focus' in client) return client.focus();
            }
            if (self.clients.openWindow) return self.clients.openWindow('/admin/launch');
        })
    );
});
"""
    return Response(sw, mimetype="application/javascript")


# Admin login via password in the URL, e.g. /123456
@app.route("/<password>")
def admin_login(password):
    # Only treat this as an admin login attempt if it matches the configured
    # password; otherwise fall through to a 404 so we don't create an open
    # route matching every possible path.
    if password == ADMIN_PASSWORD:
        session["is_admin"] = True
        session.permanent = True
        return send_from_directory(BASE_DIR, "admin.html")
    abort(404)


@app.route("/admin/launch")
def admin_launch():
    if not session.get("is_admin"):
        abort(404)
    return send_from_directory(BASE_DIR, "admin.html")


@app.route("/admin/vapid-public-key")
@require_admin
def vapid_public_key():
    return jsonify({"publicKey": VAPID_PUBLIC_KEY})


@app.route("/admin/push-subscribe", methods=["POST"])
@require_admin
def push_subscribe():
    data = request.get_json(force=True, silent=True) or {}
    subscription = data.get("subscription")
    device_id = data.get("device_id")
    if not subscription or not device_id:
        return jsonify({"success": False, "message": "Missing subscription or device_id"}), 400
    save_push_subscription(device_id, subscription)
    return jsonify({"success": True})


@app.route("/admin/settings", methods=["POST"])
@require_admin
def admin_settings():
    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action")

    if action == "get_replies":
        return jsonify({"replies": get_auto_replies()})

    if action == "add_reply":
        text = (data.get("reply_text") or "").strip()
        if not text:
            return jsonify({"success": False, "message": "Reply text cannot be empty"}), 400
        add_auto_reply(text)
        return jsonify({"success": True})

    if action == "delete_reply":
        reply_id = data.get("reply_id")
        ok = delete_auto_reply(reply_id)
        return jsonify({"success": ok})

    if action == "get_second_replies":
        text = get_setting("second_reply_text", "")
        image = get_setting("second_reply_image", "")
        return jsonify({"text": text, "image": image})

    if action == "set_second_reply":
        stage = data.get("stage")
        text = (data.get("reply_text") or "").strip()
        if not text:
            return jsonify({"success": False, "message": "Reply text cannot be empty"}), 400
        if stage == "text":
            set_setting("second_reply_text", text)
        elif stage == "image":
            set_setting("second_reply_image", text)
        else:
            return jsonify({"success": False, "message": "Unknown stage"}), 400
        return jsonify({"success": True})

    return jsonify({"success": False, "message": "Unknown action"}), 400


# --------------------------------------------------------------------------
# Socket.IO — track admin sockets and user socket->device mapping in memory
# --------------------------------------------------------------------------

# sid -> device_id, for users
sid_to_device = {}
# device_id -> set of sids (a user could have multiple tabs open)
device_to_sids = {}
# sid -> True for authenticated admin sockets
admin_sids = set()


def is_valid_image_data_url(data_url):
    return isinstance(data_url, str) and re.match(r"^data:image/(png|jpe?g|gif|webp);base64,", data_url)


def save_image_from_data_url(data_url):
    match = re.match(r"^data:image/(png|jpe?g|gif|webp);base64,(.+)$", data_url, re.DOTALL)
    if not match:
        return None
    ext = match.group(1).replace("jpeg", "jpg")
    payload = match.group(2)
    try:
        raw = base64.b64decode(payload)
    except Exception:
        return None
    if len(raw) > 8 * 1024 * 1024:  # 8MB cap
        return None
    filename = f"{uuid.uuid4()}.{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(raw)
    return f"/uploads/{filename}"


@socketio.on("connect")
def handle_connect():
    pass


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    admin_sids.discard(sid)
    device_id = sid_to_device.pop(sid, None)
    if device_id:
        sids = device_to_sids.get(device_id)
        if sids:
            sids.discard(sid)
            if not sids:
                device_to_sids.pop(device_id, None)
                set_user_connected(device_id, False)


@socketio.on("join")
def handle_join(data):
    ip = client_ip()
    device_id = device_id_for_ip(ip)
    username = (data or {}).get("username") or "User"

    sid_to_device[request.sid] = device_id
    device_to_sids.setdefault(device_id, set()).add(request.sid)
    join_room(device_id)

    get_or_create_user(device_id, username)

    emit("user_data", {"device_id": device_id})

    # Notify admins a (possibly new) visitor connected.
    emit("new_user_joined", {"device_id": device_id, "username": username}, room="admins")


@socketio.on("get_my_messages")
def handle_get_my_messages(data):
    device_id = (data or {}).get("device_id")
    if not device_id:
        return
    messages = get_messages_for_device(device_id, since_days=USER_MESSAGE_RETENTION_DAYS)
    emit("my_messages", {"device_id": device_id, "messages": messages})


@socketio.on("send_message")
def handle_send_message(data):
    device_id = (data or {}).get("device_id")
    message = (data or {}).get("message", "").strip()
    sender = (data or {}).get("sender", "User")
    if not device_id or not message:
        emit("error", {"message": "Message cannot be empty"})
        return

    saved = save_message(device_id, sender, message, msg_type="text", is_admin=False)
    emit("receive_message", saved, room=device_id)
    emit("new_user_message", saved, room="admins")

    send_push_notification("New message", f"{sender}: {message[:100]}")

    # Auto-reply logic: first-ever inbound message from a device triggers
    # a random configured auto-reply; a *second* inbound message (after the
    # visitor has already gotten one auto-reply) triggers the admin's
    # configured "second reply" (text + optional image), a common pattern
    # for a lightweight canned-response funnel before a human takes over.
    conn = get_db()
    c = conn.cursor()
    c.execute(
        f"SELECT COUNT(*) AS cnt FROM messages WHERE device_id = {ph()} AND is_admin = {ph()}",
        (device_id, False if USE_POSTGRES else 0),
    )
    inbound_count = row_to_dict(c.fetchone())["cnt"]
    c.close()
    conn.close()

    if inbound_count == 1:
        replies = get_auto_replies()
        if replies:
            import random
            reply_text = random.choice(replies)["text"]
            auto = save_message(device_id, "Support", reply_text, msg_type="text", is_admin=True, is_auto_reply=True)
            socketio.sleep(1)
            emit("receive_message", auto, room=device_id)
            emit("new_user_message", auto, room="admins")
    elif inbound_count == 2:
        second_text = get_setting("second_reply_text", "")
        second_image = get_setting("second_reply_image", "")
        if second_text:
            auto = save_message(device_id, "Support", second_text, msg_type="text", is_admin=True, is_auto_reply=True)
            socketio.sleep(1)
            emit("receive_message", auto, room=device_id)
            emit("new_user_message", auto, room="admins")
        if second_image:
            auto_img = save_message(device_id, "Support", second_image, msg_type="image", is_admin=True, is_auto_reply=True)
            socketio.sleep(0.5)
            emit("receive_message", auto_img, room=device_id)
            emit("new_user_message", auto_img, room="admins")


@socketio.on("upload_image")
def handle_upload_image(data):
    device_id = (data or {}).get("device_id")
    image_data = (data or {}).get("image_data")
    is_admin = bool((data or {}).get("is_admin"))

    if not device_id or not is_valid_image_data_url(image_data):
        emit("error", {"message": "Invalid image"})
        return

    url = save_image_from_data_url(image_data)
    if not url:
        emit("error", {"message": "Could not process image (too large or invalid format)"})
        return

    sender = "Support" if is_admin else "User"
    saved = save_message(device_id, sender, url, msg_type="image", is_admin=is_admin)

    emit("receive_message", saved, room=device_id)
    if is_admin:
        emit("admin_message_sent", saved, room="admins")
    else:
        emit("new_user_message", saved, room="admins")
        send_push_notification("New image", f"{sender} sent an image")


@socketio.on("heartbeat")
def handle_heartbeat(data):
    device_id = (data or {}).get("device_id")
    if device_id:
        set_user_connected(device_id, True)
    emit("heartbeat_ack")


@socketio.on("typing")
def handle_typing(data):
    device_id = (data or {}).get("device_id") or sid_to_device.get(request.sid)
    if device_id:
        emit("typing", {"device_id": device_id}, room="admins")


@socketio.on("stop_typing")
def handle_stop_typing(data):
    device_id = (data or {}).get("device_id") or sid_to_device.get(request.sid)
    if device_id:
        emit("stop_typing", {"device_id": device_id}, room="admins")


# ----- Admin-side events -----

@socketio.on("admin_auth")
def handle_admin_auth(data):
    password = (data or {}).get("password")
    if password == ADMIN_PASSWORD:
        admin_sids.add(request.sid)
        emit("admin_auth_response", {"success": True})
    else:
        emit("admin_auth_response", {"success": False})


@socketio.on("admin_join")
def handle_admin_join(data):
    if request.sid not in admin_sids:
        emit("admin_auth_response", {"success": False})
        return
    join_room("admins")
    emit("admin_room_joined")


@socketio.on("get_all_users")
def handle_get_all_users(data):
    if request.sid not in admin_sids:
        return
    emit("users_list", {"users": get_all_users_summary()})


@socketio.on("get_user_messages")
def handle_get_user_messages(data):
    if request.sid not in admin_sids:
        return
    device_id = (data or {}).get("device_id")
    if not device_id:
        return
    messages = get_messages_for_device(device_id)
    emit("user_messages", {"device_id": device_id, "messages": messages})


@socketio.on("admin_send_message")
def handle_admin_send_message(data):
    if request.sid not in admin_sids:
        return
    device_id = (data or {}).get("device_id")
    message = (data or {}).get("message", "").strip()
    if not device_id or not message:
        return
    saved = save_message(device_id, "Support", message, msg_type="text", is_admin=True)
    emit("receive_message", saved, room=device_id)
    emit("admin_message_sent", saved, room="admins")


@socketio.on("admin_typing")
def handle_admin_typing(data):
    if request.sid not in admin_sids:
        return
    device_id = (data or {}).get("device_id")
    if device_id:
        emit("typing", {"device_id": device_id}, room=device_id)


@socketio.on("admin_stop_typing")
def handle_admin_stop_typing(data):
    if request.sid not in admin_sids:
        return
    device_id = (data or {}).get("device_id")
    if device_id:
        emit("stop_typing", {"device_id": device_id}, room=device_id)


@socketio.on("delete_user")
def handle_delete_user(data):
    if request.sid not in admin_sids:
        return
    device_id = (data or {}).get("device_id")
    if not device_id:
        return
    delete_user_data(device_id)
    emit("user_deleted", {"device_id": device_id}, room="admins")
    emit("user_deleted", {}, room=device_id)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
