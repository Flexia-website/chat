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
    
    # Messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        sender TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'text',
        is_admin BOOLEAN DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES users(device_id) ON DELETE CASCADE
    )''')
    
    # Files table
    c.execute('''CREATE TABLE IF NOT EXISTS uploaded_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES users(device_id) ON DELETE CASCADE
    )''')
    
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

# Authentication decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

# In-memory storage for admin sessions
admin_sessions = {}
user_rooms = {}

def cleanup_inactive_users():
    """Delete users inactive for more than 2 days and their associated files"""
    conn = get_db()
    c = conn.cursor()
    
    # Calculate cutoff time (2 days ago)
    cutoff_time = datetime.now() - timedelta(days=2)
    
    # Get inactive users
    c.execute('SELECT device_id FROM users WHERE last_active < ?', (cutoff_time.isoformat(),))
    inactive_users = c.fetchall()
    
    deleted_count = 0
    for user in inactive_users:
        device_id = user[0]
        
        # Get all files for this user
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
        print(f"🗑️ Deleted inactive user: {device_id}")
        deleted_count += 1
    
    conn.commit()
    conn.close()
    
    if deleted_count > 0:
        print(f"✅ Cleaned up {deleted_count} inactive users")
    
    return deleted_count

def run_cleanup_scheduler():
    """Run cleanup every hour"""
    while True:
        time.sleep(3600)  # Wait 1 hour
        try:
            cleanup_inactive_users()
        except Exception as e:
            print(f"❌ Cleanup error: {e}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=run_cleanup_scheduler, daemon=True)
cleanup_thread.start()

# HTTP Routes - SERVE FILES FROM ROOT
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
    <head><title>Admin Login</title></head>
    <body>
        <form method="POST">
            <input type="password" name="password" placeholder="Admin password" required>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    '''

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
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'total_messages': total_messages,
            'total_files': total_files,
            'today_messages': today_messages,
            'server_time': datetime.now().isoformat()
        })
    finally:
        conn.close()

