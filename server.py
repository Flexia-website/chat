from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import uuid
import os
from datetime import datetime, timedelta
import json
import eventlet
import base64
from PIL import Image
import io
import sqlite3
from contextlib import contextmanager
import logging
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

eventlet.monkey_patch()

app = Flask(__name__, static_folder='static', template_folder='templates')

# Configuration for Render
if 'RENDER' in os.environ:
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'production-secret-key-change-in-render')
    app.config['UPLOAD_FOLDER'] = '/opt/render/project/src/uploads'
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
else:
    app.config['SECRET_KEY'] = 'development-secret-key-change-this'
    app.config['UPLOAD_FOLDER'] = 'uploads'
    admin_password = '123456'

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

CORS(app)
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   async_mode='eventlet',
                   logger=True,
                   engineio_logger=True)

# Database setup
DATABASE_PATH = 'chat_app.db'

def init_database():
    """Initialize the database with tables"""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      device_id TEXT UNIQUE NOT NULL,
                      username TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      expires_at TIMESTAMP,
                      last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      is_active BOOLEAN DEFAULT 1,
                      message_count INTEGER DEFAULT 0)''')
        
        # Messages table
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      message_id TEXT UNIQUE NOT NULL,
                      device_id TEXT NOT NULL,
                      sender TEXT NOT NULL,
                      message TEXT NOT NULL,
                      message_type TEXT DEFAULT 'text',
                      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      is_admin BOOLEAN DEFAULT 0,
                      is_read BOOLEAN DEFAULT 0)''')
        
        # Files table for uploaded images
        c.execute('''CREATE TABLE IF NOT EXISTS files
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      file_id TEXT UNIQUE NOT NULL,
                      filename TEXT NOT NULL,
                      filepath TEXT NOT NULL,
                      device_id TEXT NOT NULL,
                      upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      file_size INTEGER,
                      mime_type TEXT)''')
        
        # Create indexes for better performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_device_id ON users(device_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_expires_at ON users(expires_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_messages_device_id ON messages(device_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_files_device_id ON files(device_id)')
        
        conn.commit()
    logger.info("✅ Database initialized successfully")

@contextmanager
def get_db_connection():
    """Get database connection with automatic cleanup"""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()

# Initialize database on startup
init_database()

# Cleanup function for expired users
def cleanup_expired_users():
    """Remove expired users and their data"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Find expired users
            c.execute("SELECT device_id FROM users WHERE expires_at <= datetime('now')")
            expired_users = [row['device_id'] for row in c.fetchall()]
            
            if expired_users:
                # Delete messages
                c.execute("DELETE FROM messages WHERE device_id IN ({})".format(
                    ','.join(['?'] * len(expired_users))
                ), expired_users)
                
                # Delete files records (actual files remain in uploads folder)
                c.execute("DELETE FROM files WHERE device_id IN ({})".format(
                    ','.join(['?'] * len(expired_users))
                ), expired_users)
                
                # Delete users
                c.execute("DELETE FROM users WHERE device_id IN ({})".format(
                    ','.join(['?'] * len(expired_users))
                ), expired_users)
                
                conn.commit()
                logger.info(f"✅ Cleaned up {len(expired_users)} expired users")
    
    except Exception as e:
        logger.error(f"❌ Error cleaning up expired users: {str(e)}")

# Run cleanup on startup
cleanup_expired_users()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<password>.html')
def admin_page(password):
    if password == admin_password:
        return render_template('admin.html')
    return "Invalid password", 403

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT 1")
        db_status = 'healthy'
    except:
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'users_count': get_total_users_count(),
        'messages_count': get_total_messages_count()
    })

@app.route('/api/stats')
def get_stats():
    """Get application statistics"""
    if not request.args.get('admin') == admin_password:
        return jsonify({'error': 'Unauthorized'}), 401
    
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Get user statistics
        c.execute("""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN expires_at > datetime('now') THEN 1 ELSE 0 END) as active_users,
                SUM(message_count) as total_messages,
                COUNT(CASE WHEN datetime(last_active) > datetime('now', '-1 hour') THEN 1 END) as online_now
            FROM users
        """)
        stats = dict(c.fetchone())
        
        # Get daily messages
        c.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as count
            FROM messages
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """)
        daily_messages = [dict(row) for row in c.fetchall()]
        
        # Get recent users
        c.execute("""
            SELECT 
                device_id,
                username,
                created_at,
                last_active,
                message_count
            FROM users
            WHERE expires_at > datetime('now')
            ORDER BY last_active DESC
            LIMIT 10
        """)
        recent_users = [dict(row) for row in c.fetchall()]
    
    return jsonify({
        'stats': stats,
        'daily_messages': daily_messages,
        'recent_users': recent_users
    })

