import os
from flask import Flask, send_file, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import sqlite3
import base64
import uuid
import threading
import time
import hashlib
import random
from datetime import datetime, timedelta
from functools import wraps

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'flexia123')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# File upload configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Enable CORS and SocketIO
CORS(app)
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   logger=True, 
                   engineio_logger=True,
                   async_mode='eventlet')

# Database setup
def init_db():
    conn = sqlite3.connect('flexia_chat.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT UNIQUE NOT NULL,
        username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Messages table with 2-day expiration
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        sender TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'text',
        is_admin BOOLEAN DEFAULT 0,
        is_auto_reply BOOLEAN DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP DEFAULT (datetime('now', '+2 days')),
        FOREIGN KEY (device_id) REFERENCES users(device_id) ON DELETE CASCADE
    )''')
    
    # Files table with 2-day expiration
    c.execute('''CREATE TABLE IF NOT EXISTS uploaded_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP DEFAULT (datetime('now', '+2 days')),
        FOREIGN KEY (device_id) REFERENCES users(device_id) ON DELETE CASCADE
    )''')
    
    # Auto-reply settings
    c.execute('''CREATE TABLE IF NOT EXISTS auto_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reply_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create indexes
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_device_id ON messages(device_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_expires ON messages(expires_at)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_files_expires ON uploaded_files(expires_at)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)')
    
    conn.commit()
    conn.close()

init_db()

# Helper functions
def get_db():
    conn = sqlite3.connect('flexia_chat.db')
    conn.row_factory = sqlite3.Row
    return conn

def update_user_activity(device_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET last_active = ? WHERE device_id = ?', 
              (datetime.now().isoformat(), device_id))
    conn.commit()
    conn.close()

# In-memory storage for sessions
admin_sessions = {}
user_rooms = {}
user_sockets = {}  # device_id -> [socket_ids]
admin_sockets = []  # List of admin socket IDs
admin_devices = set()  # Track which devices have accessed admin panel

def cleanup_expired_data():
    """Delete all messages and files older than 2 days"""
    conn = get_db()
    c = conn.cursor()
    
    deleted_messages = 0
    deleted_files = 0
    deleted_users = 0
    
    try:
        now = datetime.now().isoformat()
        
        c.execute('DELETE FROM messages WHERE expires_at < ?', (now,))
        deleted_messages = c.rowcount
        
        c.execute('SELECT filepath FROM uploaded_files WHERE expires_at < ?', (now,))
        expired_files = c.fetchall()
        
        for file_row in expired_files:
            filepath = file_row[0]
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    deleted_files += 1
                except Exception as e:
                    print(f"❌ Error deleting file: {e}")
        
        c.execute('DELETE FROM uploaded_files WHERE expires_at < ?', (now,))
        
        cutoff_3days = (datetime.now() - timedelta(days=3)).isoformat()
        c.execute('''DELETE FROM users 
                     WHERE last_active < ? 
                     AND device_id NOT IN (
                         SELECT DISTINCT device_id FROM messages
                     )''', (cutoff_3days,))
        deleted_users = c.rowcount
        
        conn.commit()
        
        if deleted_messages > 0 or deleted_files > 0 or deleted_users > 0:
            print(f"🗑️ Cleanup: {deleted_messages} messages, {deleted_files} files, {deleted_users} users deleted")
        
        return {
            'messages': deleted_messages,
            'files': deleted_files,
            'users': deleted_users
        }
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return {'error': str(e)}
    finally:
        conn.close()

def run_cleanup_scheduler():
    """Run cleanup every hour"""
    while True:
        time.sleep(3600)
        try:
            cleanup_expired_data()
        except Exception as e:
            print(f"❌ Cleanup scheduler error: {e}")

cleanup_thread = threading.Thread(target=run_cleanup_scheduler, daemon=True)
cleanup_thread.start()