@app.route('/api/cleanup', methods=['POST'])
@admin_required
def manual_cleanup():
    """Manual cleanup endpoint"""
    try:
        count = cleanup_inactive_users()
        return jsonify({'success': True, 'message': f'Cleanup completed. Deleted {count} users.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==============================================
# SOCKET.IO EVENTS
# ==============================================

@socketio.on('connect')
def handle_connect():
    print(f'✅ Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f'🔌 Client disconnected: {sid}')
    
    # Clean up admin session
    if sid in admin_sessions:
        del admin_sessions[sid]
    
    # Clean up user room
    if sid in user_rooms:
        del user_rooms[sid]

@socketio.on('admin_auth')
def handle_admin_auth(data):
    """Authenticate admin via SocketIO"""
    password = data.get('password')
    sid = request.sid
    
    if check_admin_password(password):
        admin_sessions[sid] = True
        emit('admin_auth_success', {
            'message': 'Authenticated successfully',
            'timestamp': datetime.now().isoformat()
        })
        print(f'👑 Admin authenticated: {sid}')
    else:
        emit('admin_auth_failed', {'message': 'Invalid password'})

@socketio.on('register_user')
def handle_register_user(data):
    """Register or update user with persistent device_id"""
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
            print(f'🔄 Updated user: {username} ({device_id[:8]}...)')
        else:
            # Insert new user
            c.execute('INSERT INTO users (device_id, username, last_active) VALUES (?, ?, ?)',
                     (device_id, username, now))
            print(f'✅ New user registered: {username} ({device_id[:8]}...)')
        
        conn.commit()
        
        # Join room for this device
        join_room(device_id)
        user_rooms[request.sid] = device_id
        
        emit('user_registered', {
            'device_id': device_id, 
            'username': username,
            'timestamp': now,
            'is_new': not existing_user
        })
        
    except Exception as e:
        print(f'❌ Error registering user: {e}')
        emit('error', {'message': 'Registration failed'})
    finally:
        conn.close()

@socketio.on('send_message')
def handle_send_message(data):
    """Handle user message"""
    device_id = data.get('device_id')
    username = data.get('username', 'Anonymous')
    message = data.get('message', '').strip()
    msg_type = data.get('type', 'text')
    
    if not all([device_id, message]):
        emit('error', {'message': 'Missing required fields'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Update user activity
        update_user_activity(device_id)
        
        # Save message
        timestamp = datetime.now().isoformat()
        c.execute('''INSERT INTO messages (device_id, sender, message, type, is_admin, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (device_id, username, message, msg_type, False, timestamp))
        conn.commit()
        
        message_data = {
            'device_id': device_id,
            'sender': username,
            'message': message,
            'type': msg_type,
            'is_admin': False,
            'timestamp': timestamp,
            'id': c.lastrowid
        }
        
        # Send to user's room
        emit('receive_message', message_data, room=device_id)
        
        # Notify admins
        emit('new_user_message', message_data, broadcast=True, include_self=False)
        
        print(f'💬 Message from {username} ({device_id[:8]}...): {message[:50]}...')
        
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
    if sid not in admin_sessions or not admin_sessions[sid]:
        emit('error', {'message': 'Unauthorized - Admin access required'})
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        timestamp = datetime.now().isoformat()
        c.execute('''INSERT INTO messages (device_id, sender, message, type, is_admin, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (device_id, 'Flexia Merchant', message, msg_type, True, timestamp))
        conn.commit()
        
        message_data = {
            'device_id': device_id,
            'sender': 'Flexia Merchant',
            'message': message,
            'type': msg_type,
            'is_admin': True,
            'timestamp': timestamp,
            'id': c.lastrowid
        }
        
        # Send to specific user's room
        emit('receive_message', message_data, room=device_id)
        
        # Also send to admin panel
        emit('receive_message', message_data, broadcast=True)
        
        print(f'📤 Admin message to {device_id[:8]}...: {message[:50]}...')
        
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
        if sid not in admin_sessions or not admin_sessions[sid]:
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
        
        # Save to database
        conn = get_db()
        c = conn.cursor()
        
        # Record file upload
        c.execute('''INSERT INTO uploaded_files (device_id, filename, filepath)
                     VALUES (?, ?, ?)''', (device_id, filename, filepath))
        
        # Save as message
        image_url = f'/uploads/{unique_filename}'
        sender = 'Flexia Merchant' if is_admin else username
        timestamp = datetime.now().isoformat()
        
        c.execute('''INSERT INTO messages (device_id, sender, message, type, is_admin, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (device_id, sender, image_url, 'image', is_admin, timestamp))
        conn.commit()
        conn.close()
        
        message_data = {
            'device_id': device_id,
            'sender': sender,
            'message': image_url,
            'type': 'image',
            'is_admin': is_admin,
            'timestamp': timestamp
        }
        
        if is_admin:
            # Admin sending to user
            emit('receive_message', message_data, room=device_id)
            emit('receive_message', message_data, broadcast=True)
        else:
            # User sending to admin
            emit('receive_message', message_data, room=device_id)
            emit('new_user_message', message_data, broadcast=True, include_self=False)
        
        print(f'📷 Image uploaded: {unique_filename}')
        
    except Exception as e:
        print(f'❌ Error uploading image: {e}')
        emit('error', {'message': 'Image upload failed'})

@socketio.on('get_all_users')
def handle_get_all_users(data=None):
    """Get all users for admin"""
    # Check admin authentication
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid]:
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
                     LEFT JOIN messages m ON u.device_id = m.device_id
                     GROUP BY u.device_id
                     ORDER BY u.last_active DESC''')
        
        users = []
        for row in c.fetchall():
            # Calculate inactivity duration
            last_active = datetime.fromisoformat(row['last_active']) if row['last_active'] else datetime.now()
            inactive_hours = (datetime.now() - last_active).total_seconds() / 3600
            
            users.append({
                'device_id': row['device_id'],
                'username': row['username'] or 'Anonymous',
                'created_at': row['created_at'],
                'last_active': row['last_active'],
                'last_message': row['last_message'],
                'message_count': row['message_count'],
                'inactive_hours': round(inactive_hours, 1),
                'is_active': inactive_hours < 48  # Active if less than 2 days
            })
        
        emit('users_list', {'users': users, 'total': len(users), 'timestamp': datetime.now().isoformat()})
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
        c.execute('''SELECT * FROM messages 
                     WHERE device_id = ? 
                     ORDER BY timestamp ASC''', (device_id,))
        
        messages = []
        for row in c.fetchall():
            messages.append({
                'id': row['id'],
                'device_id': row['device_id'],
                'sender': row['sender'],
                'message': row['message'],
                'type': row['type'],
                'is_admin': bool(row['is_admin']),
                'timestamp': row['timestamp']
            })
        
        # Get user info
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
    
    # Check admin authentication
    sid = request.sid
    if sid not in admin_sessions or not admin_sessions[sid]:
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
        
        print(f"🗑️ Admin deleted user: {device_id}")
        emit('user_deleted', {'device_id': device_id, 'success': True})
        
        # Refresh users list
        handle_get_all_users({})
        
    except Exception as e:
        print(f'❌ Error deleting user: {e}')
        emit('error', {'message': 'Failed to delete user'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'🚀 Server starting on port {port}')
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