# Helper functions
def get_total_users_count():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE expires_at > datetime('now')")
        return c.fetchone()[0]

def get_total_messages_count():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM messages")
        return c.fetchone()[0]

def create_or_get_user(device_id, ip_address=None, user_agent=None):
    """Get existing user or create new one"""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Check if user exists and is not expired
        c.execute("""
            SELECT * FROM users 
            WHERE device_id = ? AND expires_at > datetime('now')
        """, (device_id,))
        
        user = c.fetchone()
        
        if user:
            # Update last active
            c.execute("""
                UPDATE users 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE device_id = ?
            """, (device_id,))
            conn.commit()
            return dict(user)
        else:
            # Create new user
            username = f"User_{device_id[:8]}"
            expires_at = datetime.now() + timedelta(days=7)
            
            c.execute("""
                INSERT OR REPLACE INTO users 
                (device_id, username, created_at, expires_at, last_active, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                device_id,
                username,
                datetime.now().isoformat(),
                expires_at.isoformat(),
                datetime.now().isoformat(),
                1
            ))
            conn.commit()
            
            return {
                'device_id': device_id,
                'username': username,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'last_active': datetime.now().isoformat(),
                'is_active': True,
                'message_count': 0
            }

def save_message(device_id, sender, message, message_type='text', is_admin=False):
    """Save message to database"""
    message_id = str(uuid.uuid4())
    
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Save message
        c.execute("""
            INSERT INTO messages 
            (message_id, device_id, sender, message, message_type, timestamp, is_admin)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            device_id,
            sender,
            message,
            message_type,
            datetime.now().isoformat(),
            1 if is_admin else 0
        ))
        
        # Update user's message count
        c.execute("""
            UPDATE users 
            SET message_count = message_count + 1,
                last_active = CURRENT_TIMESTAMP
            WHERE device_id = ?
        """, (device_id,))
        
        conn.commit()
    
    return message_id

