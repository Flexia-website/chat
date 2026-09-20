import os
from flask import Flask, send_file, send_from_directory, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import sqlite3
import base64
import uuid
import threading
import time
import hashlib
import random
import json
from datetime import datetime, timedelta
from functools import wraps
from pywebpush import webpush, WebPushException

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'flexia123')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# VAPID keys for Web Push
VAPID_PUBLIC_KEY = os.environ.get(
    'VAPID_PUBLIC_KEY',
    'BM1-RUgnfm9zRS6Vx1khWAoVC8zOs1naoM-Pl6i3QX6iwDm2lMuXC_R73Bm1FY3gvQyD5UdW_HzhERryVhpKZLM'
)
VAPID_PRIVATE_KEY = os.environ.get(
    'VAPID_PRIVATE_KEY',
    'x5uL2TLfSJfq1TzMxYA2DsfOB6jijcpb9wrLo-opt8k'
)
VAPID_CLAIMS_EMAIL = os.environ.get('VAPID_CLAIMS_EMAIL', 'mailto:admin@example.com')

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = bool(DATABASE_URL)
SQLITE_PATH = 'flexia_chat.db'

# File upload
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Enable CORS and SocketIO
CORS(app)
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   logger=False, 
                   engineio_logger=False,
                   async_mode='eventlet',
                   ping_timeout=60,
                   ping_interval=25)

# Track connected admins and users
admin_devices = []
user_sockets = {}
user_rooms = {}
admin_sessions = {}

# Cache for users list (expire every 5 seconds)
users_cache = {'data': None, 'timestamp': 0}
CACHE_TTL = 5

class _CursorCompat:
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def execute(self, query, params=()):
        q = query.replace('?', '%s')
        q = q.replace('!= "Support"', "!= 'Support'")
        needs_id = q.strip().upper().startswith('INSERT INTO MESSAGES') and 'RETURNING' not in q.upper()
        if needs_id:
            q = q.rstrip().rstrip(';') + ' RETURNING id'
        self._cursor.execute(q, params)
        if needs_id:
            row = self._cursor.fetchone()
            self.lastrowid = row['id'] if row else None
        return self

    def executemany(self, query, seq_of_params):
        return self._cursor.executemany(query.replace('?', '%s'), seq_of_params)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def close(self):
        self._cursor.close()

class _ConnCompat:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _CursorCompat(self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor))

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