def get_auto_reply():
    """Get a random auto-reply"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT reply_text FROM auto_replies ORDER BY RANDOM() LIMIT 1')
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    return "Thank you for reaching out! We'll get back to you shortly."

def send_auto_reply(device_id, message_type='first'):
    """Send automatic reply based on message type"""
    if message_type == 'first':
        reply_text = get_auto_reply()
    elif message_type == 'image':
        reply_text = "Please wait while I review"
    elif message_type == 'text':
        reply_text = "I'll get back to you soon"
    else:
        return None
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        message_data = {
            'device_id': device_id,
            'sender': 'Support',
            'message': reply_text,
            'type': 'text',
            'is_admin': True,
            'is_auto_reply': True,
            'timestamp': datetime.now().isoformat()
        }
        
        c.execute('''INSERT INTO messages 
                     (device_id, sender, message, type, is_admin, is_auto_reply, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (device_id, 'Support', reply_text, 'text', True, True, message_data['timestamp']))
        
        conn.commit()
        
        # Emit to user
        if device_id in user_sockets:
            socketio.emit('receive_message', message_data, room=device_id)
        
        return message_data
        
    except Exception as e:
        print(f"❌ Error sending auto-reply: {e}")
    finally:
        conn.close()

# HTTP Routes
@app.route('/')
def index():
    """Serve the user chat interface"""
    try:
        return send_file('index.html')
    except:
        return '''
        <h1>Flexia Merchant Chat</h1>
        <p>Chat interface loading...</p>
        '''

@app.route('/<admin_password>')
def admin_access(admin_password):
    """Access admin panel with password in URL"""
    if admin_password == app.config['ADMIN_PASSWORD']:
        session['admin_logged_in'] = True
        session.permanent = True
        try:
            return send_file('admin.html')
        except:
            return 'Admin interface loading...'
    return 'Invalid access link', 401

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """Admin settings for auto-replies"""
    if not session.get('admin_logged_in'):
        return 'Unauthorized', 401
    
    if request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        
        conn = get_db()
        c = conn.cursor()
        
        if action == 'add_reply':
            reply_text = data.get('reply_text')
            if reply_text:
                c.execute('INSERT INTO auto_replies (reply_text) VALUES (?)', (reply_text,))
                conn.commit()
                return jsonify({'success': True, 'message': 'Reply added'})
        
        elif action == 'get_replies':
            c.execute('SELECT id, reply_text FROM auto_replies ORDER BY created_at DESC')
            replies = []
            for row in c.fetchall():
                replies.append({'id': row['id'], 'text': row['reply_text']})
            conn.close()
            return jsonify({'replies': replies})
        
        elif action == 'delete_reply':
            reply_id = data.get('reply_id')
            c.execute('DELETE FROM auto_replies WHERE id = ?', (reply_id,))
            conn.commit()
            return jsonify({'success': True, 'message': 'Reply deleted'})
        
        conn.close()
    
    return jsonify({'error': 'Invalid request'}), 400

# SocketIO Events
@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection"""
    sid = request.sid
    print(f'✅ Client connected: {sid}')
    emit('connection_response', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    sid = request.sid
    
    # Remove from user rooms
    device_id = None
    for did, sids in user_sockets.items():
        if sid in sids:
            sids.remove(sid)
            device_id = did
            if not sids:
                del user_sockets[did]
            break
    
    if sid in user_rooms:
        del user_rooms[sid]
    
    print(f'❌ Client disconnected: {sid}' + (f' (device: {device_id})' if device_id else ''))

@socketio.on('admin_auth')
def handle_admin_auth(data):
    """Authenticate admin via password"""
    password = data.get('password')
    sid = request.sid
    device_id = data.get('device_id')  # Get admin device ID
    
    if password == app.config['ADMIN_PASSWORD']:
        admin_sessions[sid] = {
            'authenticated': True,
            'login_time': datetime.now().isoformat(),
            'device_id': device_id  # Store admin device ID
        }
        admin_sockets.append(sid)
        if device_id:
            admin_devices.add(device_id)  # Track this admin device
        emit('admin_auth_response', {'success': True, 'message': 'Admin authenticated'})
        print(f'👨‍💼 Admin authenticated: {sid} (Device: {device_id})')
        print(f'📱 Admin devices with notifications enabled: {admin_devices}')
    else:
        emit('admin_auth_response', {'success': False, 'message': 'Invalid password'})

@socketio.on('join')
def on_join(data):
    """User joins their room"""
    device_id = data.get('device_id')
    username = data.get('username', 'Anonymous')
    
    if not device_id:
        device_id = str(uuid.uuid4())
    
    sid = request.sid
    join_room(device_id)
    user_rooms[sid] = device_id
    
    if device_id not in user_sockets:
        user_sockets[device_id] = []
    user_sockets[device_id].append(sid)
    
    # Store or update user in database
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT id FROM users WHERE device_id = ?', (device_id,))
    if c.fetchone():
        c.execute('UPDATE users SET last_active = ? WHERE device_id = ?',
                  (datetime.now().isoformat(), device_id))
    else:
        c.execute('INSERT INTO users (device_id, username) VALUES (?, ?)',
                  (device_id, username))
    
    conn.commit()
    conn.close()
    
    # Check if user is first-time
    c = get_db().cursor()
    c.execute('SELECT COUNT(*) FROM messages WHERE device_id = ? AND sender != "Support"',
              (device_id,))
    message_count = c.fetchone()[0]
    
    emit('user_data', {
        'device_id': device_id,
        'username': username,
        'is_first_message': message_count == 0
    })
    
    print(f'👤 User joined: {device_id} ({username})')

@socketio.on('send_message')
def handle_send_message(data):
    """Handle message from user"""
    device_id = data.get('device_id')
    message = data.get('message')
    msg_type = data.get('type', 'text')
    
    if not device_id or not message:
        emit('error', {'message': 'Device ID and message required'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Check if this is the first message from this user
        c.execute('SELECT COUNT(*) FROM messages WHERE device_id = ? AND sender != "Support"',
                  (device_id,))
        user_message_count = c.fetchone()[0]
        is_first_message = user_message_count == 0
        
        # Store message
        timestamp = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(days=2)).isoformat()
        
        c.execute('''INSERT INTO messages 
                     (device_id, sender, message, type, is_admin, timestamp, expires_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (device_id, data.get('sender', 'User'), message, msg_type, False, timestamp, expires_at))
        
        conn.commit()
        
        message_data = {
            'id': c.lastrowid,
            'device_id': device_id,
            'sender': data.get('sender', 'User'),
            'message': message,
            'type': msg_type,
            'is_admin': False,
            'timestamp': timestamp
        }
        
        # Send to user
        emit('receive_message', message_data, room=device_id)
        
        # Notify admins ONLY if they are registered admin devices
        if admin_devices:  # Only emit if admin devices exist
            socketio.emit('new_user_message', message_data, room='admin_room')
            print(f'🔔 Notification queued for admin devices: {admin_devices}')
        
        # Send automatic reply if appropriate
        if is_first_message:
            send_auto_reply(device_id, 'first')
        elif user_message_count == 1:  # This is the user's 2nd message
            if msg_type == 'image':
                send_auto_reply(device_id, 'image')
            else:
                send_auto_reply(device_id, 'text')
        
        print(f'💬 Message received from {device_id}: {message[:50]}...')
        
    except Exception as e:
        print(f'❌ Error storing message: {e}')
        emit('error', {'message': 'Failed to send message'})
    finally:
        conn.close()

@socketio.on('admin_send_message')
def handle_admin_send_message(data):
    """Handle admin message"""
    device_id = data.get('device_id')
    message = data.get('message')
    
    if not device_id or not message:
        emit('error', {'message': 'Device ID and message required'})
        return
    
    # Check admin authentication
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid].get('authenticated'):
        emit('error', {'message': 'Unauthorized - Admin access required'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        timestamp = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(days=2)).isoformat()
        
        c.execute('''INSERT INTO messages 
                     (device_id, sender, message, type, is_admin, timestamp, expires_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (device_id, 'Support', message, 'text', True, timestamp, expires_at))
        
        conn.commit()
        
        message_data = {
            'id': c.lastrowid,
            'device_id': device_id,
            'sender': 'Support',
            'message': message,
            'type': 'text',
            'is_admin': True,
            'is_auto_reply': False,
            'timestamp': timestamp
        }
        
        # Send to user and admin
        emit('receive_message', message_data, room=device_id)
        emit('message_sent', {'device_id': device_id, 'success': True}, room=sid)
        
        # Notify other admins
        socketio.emit('admin_message_sent', message_data, room='admin_room', skip_sid=sid)
        
        print(f'📤 Admin sent message to {device_id}')
        
    except Exception as e:
        print(f'❌ Error sending admin message: {e}')
        emit('error', {'message': 'Failed to send message'})
    finally:
        conn.close()

@socketio.on('upload_image')
def handle_upload_image(data):
    """Handle image upload"""
    device_id = data.get('device_id')
    image_data = data.get('image_data')
    is_admin = data.get('is_admin', False)
    
    if not device_id or not image_data:
        emit('error', {'message': 'Device ID and image data required'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Check if this is the first or second message from this user
        c.execute('SELECT COUNT(*) FROM messages WHERE device_id = ? AND sender != "Support"',
                  (device_id,))
        user_message_count = c.fetchone()[0]
        is_first_message = user_message_count == 0
        is_second_message = user_message_count == 1

        # Decode and save image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        filename = f"{uuid.uuid4()}_image.png"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        # Store in database
        timestamp = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(days=2)).isoformat()
        
        c.execute('''INSERT INTO uploaded_files 
                     (device_id, filename, filepath, uploaded_at, expires_at)
                     VALUES (?, ?, ?, ?, ?)''',
                  (device_id, filename, filepath, timestamp, expires_at))
        
        # Store as message
        c.execute('''INSERT INTO messages 
                     (device_id, sender, message, type, is_admin, timestamp, expires_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (device_id, 'Admin' if is_admin else 'User', f'/uploads/{filename}', 'image', is_admin, timestamp, expires_at))
        
        conn.commit()
        
        message_data = {
            'id': c.lastrowid,
            'device_id': device_id,
            'sender': 'Admin' if is_admin else 'User',
            'message': f'/uploads/{filename}',
            'type': 'image',
            'is_admin': is_admin,
            'timestamp': timestamp
        }
        
        if is_admin:
            emit('receive_message', message_data, room=device_id)
            emit('receive_message', message_data, room='admin_room')
        else:
            emit('receive_message', message_data, room=device_id)
            emit('new_user_message', message_data, room='admin_room')
            # Send auto-reply based on message position
            if is_first_message:
                send_auto_reply(device_id, 'first')
            elif is_second_message:
                send_auto_reply(device_id, 'image')
        
        print(f'📷 Image uploaded (expires: {expires_at})')
        
    except Exception as e:
        print(f'❌ Error uploading image: {e}')
        emit('error', {'message': 'Image upload failed'})
    finally:
        conn.close()

@socketio.on('admin_join')
def handle_admin_join(data=None):
    """Admin joins the admin room"""
    sid = request.sid
    join_room('admin_room')
    
    if sid in admin_sessions and admin_sessions[sid].get('authenticated'):
        print(f'👨‍💼 Admin joined admin room: {sid}')
        emit('admin_room_joined', {'success': True})

@socketio.on('get_all_users')
def handle_get_all_users(data=None):
    """Get all users for admin"""
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid].get('authenticated'):
        emit('error', {'message': 'Unauthorized - Admin access required'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('''SELECT 
                        u.device_id,
                        u.username,
                        u.created_at,
                        u.last_active,
                        COUNT(m.id) as message_count,
                        MAX(m.timestamp) as last_message
                     FROM users u
                     LEFT JOIN messages m ON u.device_id = m.device_id AND m.expires_at > ?
                     GROUP BY u.device_id
                     ORDER BY u.last_active DESC''', (datetime.now().isoformat(),))
        
        users = []
        for row in c.fetchall():
            last_active = datetime.fromisoformat(row['last_active']) if row['last_active'] else datetime.now()
            inactive_hours = (datetime.now() - last_active).total_seconds() / 3600
            
            is_connected = row['device_id'] in user_sockets and len(user_sockets[row['device_id']]) > 0
            
            users.append({
                'device_id': row['device_id'],
                'username': row['username'] or 'Anonymous',
                'created_at': row['created_at'],
                'last_active': row['last_active'],
                'last_message': row['last_message'],
                'message_count': row['message_count'],
                'inactive_hours': round(inactive_hours, 1),
                'is_active': inactive_hours < 48,
                'is_connected': is_connected,
                'connection_count': len(user_sockets.get(row['device_id'], []))
            })
        
        emit('users_list', {
            'users': users, 
            'total': len(users), 
            'timestamp': datetime.now().isoformat(),
            'connected_users': len(user_rooms)
        })
        print(f'📋 Sent users list: {len(users)} users')
        
    except Exception as e:
        print(f'❌ Error getting users: {e}')
        emit('error', {'message': 'Failed to get users'})
    finally:
        conn.close()

@socketio.on('get_user_messages')
def handle_get_user_messages(data):
    """Get messages for a specific user"""
    device_id = data.get('device_id')
    
    if not device_id:
        emit('error', {'message': 'Device ID required'})
        return
    
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid]:
        emit('error', {'message': 'Unauthorized - Admin access required'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        now = datetime.now().isoformat()
        c.execute('''SELECT * FROM messages 
                     WHERE device_id = ? 
                     AND expires_at > ?
                     ORDER BY timestamp ASC''', (device_id, now))
        
        messages = []
        for row in c.fetchall():
            messages.append({
                'id': row['id'],
                'device_id': row['device_id'],
                'sender': row['sender'],
                'message': row['message'],
                'type': row['type'],
                'is_admin': bool(row['is_admin']),
                'is_auto_reply': bool(row.get('is_auto_reply', False)) if 'is_auto_reply' in row.keys() else False,
                'timestamp': row['timestamp']
            })
        
        c.execute('SELECT username FROM users WHERE device_id = ?', (device_id,))
        user_info = c.fetchone()
        username = user_info['username'] if user_info else 'Anonymous'
        
        emit('user_messages', {
            'device_id': device_id,
            'username': username,
            'messages': messages,
            'total': len(messages)
        })
        print(f'💬 Sent {len(messages)} messages for {device_id}')
        
    except Exception as e:
        print(f'❌ Error getting messages: {e}')
        emit('error', {'message': 'Failed to get messages'})
    finally:
        conn.close()

@socketio.on('delete_user')
def handle_delete_user(data):
    """Delete a user and all their data"""
    device_id = data.get('device_id')
    
    if not device_id:
        emit('error', {'message': 'Device ID required'})
        return
    
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid].get('authenticated'):
        emit('error', {'message': 'Unauthorized - Admin access required'})
        return
    
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT filepath FROM uploaded_files WHERE device_id = ?', (device_id,))
        files = c.fetchall()
        
        for file_row in files:
            filepath = file_row[0]
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"🗑️ Deleted file: {filepath}")
                except Exception as e:
                    print(f"❌ Error deleting file {filepath}: {e}")
        
        c.execute('DELETE FROM users WHERE device_id = ?', (device_id,))
        conn.commit()
        conn.close()
        
        if device_id in user_sockets:
            for socket_id in user_sockets[device_id]:
                if socket_id in user_rooms:
                    del user_rooms[socket_id]
            del user_sockets[device_id]
        
        print(f"🗑️ Admin deleted user: {device_id}")
        emit('user_deleted', {'device_id': device_id, 'success': True})
        handle_get_all_users({})
        
    except Exception as e:
        print(f'❌ Error deleting user: {e}')
        emit('error', {'message': 'Failed to delete user'})

@socketio.on('heartbeat')
def handle_heartbeat(data):
    """Handle client heartbeat"""
    sid = request.sid
    device_id = data.get('device_id')
    
    if device_id and sid in user_rooms:
        update_user_activity(device_id)
        if sid in admin_sessions:
            admin_sessions[sid]['last_activity'] = datetime.now().isoformat()
        
        emit('heartbeat_ack', {
            'timestamp': datetime.now().isoformat(),
            'status': 'ok'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'🚀 Server starting on port {port}')
    print(f'🔑 Admin URL: example.com/{app.config["ADMIN_PASSWORD"]}')
    print(f'📁 Upload folder: {app.config["UPLOAD_FOLDER"]}')
    print(f'🗑️ Auto-cleanup: Every 1 hour (deletes data older than 2 days)')
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