def get_user_messages(device_id, limit=50):
    """Get messages for a user"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT 
                message_id as id,
                sender,
                message,
                message_type as type,
                timestamp,
                is_admin
            FROM messages 
            WHERE device_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (device_id, limit))
        
        messages = []
        for row in c.fetchall():
            messages.append({
                'id': row['id'],
                'sender': row['sender'],
                'message': row['message'],
                'type': row['type'],
                'timestamp': row['timestamp'],
                'is_admin': bool(row['is_admin']),
                'device_id': device_id
            })
    
    return messages

def get_all_active_users():
    """Get all active users for admin panel"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT 
                u.device_id,
                u.username,
                u.created_at,
                u.expires_at,
                u.last_active,
                u.message_count,
                COUNT(m.id) as recent_messages,
                MAX(m.timestamp) as last_message_time
            FROM users u
            LEFT JOIN messages m ON u.device_id = m.device_id 
                AND m.timestamp > datetime('now', '-1 day')
            WHERE u.expires_at > datetime('now')
            GROUP BY u.device_id, u.username, u.created_at, u.expires_at, 
                     u.last_active, u.message_count
            ORDER BY u.last_active DESC
        """)
        
        users = []
        for row in c.fetchall():
            users.append({
                'device_id': row['device_id'],
                'username': row['username'],
                'created_at': row['created_at'],
                'expires_at': row['expires_at'],
                'last_active': row['last_active'],
                'message_count': row['message_count'] or 0,
                'recent_messages': row['recent_messages'] or 0,
                'is_online': datetime.fromisoformat(row['last_active']) > datetime.now() - timedelta(minutes=5)
            })
    
    return users

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    try:
        device_id = request.args.get('device_id')
        if not device_id:
            device_id = str(uuid.uuid4())
        
        # Get or create user
        user = create_or_get_user(device_id)
        
        # Join user's room
        join_room(device_id)
        
        # Send user info
        emit('user_info', {
            'device_id': user['device_id'],
            'username': user['username'],
            'expires_at': user['expires_at'],
            'created_at': user['created_at'],
            'message_count': user['message_count']
        })
        
        # Send previous messages
        messages = get_user_messages(device_id, 50)
        for msg in messages:
            emit('receive_message', msg)
        
        logger.info(f"✅ User connected: {user['username']} ({device_id[:8]}...)")
    
    except Exception as e:
        logger.error(f"❌ Connection error: {str(e)}")
        emit('error', {'message': 'Connection failed'})

@socketio.on('send_message')
def handle_message(data):
    try:
        device_id = data.get('device_id')
        message = data.get('message', '').strip()
        message_type = data.get('type', 'text')
        
        if not device_id or not message:
            return
        
        # Get user
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE device_id = ?", (device_id,))
            user = c.fetchone()
        
        if not user:
            emit('error', {'message': 'User not found'})
            return
        
        # Check if user is expired
        expires_at = datetime.fromisoformat(user['expires_at'])
        if datetime.now() > expires_at:
            emit('error', {'message': 'Your account has expired'})
            return
        
        # Save user message
        message_id = save_message(device_id, user['username'], message, message_type, False)
        
        # Send to user
        user_msg = {
            'id': message_id,
            'sender': user['username'],
            'message': message,
            'type': message_type,
            'timestamp': datetime.now().isoformat(),
            'is_admin': False,
            'device_id': device_id
        }
        
        emit('receive_message', user_msg, room=device_id)
        
        # Notify all admins about new message
        emit('new_user_message', user_msg, broadcast=True)
        
        logger.info(f"📨 Message sent from {user['username']}: {message[:50]}...")
    
    except Exception as e:
        logger.error(f"❌ Message sending error: {str(e)}")
        emit('error', {'message': 'Failed to send message'})

@socketio.on('upload_image')
def handle_image_upload(data):
    try:
        device_id = data.get('device_id')
        image_data = data.get('image')
        filename = data.get('filename', 'image.png')
        is_admin = data.get('is_admin', False)
        
        if not device_id or not image_data:
            return
        
        # Get user
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE device_id = ?", (device_id,))
            user = c.fetchone()
        
        if not user:
            emit('error', {'message': 'User not found'})
            return
        
        # Check if user is expired (skip for admin)
        if not is_admin:
            expires_at = datetime.fromisoformat(user['expires_at'])
            if datetime.now() > expires_at:
                emit('error', {'message': 'Your account has expired'})
                return
        
        # Decode and save image
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Validate image
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        unique_filename = f"{file_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        # Save file record to database
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO files 
                (file_id, filename, filepath, device_id, upload_time, file_size, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id,
                filename,
                f'/uploads/{unique_filename}',
                device_id,
                datetime.now().isoformat(),
                len(image_bytes),
                'image/png'
            ))
            conn.commit()
        
        # Determine sender
        sender = 'Flexia Merchant' if is_admin else user['username']
        
        # Save message with image
        message_id = save_message(
            device_id,
            sender,
            f'/uploads/{unique_filename}',
            'image',
            is_admin
        )
        
        # Send to user
        image_msg = {
            'id': message_id,
            'sender': sender,
            'message': f'/uploads/{unique_filename}',
            'type': 'image',
            'timestamp': datetime.now().isoformat(),
            'is_admin': is_admin,
            'device_id': device_id
        }
        
        emit('receive_message', image_msg, room=device_id)
        
        # If not admin, broadcast to admins
        if not is_admin:
            emit('new_user_message', image_msg, broadcast=True)
        
        logger.info(f"🖼️ Image uploaded by {sender}: {filename}")
    
    except Exception as e:
        logger.error(f"❌ Image upload error: {str(e)}")
        emit('error', {'message': f'Failed to upload image: {str(e)}'})

@socketio.on('admin_message')
def handle_admin_message(data):
    try:
        device_id = data.get('device_id')
        message = data.get('message', '').strip()
        message_type = data.get('type', 'text')
        is_admin = data.get('is_admin', False)
        
        if not device_id or not message:
            logger.warning("❌ Admin message missing device_id or message")
            return
        
        # Basic admin verification
        if not is_admin:
            logger.warning("❌ Not an admin request")
            return
        
        logger.info(f"👑 Admin sending message to {device_id[:8]}...: {message[:50]}...")
        
        # Save admin message
        message_id = save_message(device_id, 'Flexia Merchant', message, message_type, True)
        
        # Create message object
        admin_msg = {
            'id': message_id,
            'sender': 'Flexia Merchant',
            'message': message,
            'type': message_type,
            'timestamp': datetime.now().isoformat(),
            'is_admin': True,
            'device_id': device_id
        }
        
        # Send to user's room
        emit('receive_message', admin_msg, room=device_id)
        
        # Also send back to admin for confirmation
        emit('receive_message', admin_msg)
        
        logger.info(f"✅ Admin message delivered to {device_id[:8]}...")
    
    except Exception as e:
        logger.error(f"❌ Admin message error: {str(e)}")
        import traceback
        traceback.print_exc()

@socketio.on('get_all_users')
def handle_get_users(data):
    try:
        is_admin = data.get('is_admin', False)
        
        if not is_admin:
            logger.warning("❌ Unauthorized user list request")
            return
        
        users = get_all_active_users()
        
        emit('users_list', {
            'users': users,
            'total': len(users),
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"📊 Admin requested user list: {len(users)} users")
    
    except Exception as e:
        logger.error(f"❌ Get users error: {str(e)}")

@socketio.on('get_user_messages')
def handle_get_user_messages(data):
    try:
        device_id = data.get('device_id')
        is_admin = data.get('is_admin', False)
        
        if not is_admin or not device_id:
            logger.warning("❌ Unauthorized messages request")
            return
        
        messages = get_user_messages(device_id, 100)
        
        emit('user_messages', {
            'device_id': device_id,
            'messages': messages,
            'total': len(messages)
        })
        
        logger.info(f"📨 Admin requested messages for {device_id[:8]}...: {len(messages)} messages")
    
    except Exception as e:
        logger.error(f"❌ Get user messages error: {str(e)}")

@socketio.on('delete_user')
def handle_delete_user(data):
    try:
        device_id = data.get('device_id')
        is_admin = data.get('is_admin', False)
        
        if not is_admin or not device_id:
            return
        
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Delete messages
            c.execute("DELETE FROM messages WHERE device_id = ?", (device_id,))
            
            # Delete files records
            c.execute("DELETE FROM files WHERE device_id = ?", (device_id,))
            
            # Delete user
            c.execute("DELETE FROM users WHERE device_id = ?", (device_id,))
            
            conn.commit()
        
        emit('user_deleted', {'device_id': device_id})
        
        logger.info(f"🗑️ Admin deleted user: {device_id[:8]}...")
    
    except Exception as e:
        logger.error(f"❌ Delete user error: {str(e)}")

# Background task for periodic cleanup
def background_cleanup():
    """Periodic cleanup task"""
    while True:
        socketio.sleep(3600)  # Run every hour
        cleanup_expired_users()

# Start background task
socketio.start_background_task(background_cleanup)

# Shutdown handler
@atexit.register
def shutdown():
    logger.info("🛑 Server shutting down...")
    cleanup_expired_users()

# Main entry point
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting Flexia Merchant Chat Server on port {port}...")
    logger.info(f"🔧 Admin panel: http://localhost:{port}/{admin_password}.html")
    logger.info(f"📊 Health check: http://localhost:{port}/health")
    logger.info(f"📈 Stats API: http://localhost:{port}/api/stats?admin={admin_password}")
    
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=port, 
                 debug=False,
                 allow_unsafe_werkzeug=True)