def get_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return _ConnCompat(conn)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 device_id TEXT UNIQUE NOT NULL,
                 username TEXT,
                 created_at TEXT,
                 last_active TEXT
             )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                 id INTEGER PRIMARY KEY,
                 device_id TEXT NOT NULL,
                 sender TEXT NOT NULL,
                 message TEXT NOT NULL,
                 type TEXT DEFAULT 'text',
                 is_admin BOOLEAN DEFAULT 0,
                 is_auto_reply BOOLEAN DEFAULT 0,
                 timestamp TEXT NOT NULL,
                 expires_at TEXT NOT NULL
             )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS admin_settings (
                 id INTEGER PRIMARY KEY,
                 setting_name TEXT UNIQUE NOT NULL,
                 setting_value TEXT
             )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                 id INTEGER PRIMARY KEY,
                 device_id TEXT,
                 endpoint TEXT UNIQUE,
                 p256dh TEXT,
                 auth TEXT
             )''')
    
    # Create indexes for fast queries
    c.execute('CREATE INDEX IF NOT EXISTS idx_device_id ON users(device_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_device ON messages(device_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_expires ON messages(expires_at)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_last_active ON users(last_active)')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/admin')
def admin():
    return send_file('admin.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    password = data.get('password', '')
    
    if password == app.config['ADMIN_PASSWORD']:
        session['authenticated'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Invalid password'}), 401

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ============================================================================
# SOCKETIO EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('admin_login')
def handle_admin_login(data):
    password = data.get('password', '')
    sid = request.sid
    
    if password == app.config['ADMIN_PASSWORD']:
        admin_sessions[sid] = {
            'authenticated': True,
            'device_id': f'admin-{sid}',
            'last_activity': datetime.now().isoformat()
        }
        emit('admin_authenticated', {'success': True})
        print(f'Admin authenticated: {sid}')
    else:
        emit('error', {'message': 'Invalid password'})

@socketio.on('admin_join')
def handle_admin_join(data=None):
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid].get('authenticated'):
        emit('error', {'message': 'Unauthorized'})
        return
    
    device_id = admin_sessions[sid].get('device_id')
    if device_id and device_id not in admin_devices:
        admin_devices.append(device_id)
    
    join_room('admin_room')
    emit('admin_room_joined', {'success': True})
    print(f'Admin joined room: {sid}')

@socketio.on('join')
def on_join(data):
    """User joins with IP-based persistent device_id"""
    device_id = data.get('device_id')
    username = data.get('username', 'Anonymous')
    
    if not device_id:
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        device_id = 'ip-' + hashlib.sha256(client_ip.encode()).hexdigest()[:16]
    
    sid = request.sid
    join_room(device_id)
    user_rooms[sid] = device_id
    
    if device_id not in user_sockets:
        user_sockets[device_id] = []
    user_sockets[device_id].append(sid)
    
    conn = get_db()
    c = conn.cursor()
    
    is_new_user = False
    c.execute('SELECT id FROM users WHERE device_id = ?', (device_id,))
    if c.fetchone():
        c.execute('UPDATE users SET last_active = ? WHERE device_id = ?',
                  (datetime.now().isoformat(), device_id))
    else:
        c.execute('INSERT INTO users (device_id, username, created_at, last_active) VALUES (?, ?, ?, ?)',
                  (device_id, username, datetime.now().isoformat(), datetime.now().isoformat()))
        is_new_user = True
    
    conn.commit()
    conn.close()
    
    # Check if first-time user
    c = get_db().cursor()
    c.execute('SELECT COUNT(*) as count FROM messages WHERE device_id = ? AND sender != "Support"', (device_id,))
    row = c.fetchone()
    message_count = row['count'] if row else 0
    
    emit('user_data', {
        'device_id': device_id,
        'username': username,
        'is_first_message': message_count == 0
    })
    
    # Notify admins of new user
    if is_new_user:
        socketio.emit('new_user_joined', {
            'device_id': device_id,
            'username': username,
            'timestamp': datetime.now().isoformat()
        }, room='admin_room')
        users_cache['timestamp'] = 0  # Invalidate cache
        print(f'🆕 New user: {device_id}')

@socketio.on('send_message')
def handle_send_message(data):
    """Handle user message"""
    device_id = data.get('device_id')
    message = data.get('message')
    msg_type = data.get('type', 'text')
    
    if not device_id or not message:
        emit('error', {'message': 'Missing data'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Store message
    timestamp = datetime.now().isoformat()
    expires_at = (datetime.now() + timedelta(days=2)).isoformat()
    
    c.execute('''INSERT INTO messages 
                 (device_id, sender, message, type, is_admin, timestamp, expires_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (device_id, 'User', message, msg_type, False, timestamp, expires_at))
    
    conn.commit()
    conn.close()
    
    message_data = {
        'device_id': device_id,
        'sender': 'User',
        'message': message,
        'type': msg_type,
        'timestamp': timestamp
    }
    
    # Send to user
    emit('receive_message', message_data, room=device_id)
    
    # Notify admin
    socketio.emit('new_user_message', message_data, room='admin_room')
    
    # Auto-reply logic (database controlled)
    c = get_db().cursor()
    c.execute('SELECT COUNT(*) as count FROM messages WHERE device_id = ? AND sender != "Support"', (device_id,))
    row = c.fetchone()
    message_count = row['count'] if row else 0
    
    if message_count == 1:
        socketio.start_background_task(send_auto_reply_delayed, device_id, 'first')
    elif message_count == 2:
        if msg_type == 'image':
            socketio.start_background_task(send_auto_reply_delayed, device_id, 'image')
        else:
            socketio.start_background_task(send_auto_reply_delayed, device_id, 'text')

@socketio.on('get_all_users')
def handle_get_all_users(data=None):
    """Get all users with caching"""
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid].get('authenticated'):
        emit('error', {'message': 'Unauthorized'})
        return
    
    # Check cache
    now_ts = time.time()
    if users_cache['data'] and (now_ts - users_cache['timestamp']) < CACHE_TTL:
        emit('users_list', users_cache['data'])
        return
    
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    # Fast query: only select needed columns
    c.execute('''SELECT device_id, username, created_at, last_active
                 FROM users
                 ORDER BY last_active DESC''', ())
    
    users = []
    for row in c.fetchall():
        device_id = row['device_id']
        last_active = datetime.fromisoformat(row['last_active']) if row['last_active'] else datetime.now()
        inactive_hours = (datetime.now() - last_active).total_seconds() / 3600
        
        # Count messages
        c.execute('SELECT COUNT(*) as count FROM messages WHERE device_id = ? AND expires_at > ?', 
                  (device_id, now))
        msg_row = c.fetchone()
        msg_count = msg_row['count'] if msg_row else 0
        
        # Last message
        c.execute('SELECT timestamp FROM messages WHERE device_id = ? AND expires_at > ? ORDER BY timestamp DESC LIMIT 1',
                  (device_id, now))
        last_msg = c.fetchone()
        last_message = last_msg['timestamp'] if last_msg else None
        
        is_connected = device_id in user_sockets and len(user_sockets[device_id]) > 0
        
        users.append({
            'device_id': device_id,
            'username': row['username'] or 'Anonymous',
            'created_at': row['created_at'],
            'last_active': row['last_active'],
            'last_message': last_message,
            'message_count': msg_count,
            'inactive_hours': round(inactive_hours, 1),
            'is_active': inactive_hours < 48,
            'is_connected': is_connected
        })
    
    conn.close()
    
    response = {
        'users': users,
        'total': len(users),
        'timestamp': datetime.now().isoformat(),
        'connected_users': len(user_rooms)
    }
    
    # Cache the response
    users_cache['data'] = response
    users_cache['timestamp'] = now_ts
    
    emit('users_list', response)
    print(f'Sent {len(users)} users (cached)')

