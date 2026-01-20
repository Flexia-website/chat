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
from datetime import datetime, timedelta
from functools import wraps

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'flexia123')
app.config['ADMIN_PASSWORD_HASH'] = hashlib.sha256(app.config['ADMIN_PASSWORD'].encode()).hexdigest()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

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

def check_admin_password(password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == app.config['ADMIN_PASSWORD_HASH']

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

def cleanup_expired_data():
    """Delete all messages and files older than 2 days"""
    conn = get_db()
    c = conn.cursor()
    
    deleted_messages = 0
    deleted_files = 0
    deleted_users = 0
    
    try:
        # Get current time
        now = datetime.now().isoformat()
        
        # Delete expired messages (older than 2 days)
        c.execute('DELETE FROM messages WHERE expires_at < ?', (now,))
        deleted_messages = c.rowcount
        
        # Delete expired files
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
        
        # Delete expired file records
        c.execute('DELETE FROM uploaded_files WHERE expires_at < ?', (now,))
        
        # Delete users who have been inactive for 3 days AND have no messages
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
        time.sleep(3600)  # Wait 1 hour
        try:
            cleanup_expired_data()
        except Exception as e:
            print(f"❌ Cleanup scheduler error: {e}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=run_cleanup_scheduler, daemon=True)
cleanup_thread.start()

# Authentication decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

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
        <a href="/admin/login">Admin Panel</a>
        '''

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if check_admin_password(password):
            session['admin_logged_in'] = True
            return redirect('/admin')
        return 'Invalid password', 401
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login</title>
        <style>
            body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100vh; display: flex; justify-content: center; align-items: center; }
            .login-box { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); text-align: center; }
            h1 { color: #333; margin-bottom: 30px; }
            input[type="password"] { width: 100%; padding: 15px; margin: 15px 0; border: 2px solid #ddd; border-radius: 10px; font-size: 16px; }
            button { background: #4361ee; color: white; border: none; padding: 15px 40px; border-radius: 10px; font-size: 16px; cursor: pointer; transition: 0.3s; }
            button:hover { background: #3a0ca3; transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>🔒 Admin Login</h1>
            <form method="POST">
                <input type="password" name="password" placeholder="Enter admin password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')

@app.route('/admin')
@admin_required
def admin_panel():
    try:
        return send_file('admin.html')
    except:
        return 'Admin panel not found', 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/stats')
@admin_required
def get_stats():
    """Get system statistics"""
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('SELECT COUNT(*) as total FROM users')
        total_users = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) as total FROM messages')
        total_messages = c.fetchone()[0]
        
        cutoff = (datetime.now() - timedelta(days=2)).isoformat()
        c.execute('SELECT COUNT(*) as total FROM users WHERE last_active >= ?', (cutoff,))
        active_users = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) as total FROM uploaded_files')
        total_files = c.fetchone()[0]
        
        # Today's activity
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        c.execute('SELECT COUNT(*) as total FROM messages WHERE timestamp >= ?', (today_start,))
        today_messages = c.fetchone()[0]
        
        # Active connections
        active_connections = len(user_rooms)
        
        # Expiring soon count
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
        c.execute('SELECT COUNT(*) as total FROM messages WHERE expires_at < ?', (tomorrow,))
        expiring_soon = c.fetchone()[0]
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'total_messages': total_messages,
            'total_files': total_files,
            'today_messages': today_messages,
            'active_connections': active_connections,
            'admin_connections': len([s for s in admin_sessions if admin_sessions[s].get('authenticated')]),
            'expiring_soon': expiring_soon,
            'server_time': datetime.now().isoformat()
        })
    finally:
        conn.close()

@app.route('/api/cleanup', methods=['POST'])
@admin_required
def manual_cleanup():
    """Manual cleanup endpoint"""
    try:
        result = cleanup_expired_data()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/history')
def get_user_history():
    """Get user's chat history"""
    device_id = request.args.get('device_id')
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Get user info
        c.execute('SELECT username FROM users WHERE device_id = ?', (device_id,))
        user = c.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all messages for this user (not expired)
        now = datetime.now().isoformat()
        c.execute('''SELECT * FROM messages 
                     WHERE device_id = ? 
                     AND expires_at > ?
                     ORDER BY timestamp ASC''', (device_id, now))
        
        messages = []
        for row in c.fetchall():
            messages.append({
                'id': row['id'],
                'sender': row['sender'],
                'message': row['message'],
                'type': row['type'],
                'is_admin': bool(row['is_admin']),
                'timestamp': row['timestamp'],
                'expires_at': row['expires_at']
            })
        
        # Update user activity
        update_user_activity(device_id)
        
        return jsonify({
            'success': True,
            'username': user['username'],
            'device_id': device_id,
            'messages': messages,
            'total': len(messages),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f'❌ Error getting user history: {e}')
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ==============================================
# SOCKET.IO EVENTS
# ==============================================

@socketio.on('connect')
def handle_connect():
    print(f'✅ Client connected: {request.sid}')
    emit('connection_established', {'sid': request.sid, 'timestamp': datetime.now().isoformat()})

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f'🔌 Client disconnected: {sid}')
    
    # Clean up admin session
    if sid in admin_sessions:
        print(f'🗑️ Removed admin session for {sid}')
        del admin_sessions[sid]
    
    # Clean up user room
    if sid in user_rooms:
        device_id = user_rooms[sid]
        
        # Remove from user_sockets
        if device_id in user_sockets:
            if sid in user_sockets[device_id]:
                user_sockets[device_id].remove(sid)
            if not user_sockets[device_id]:
                del user_sockets[device_id]
        
        del user_rooms[sid]
        
        # Notify admins about user disconnection
        emit('user_disconnected', {
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        }, broadcast=True)
        
        print(f'🗑️ User {device_id[:8]}... disconnected')

@socketio.on('admin_auth')
def handle_admin_auth(data):
    """Authenticate admin via SocketIO"""
    password = data.get('password')
    sid = request.sid
    
    print(f'🔐 Admin auth attempt from {sid}')
    
    if check_admin_password(password):
        admin_sessions[sid] = {
            'authenticated': True,
            'authenticated_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        # Join admin room
        join_room('admin_room')
        
        emit('admin_auth_success', {
            'message': 'Authenticated successfully',
            'timestamp': datetime.now().isoformat(),
            'session_id': sid
        })
        
        print(f'👑 Admin authenticated: {sid}')
        
        # Send initial data
        handle_get_all_users({})
        
    else:
        admin_sessions[sid] = {'authenticated': False}
        emit('admin_auth_failed', {'message': 'Invalid password'})
        print(f'❌ Admin auth failed: {sid}')

@socketio.on('register_user')
def handle_register_user(data):
    """Register or update user and send their chat history"""
    device_id = data.get('device_id')
    username = data.get('username', 'Anonymous')
    
    if not device_id:
        emit('error', {'message': 'Device ID required'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Check if user exists
        c.execute('SELECT * FROM users WHERE device_id = ?', (device_id,))
        existing_user = c.fetchone()
        
        now = datetime.now().isoformat()
        if existing_user:
            # Update existing user
            if username != 'Anonymous':
                c.execute('UPDATE users SET username = ?, last_active = ? WHERE device_id = ?',
                         (username, now, device_id))
            else:
                c.execute('UPDATE users SET last_active = ? WHERE device_id = ?',
                         (now, device_id))
            is_new = False
            print(f'🔄 Updated user: {username} ({device_id[:8]}...)')
        else:
            # Insert new user
            c.execute('INSERT INTO users (device_id, username, last_active) VALUES (?, ?, ?)',
                     (device_id, username, now))
            is_new = True
            print(f'✅ New user registered: {username} ({device_id[:8]}...)')
        
        # Get user's chat history (not expired)
        now_time = datetime.now().isoformat()
        c.execute('''SELECT * FROM messages 
                     WHERE device_id = ? 
                     AND expires_at > ?
                     ORDER BY timestamp ASC''', (device_id, now_time))
        
        history = []
        for row in c.fetchall():
            history.append({
                'id': row['id'],
                'sender': row['sender'],
                'message': row['message'],
                'type': row['type'],
                'is_admin': bool(row['is_admin']),
                'timestamp': row['timestamp']
            })
        
        conn.commit()
        
        # Join room for this device
        join_room(device_id)
        user_rooms[request.sid] = device_id
        
        # Track socket connection
        if device_id not in user_sockets:
            user_sockets[device_id] = []
        if request.sid not in user_sockets[device_id]:
            user_sockets[device_id].append(request.sid)
        
        # Send user registered event to all admins
        for admin_sid in list(admin_sessions.keys()):
            if admin_sessions[admin_sid].get('authenticated'):
                emit('user_connected', {
                    'device_id': device_id,
                    'username': username,
                    'timestamp': now,
                    'is_new': is_new,
                    'socket_count': len(user_sockets.get(device_id, [])),
                    'message_count': len(history)
                }, room=admin_sid)
        
        # Send registration success WITH chat history
        emit('user_registered', {
            'device_id': device_id, 
            'username': username,
            'timestamp': now,
            'is_new': is_new,
            'history': history,
            'message_count': len(history),
            'message': 'Registration successful'
        })
        
        print(f'📋 Sent {len(history)} messages from history to {username}')
        
    except Exception as e:
        print(f'❌ Error registering user: {e}')
        emit('registration_failed', {'message': 'Registration failed: ' + str(e)})
    finally:
        conn.close()

@socketio.on('send_message')
def handle_send_message(data):
    """Handle user message"""
    device_id = data.get('device_id')
    username = data.get('username', 'Anonymous')
    message = data.get('message', '').strip()
    msg_type = data.get('type', 'text')
    
    print(f'📨 Message from {username} ({device_id[:8]}...): {message[:100]}')
    
    if not all([device_id, message]):
        emit('error', {'message': 'Missing required fields'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Verify user exists
        c.execute('SELECT * FROM users WHERE device_id = ?', (device_id,))
        user = c.fetchone()
        
        if not user:
            emit('error', {'message': 'User not registered'})
            return
        
        # Update user activity
        update_user_activity(device_id)
        
        # Save message with 2-day expiration
        expires_at = (datetime.now() + timedelta(days=2)).isoformat()
        timestamp = datetime.now().isoformat()
        c.execute('''INSERT INTO messages (device_id, sender, message, type, is_admin, timestamp, expires_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (device_id, username, message, msg_type, False, timestamp, expires_at))
        conn.commit()
        
        message_data = {
            'device_id': device_id,
            'sender': username,
            'message': message,
            'type': msg_type,
            'is_admin': False,
            'timestamp': timestamp,
            'expires_at': expires_at,
            'id': c.lastrowid
        }
        
        # Send to user's room (echo back)
        emit('receive_message', message_data, room=device_id)
        
        # Notify all authenticated admins
        authenticated_admins = [sid for sid in admin_sessions if admin_sessions[sid].get('authenticated')]
        if authenticated_admins:
            emit('new_user_message', message_data, room='admin_room')
            print(f'📢 Sent to {len(authenticated_admins)} admin(s)')
        else:
            print('⚠️ No authenticated admins to notify')
        
        print(f'✅ Message saved (expires: {expires_at})')
        
    except Exception as e:
        print(f'❌ Error sending message: {e}')
        emit('error', {'message': 'Failed to send message'})
    finally:
        conn.close()

@socketio.on('admin_message')
def handle_admin_message(data):
    """Handle admin message to user"""
    device_id = data.get('device_id')
    message = data.get('message', '').strip()
    msg_type = data.get('type', 'text')
    
    if not all([device_id, message]):
        emit('error', {'message': 'Missing required fields'})
        return
    
    # Check admin authentication
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid].get('authenticated'):
        emit('error', {'message': 'Unauthorized - Admin access required'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Save message with 2-day expiration
        expires_at = (datetime.now() + timedelta(days=2)).isoformat()
        timestamp = datetime.now().isoformat()
        c.execute('''INSERT INTO messages (device_id, sender, message, type, is_admin, timestamp, expires_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (device_id, 'Flexia Merchant', message, msg_type, True, timestamp, expires_at))
        conn.commit()
        
        message_data = {
            'device_id': device_id,
            'sender': 'Flexia Merchant',
            'message': message,
            'type': msg_type,
            'is_admin': True,
            'timestamp': timestamp,
            'expires_at': expires_at,
            'id': c.lastrowid
        }
        
        # Send to specific user's room
        emit('receive_message', message_data, room=device_id)
        
        # Also send to admin room
        emit('receive_message', message_data, room='admin_room')
        
        print(f'📤 Admin message to {device_id[:8]}... (expires: {expires_at})')
        
    except Exception as e:
        print(f'❌ Error sending admin message: {e}')
        emit('error', {'message': 'Failed to send admin message'})
    finally:
        conn.close()

@socketio.on('upload_image')
def handle_upload_image(data):
    """Handle image upload"""
    device_id = data.get('device_id')
    image_data = data.get('image')
    filename = data.get('filename', 'image.jpg')
    is_admin = data.get('is_admin', False)
    username = data.get('username', 'Anonymous')
    
    if not all([device_id, image_data]):
        emit('error', {'message': 'Missing required fields'})
        return
    
    # Check admin authentication if is_admin
    if is_admin:
        sid = request.sid
        if sid not in admin_sessions or not admin_sessions[sid].get('authenticated'):
            emit('error', {'message': 'Unauthorized - Admin access required'})
            return
    
    try:
        # Update user activity
        if not is_admin:
            update_user_activity(device_id)
        
        # Extract base64 data
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Generate unique filename
        ext = filename.split('.')[-1] if '.' in filename else 'jpg'
        unique_filename = f"{device_id}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        # Save to database with 2-day expiration
        expires_at = (datetime.now() + timedelta(days=2)).isoformat()
        conn = get_db()
        c = conn.cursor()
        
        # Record file upload
        c.execute('''INSERT INTO uploaded_files (device_id, filename, filepath, expires_at)
                     VALUES (?, ?, ?, ?)''', 
                  (device_id, filename, filepath, expires_at))
        
        # Save as message
        image_url = f'/uploads/{unique_filename}'
        sender = 'Flexia Merchant' if is_admin else username
        timestamp = datetime.now().isoformat()
        
        c.execute('''INSERT INTO messages (device_id, sender, message, type, is_admin, timestamp, expires_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (device_id, sender, image_url, 'image', is_admin, timestamp, expires_at))
        conn.commit()
        
        message_data = {
            'device_id': device_id,
            'sender': sender,
            'message': image_url,
            'type': 'image',
            'is_admin': is_admin,
            'timestamp': timestamp,
            'expires_at': expires_at,
            'id': c.lastrowid
        }
        
        if is_admin:
            # Admin sending to user
            emit('receive_message', message_data, room=device_id)
            emit('receive_message', message_data, room='admin_room')
        else:
            # User sending
            emit('receive_message', message_data, room=device_id)
            # Notify admins
            emit('new_user_message', message_data, room='admin_room')
        
        print(f'📷 Image uploaded (expires: {expires_at})')
        
    except Exception as e:
        print(f'❌ Error uploading image: {e}')
        emit('error', {'message': 'Image upload failed'})
    finally:
        conn.close()

@socketio.on('get_all_users')
def handle_get_all_users(data=None):
    """Get all users for admin"""
    # Check admin authentication
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
            # Calculate inactivity duration
            last_active = datetime.fromisoformat(row['last_active']) if row['last_active'] else datetime.now()
            inactive_hours = (datetime.now() - last_active).total_seconds() / 3600
            
            # Check if user is currently connected
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
    
    # Check admin authentication for this endpoint
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid]:
        emit('error', {'message': 'Unauthorized - Admin access required'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Get only non-expired messages
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
                'timestamp': row['timestamp'],
                'expires_at': row['expires_at']
            })
        
        # Get user info
        c.execute('SELECT username FROM users WHERE device_id = ?', (device_id,))
        user_info = c.fetchone()
        username = user_info['username'] if user_info else 'Anonymous'
        
        emit('user_messages', {
            'device_id': device_id,
            'username': username,
            'messages': messages,
            'total': len(messages),
            'expired_count': get_expired_count(device_id)
        })
        print(f'💬 Sent {len(messages)} messages for {device_id}')
        
    except Exception as e:
        print(f'❌ Error getting messages: {e}')
        emit('error', {'message': 'Failed to get messages'})
    finally:
        conn.close()

def get_expired_count(device_id):
    """Get count of expired messages for a user"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM messages WHERE device_id = ? AND expires_at < ?',
              (device_id, datetime.now().isoformat()))
    count = c.fetchone()[0]
    conn.close()
    return count

@socketio.on('delete_user')
def handle_delete_user(data):
    """Delete a user and all their data"""
    device_id = data.get('device_id')
    
    if not device_id:
        emit('error', {'message': 'Device ID required'})
        return
    
    # Check admin authentication
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid].get('authenticated'):
        emit('error', {'message': 'Unauthorized - Admin access required'})
        return
    
    try:
        # Get user files first
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT filepath FROM uploaded_files WHERE device_id = ?', (device_id,))
        files = c.fetchall()
        
        # Delete physical files
        for file_row in files:
            filepath = file_row[0]
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"🗑️ Deleted file: {filepath}")
                except Exception as e:
                    print(f"❌ Error deleting file {filepath}: {e}")
        
        # Delete user (CASCADE will delete messages and file records)
        c.execute('DELETE FROM users WHERE device_id = ?', (device_id,))
        conn.commit()
        conn.close()
        
        # Remove from active connections
        if device_id in user_sockets:
            for socket_id in user_sockets[device_id]:
                if socket_id in user_rooms:
                    del user_rooms[socket_id]
            del user_sockets[device_id]
        
        print(f"🗑️ Admin deleted user: {device_id}")
        emit('user_deleted', {'device_id': device_id, 'success': True})
        
        # Refresh users list
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
        # Update user activity
        update_user_activity(device_id)
        admin_sessions[sid] = admin_sessions.get(sid, {})
        admin_sessions[sid]['last_activity'] = datetime.now().isoformat()
        
        emit('heartbeat_ack', {
            'timestamp': datetime.now().isoformat(),
            'status': 'ok'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'🚀 Server starting on port {port}')
    print(f'🔑 Admin password: {app.config["ADMIN_PASSWORD"]}')
    print(f'📁 Upload folder: {app.config["UPLOAD_FOLDER"]}')
    print(f'🗑️ Auto-cleanup: Every 1 hour (deletes data older than 2 days)')
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