@socketio.on('get_user_messages')
def handle_get_user_messages(data):
    """Get messages for specific user"""
    device_id = data.get('device_id')
    
    if not device_id:
        emit('error', {'message': 'Device ID required'})
        return
    
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid].get('authenticated'):
        emit('error', {'message': 'Unauthorized'})
        return
    
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    # Fetch all messages (they auto-expire in 2 days)
    c.execute('''SELECT id, device_id, sender, message, type, is_admin, is_auto_reply, timestamp 
                 FROM messages 
                 WHERE device_id = ? AND expires_at > ?
                 ORDER BY timestamp ASC''', (device_id, now))
    
    messages = [dict(row) for row in c.fetchall()]
    
    # Get username
    c.execute('SELECT username FROM users WHERE device_id = ?', (device_id,))
    user_row = c.fetchone()
    username = user_row['username'] if user_row else 'Anonymous'
    
    conn.close()
    
    emit('user_messages', {
        'device_id': device_id,
        'username': username,
        'messages': messages,
        'total': len(messages)
    })

@socketio.on('admin_send_message')
def handle_admin_send_message(data):
    """Admin sends message to user"""
    device_id = data.get('device_id')
    message = data.get('message')
    
    if not device_id or not message:
        emit('error', {'message': 'Missing data'})
        return
    
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid].get('authenticated'):
        emit('error', {'message': 'Unauthorized'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    expires_at = (datetime.now() + timedelta(days=2)).isoformat()
    
    c.execute('''INSERT INTO messages 
                 (device_id, sender, message, type, is_admin, timestamp, expires_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (device_id, 'Support', message, 'text', True, timestamp, expires_at))
    
    conn.commit()
    conn.close()
    
    message_data = {
        'device_id': device_id,
        'sender': 'Support',
        'message': message,
        'type': 'text',
        'is_admin': True,
        'timestamp': timestamp
    }
    
    # Send to user
    socketio.emit('receive_message', message_data, room=device_id)
    
    # Echo to admin
    emit('admin_message_sent', message_data)
    print(f'Admin sent message to {device_id}')

def send_auto_reply_delayed(device_id, reply_type):
    """Send auto-reply based on database settings"""
    time.sleep(2)  # Simulate typing delay
    
    conn = get_db()
    c = conn.cursor()
    
    # Fetch auto-reply message from settings
    c.execute('SELECT setting_value FROM admin_settings WHERE setting_name = ?', (f'auto_reply_{reply_type}',))
    row = c.fetchone()
    reply_message = row['setting_value'] if row else None
    
    if not reply_message:
        # Default messages
        defaults = {
            'first': 'Thanks for reaching out! We\'ll get back to you shortly.',
            'text': 'We appreciate your message!',
            'image': 'Thanks for sharing!'
        }
        reply_message = defaults.get(reply_type, 'Thank you!')
    
    timestamp = datetime.now().isoformat()
    expires_at = (datetime.now() + timedelta(days=2)).isoformat()
    
    c.execute('''INSERT INTO messages 
                 (device_id, sender, message, type, is_admin, is_auto_reply, timestamp, expires_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (device_id, 'Support', reply_message, 'text', True, True, timestamp, expires_at))
    
    conn.commit()
    conn.close()
    
    message_data = {
        'device_id': device_id,
        'sender': 'Support',
        'message': reply_message,
        'type': 'text',
        'is_auto_reply': True,
        'timestamp': timestamp
    }
    
    socketio.emit('receive_message', message_data, room=device_id)
    print(f'Auto-reply sent to {device_id}')

@socketio.on('get_my_messages')
def handle_get_my_messages(data):
    """Get user's own message history"""
    device_id = data.get('device_id')
    if not device_id:
        return
    
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    c.execute('''SELECT id, sender, message, type, is_admin, is_auto_reply, timestamp 
                 FROM messages 
                 WHERE device_id = ? AND expires_at > ?
                 ORDER BY timestamp ASC''', (device_id, now))
    
    messages = [dict(row) for row in c.fetchall()]
    conn.close()
    
    emit('my_messages', {'messages': messages})

@socketio.on('disconnect')
def handle_disconnect():
    """Clean up on disconnect"""
    sid = request.sid
    
    # Clean up admin
    if sid in admin_sessions:
        device_id = admin_sessions[sid].get('device_id')
        if device_id and device_id in admin_devices:
            admin_devices.remove(device_id)
        del admin_sessions[sid]
        print(f'Admin disconnected: {sid}')
    
    # Clean up user
    if sid in user_rooms:
        device_id = user_rooms[sid]
        if device_id in user_sockets:
            user_sockets[device_id].remove(sid)
            if not user_sockets[device_id]:
                del user_sockets[device_id]
        del user_rooms[sid]
        print(f'User disconnected: {sid}')

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
