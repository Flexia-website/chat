Admin.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Flexia Merchant Admin</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --primary-light: #818cf8;
            --secondary: #8b5cf6;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --dark: #0f172a;
            --light: #f8fafc;
            --sidebar-width: 320px;
            
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-full: 9999px;
            
            --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f1f5f9;
            color: #334155;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Mobile First Layout */
        .admin-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        /* Header */
        .admin-header {
            background: white;
            padding: 16px 20px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-sm);
            z-index: 10;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .menu-toggle {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: var(--radius-md);
            background: #f1f5f9;
            border: none;
            color: #475569;
            font-size: 20px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .menu-toggle:hover {
            background: #e2e8f0;
            transform: scale(1.05);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-logo {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 18px;
        }

        .brand-text h1 {
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
        }

        .brand-text p {
            font-size: 12px;
            color: #64748b;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .admin-badge {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 8px 16px;
            border-radius: var(--radius-full);
            font-size: 14px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .logout-btn {
            padding: 10px 20px;
            background: #fee2e2;
            color: #dc2626;
            border: none;
            border-radius: var(--radius-md);
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
        }

        .logout-btn:hover {
            background: #fecaca;
            transform: translateY(-2px);
        }

        /* Stats Bar */
        .stats-bar {
            background: white;
            padding: 20px;
            border-bottom: 1px solid #e2e8f0;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            box-shadow: var(--shadow-sm);
        }

        .stat-card {
            background: #f8fafc;
            padding: 20px;
            border-radius: var(--radius-lg);
            border: 1px solid #e2e8f0;
            transition: all 0.3s;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
            border-color: var(--primary-light);
        }

        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: var(--radius-full);
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
            margin-bottom: 16px;
        }

        .stat-content h3 {
            font-size: 28px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 4px;
        }

        .stat-content p {
            font-size: 14px;
            color: #64748b;
            font-weight: 500;
        }

        /* Main Content */
        .main-content {
            flex: 1;
            display: flex;
            overflow: hidden;
            position: relative;
        }

        /* Sidebar */
        .sidebar {
            position: fixed;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: white;
            z-index: 1000;
            transition: left 0.3s ease;
            box-shadow: var(--shadow-xl);
            overflow-y: auto;
        }

        .sidebar.active {
            left: 0;
        }

        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid #e2e8f0;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
        }

        .sidebar-header h2 {
            font-size: 24px;
            margin-bottom: 8px;
        }

        .sidebar-header p {
            opacity: 0.9;
            font-size: 14px;
        }

        .users-list {
            padding: 20px;
        }

        .users-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .users-header h3 {
            font-size: 18px;
            color: #1e293b;
        }

        .search-box {
            position: relative;
            width: 100%;
            margin-bottom: 20px;
        }

        .search-box input {
            width: 100%;
            padding: 12px 16px 12px 48px;
            border: 2px solid #e2e8f0;
            border-radius: var(--radius-full);
            font-size: 14px;
            transition: all 0.2s;
            background: #f8fafc;
        }

        .search-box input:focus {
            outline: none;
            border-color: var(--primary);
            background: white;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .search-box i {
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: #94a3b8;
        }

        .user-item {
            display: flex;
            align-items: center;
            padding: 16px;
            border-radius: var(--radius-lg);
            background: #f8fafc;
            margin-bottom: 12px;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }

        .user-item:hover {
            background: #f1f5f9;
            transform: translateX(4px);
        }

        .user-item.active {
            background: white;
            border-color: var(--primary);
            box-shadow: var(--shadow-md);
        }

        .user-avatar {
            width: 48px;
            height: 48px;
            border-radius: var(--radius-full);
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 18px;
            margin-right: 16px;
        }

        .user-info {
            flex: 1;
        }

        .user-name {
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 4px;
        }

        .user-details {
            display: flex;
            gap: 12px;
            font-size: 12px;
            color: #64748b;
        }

        .user-meta {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .user-status {
            width: 10px;
            height: 10px;
            border-radius: var(--radius-full);
            background: #22c55e;
        }

        .user-status.inactive {
            background: #94a3b8;
        }

        /* Chat Area */
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: white;
            overflow: hidden;
        }

        .chat-header {
            padding: 20px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: white;
        }

        .current-user {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .current-user-avatar {
            width: 56px;
            height: 56px;
            border-radius: var(--radius-full);
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 20px;
        }

        .current-user-info h3 {
            font-size: 18px;
            color: #1e293b;
            margin-bottom: 4px;
        }

        .current-user-info p {
            font-size: 14px;
            color: #64748b;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .chat-actions {
            display: flex;
            gap: 12px;
        }

        .action-btn {
            width: 44px;
            height: 44px;
            border-radius: var(--radius-full);
            background: #f1f5f9;
            border: none;
            color: #475569;
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .action-btn:hover {
            background: #e2e8f0;
            transform: scale(1.05);
        }

        .action-btn.primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
        }

        /* Messages Container */
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8fafc;
        }

        .message {
            display: flex;
            flex-direction: column;
            margin-bottom: 20px;
            max-width: 70%;
            animation: messageSlide 0.3s ease;
        }

        @keyframes messageSlide {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.user {
            align-self: flex-start;
        }

        .message.admin {
            align-self: flex-end;
        }

        .message-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }

        .message-sender {
            font-weight: 600;
            color: #1e293b;
            font-size: 14px;
        }

        .message-time {
            font-size: 12px;
            color: #94a3b8;
        }

        .message-bubble {
            padding: 16px;
            border-radius: var(--radius-lg);
            line-height: 1.5;
            box-shadow: var(--shadow-sm);
        }

        .message.user .message-bubble {
            background: white;
            border: 1px solid #e2e8f0;
            border-bottom-left-radius: var(--radius-sm);
        }

        .message.admin .message-bubble {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border-bottom-right-radius: var(--radius-sm);
        }

        .message-image {
            max-width: 300px;
            border-radius: var(--radius-md);
            margin-top: 8px;
            cursor: pointer;
            box-shadow: var(--shadow-md);
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #94a3b8;
            text-align: center;
            padding: 40px;
        }

        .empty-icon {
            font-size: 64px;
            margin-bottom: 20px;
            opacity: 0.5;
        }

        /* Input Area */
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e2e8f0;
            box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
        }

        .input-wrapper {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .input-actions {
            display: flex;
            gap: 8px;
        }

        .admin-action-btn {
            width: 48px;
            height: 48px;
            border-radius: var(--radius-full);
            background: #f1f5f9;
            border: none;
            color: #475569;
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .admin-action-btn:hover {
            background: #e2e8f0;
            transform: translateY(-2px);
        }

        .message-input {
            flex: 1;
            min-height: 48px;
            max-height: 120px;
            padding: 14px 18px;
            border: 2px solid #e2e8f0;
            border-radius: var(--radius-full);
            font-size: 15px;
            font-family: 'Poppins', sans-serif;
            resize: none;
            outline: none;
            background: #f8fafc;
            transition: all 0.2s;
        }

        .message-input:focus {
            border-color: var(--primary);
            background: white;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .send-btn {
            width: 48px;
            height: 48px;
            border-radius: var(--radius-full);
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .send-btn:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: var(--shadow-lg);
        }

        /* Overlay for mobile */
        .overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 999;
        }

        .overlay.active {
            display: block;
        }

        /* Responsive Design */
        @media (min-width: 768px) {
            .admin-container {
                flex-direction: row;
            }
            
            .sidebar {
                position: relative;
                left: 0;
                width: var(--sidebar-width);
                border-right: 1px solid #e2e8f0;
            }
            
            .menu-toggle {
                display: none;
            }
            
            .stats-bar {
                grid-template-columns: repeat(4, 1fr);
            }
        }

        @media (max-width: 767px) {
            .header-right {
                display: none;
            }
            
            .chat-header {
                padding: 16px;
            }
            
            .current-user {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }
            
            .chat-actions {
                position: absolute;
                top: 16px;
                right: 16px;
            }
            
            .message {
                max-width: 85%;
            }
            
            .message-image {
                max-width: 100%;
            }
        }

        /* Loading State */
        .loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            gap: 20px;
        }

        .spinner {
            width: 48px;
            height: 48px;
            border: 4px solid #e2e8f0;
            border-top-color: var(--primary);
            border-radius: var(--radius-full);
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 6px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f5f9;
        }

        ::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: var(--radius-full);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
    </style>
</head>
<body>
    <div class="admin-container">
        <!-- Header -->
        <header class="admin-header">
            <div class="header-left">
                <button class="menu-toggle" onclick="toggleSidebar()">
                    <i class="fas fa-bars"></i>
                </button>
                <div class="brand">
                    <div class="brand-logo">FM</div>
                    <div class="brand-text">
                        <h1>Flexia Merchant</h1>
                        <p>Admin Dashboard</p>
                    </div>
                </div>
            </div>
            <div class="header-right">
                <div class="admin-badge">
                    <i class="fas fa-shield-alt"></i>
                    <span>Admin Panel</span>
                </div>
                <button class="logout-btn" onclick="logout()">
                    <i class="fas fa-sign-out-alt"></i>
                    Logout
                </button>
            </div>
        </header>

        <!-- Stats Bar -->
        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-users"></i>
                </div>
                <div class="stat-content">
                    <h3 id="totalUsers">0</h3>
                    <p>Active Users</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-comments"></i>
                </div>
                <div class="stat-content">
                    <h3 id="totalMessages">0</h3>
                    <p>Total Messages</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <div class="stat-content">
                    <h3 id="activeChats">0</h3>
                    <p>Active Chats</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-clock"></i>
                </div>
                <div class="stat-content">
                    <h3 id="todayMessages">0</h3>
                    <p>Today's Messages</p>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Sidebar -->
            <div class="sidebar" id="sidebar">
                <div class="sidebar-header">
                    <h2>User Management</h2>
                    <p>Manage all user conversations</p>
                </div>
                
                <div class="users-list">
                    <div class="search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" id="userSearch" placeholder="Search users..." onkeyup="searchUsers()">
                    </div>
                    
                    <div class="users-header">
                        <h3>Active Conversations</h3>
                        <button class="action-btn" onclick="refreshUsers()" title="Refresh">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                    
                    <div class="users-container" id="usersContainer">
                        <!-- Users will be loaded here -->
                        <div class="loading">
                            <div class="spinner"></div>
                            <p>Loading users...</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Overlay for mobile -->
            <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>

            <!-- Chat Area -->
            <div class="chat-area" id="chatArea">
                <div class="chat-header">
                    <div class="current-user">
                        <div class="current-user-avatar" id="currentUserAvatar">?</div>
                        <div class="current-user-info">
                            <h3 id="currentUserName">Select a user to chat</h3>
                            <p id="currentUserDetails">
                                <i class="fas fa-info-circle"></i>
                                Choose from the sidebar
                            </p>
                        </div>
                    </div>
                    <div class="chat-actions">
                        <button class="action-btn" onclick="clearChat()" title="Clear chat">
                            <i class="fas fa-trash"></i>
                        </button>
                        <button class="action-btn" onclick="exportChat()" title="Export chat">
                            <i class="fas fa-download"></i>
                        </button>
                    </div>
                </div>

                <div class="messages-container" id="messagesContainer">
                    <div class="empty-state" id="emptyState">
                        <div class="empty-icon">
                            <i class="fas fa-comment-slash"></i>
                        </div>
                        <h3>No conversation selected</h3>
                        <p>Select a user from the sidebar to view and send messages</p>
                    </div>
                    <!-- Messages will be loaded here -->
                </div>

                <div class="input-area" id="inputArea" style="display: none;">
                    <div class="input-wrapper">
                        <div class="input-actions">
                            <button class="admin-action-btn" onclick="uploadAdminImage()" title="Upload image">
                                <i class="fas fa-image"></i>
                            </button>
                            <button class="admin-action-btn" onclick="showTemplates()" title="Quick replies">
                                <i class="fas fa-bolt"></i>
                            </button>
                        </div>
                        <textarea 
                            class="message-input" 
                            id="adminMessageInput" 
                            placeholder="Type your message as Flexia Merchant..."
                            rows="1"
                            oninput="autoResize(this)"
                            onkeydown="handleAdminKeyDown(event)"
                        ></textarea>
                        <button class="send-btn" onclick="sendAdminMessage()" title="Send message">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Hidden File Input -->
        <input type="file" id="adminImageInput" accept="image/*" style="display: none;" onchange="handleAdminImageSelect(event)">
    </div>

    <!-- Socket.io -->
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    
    <script>
        // Global variables
        let socket;
        let selectedUser = null;
        let allUsers = [];
        let isSidebarOpen = false;

        // Initialize admin panel
        function initAdmin() {
            // Connect to server
            socket = io({
                transports: ['websocket', 'polling'],
                reconnection: true
            });

            // Socket event handlers
            socket.on('connect', () => {
                console.log('Admin connected');
                loadUsers();
                
                // Refresh users every 30 seconds
                setInterval(loadUsers, 30000);
            });

            socket.on('users_list', (data) => {
                displayUsers(data.users);
                updateStats(data.users);
            });

            socket.on('user_messages', (data) => {
                if (selectedUser && data.device_id === selectedUser.device_id) {
                    displayMessages(data.messages);
                }
            });

            socket.on('receive_message', (data) => {
                if (selectedUser && data.device_id === selectedUser.device_id) {
                    addMessageToChat(data);
                }
            });

            // Auto-resize sidebar for mobile
            if (window.innerWidth < 768) {
                closeSidebar();
            }
        }

        // Toggle sidebar on mobile
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('overlay');
            
            if (window.innerWidth < 768) {
                isSidebarOpen = !isSidebarOpen;
                sidebar.classList.toggle('active', isSidebarOpen);
                overlay.classList.toggle('active', isSidebarOpen);
            }
        }

        function closeSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('overlay');
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            isSidebarOpen = false;
        }

        // Load all users
        function loadUsers() {
            if (socket) {
                socket.emit('get_all_users', {
                    is_admin: true
                });
            }
        }

        // Display users in sidebar
        function displayUsers(users) {
            allUsers = users;
            const container = document.getElementById('usersContainer');
            
            if (users.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">
                            <i class="fas fa-user-slash"></i>
                        </div>
                        <h3>No active users</h3>
                        <p>Users will appear here when they connect</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = users.map(user => `
                <div class="user-item ${selectedUser?.device_id === user.device_id ? 'active' : ''}" 
                     onclick="selectUser('${user.device_id}')">
                    <div class="user-avatar">${user.username.charAt(0)}</div>
                    <div class="user-info">
                        <div class="user-name">${user.username}</div>
                        <div class="user-details">
                            <div class="user-meta">
                                <i class="fas fa-comment"></i>
                                <span>${user.message_count} messages</span>
                            </div>
                            <div class="user-meta">
                                <i class="fas fa-clock"></i>
                                <span>${formatTimeAgo(user.created_at)}</span>
                            </div>
                        </div>
                    </div>
                    <div class="user-status ${user.message_count > 0 ? '' : 'inactive'}"></div>
                </div>
            `).join('');
        }

        // Update statistics
        function updateStats(users) {
            const totalUsers = users.length;
            const totalMessages = users.reduce((sum, user) => sum + user.message_count, 0);
            const activeChats = users.filter(u => u.message_count > 0).length;
            
            // Calculate today's messages
            const today = new Date().toISOString().split('T')[0];
            const todayMessages = users.reduce((sum, user) => {
                // Simple approximation - in production, count actual today's messages
                return sum + Math.min(user.message_count, 5); 
            }, 0);
            
            document.getElementById('totalUsers').textContent = totalUsers;
            document.getElementById('totalMessages').textContent = totalMessages.toLocaleString();
            document.getElementById('activeChats').textContent = activeChats;
            document.getElementById('todayMessages').textContent = todayMessages;
        }

        // Format time ago
        function formatTimeAgo(timestamp) {
            const now = new Date();
            const time = new Date(timestamp);
            const diffMs = now - time;
            const diffMins = Math.floor(diffMs / 60000);
            
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
            return `${Math.floor(diffMins / 1440)}d ago`;
        }

        // Search users
        function searchUsers() {
            const searchTerm = document.getElementById('userSearch').value.toLowerCase();
            const filteredUsers = allUsers.filter(user => 
                user.username.toLowerCase().includes(searchTerm) ||
                user.device_id.toLowerCase().includes(searchTerm)
            );
            
            const container = document.getElementById('usersContainer');
            if (filteredUsers.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-search"></i>
                        <p>No users found</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = filteredUsers.map(user => `
                <div class="user-item ${selectedUser?.device_id === user.device_id ? 'active' : ''}" 
                     onclick="selectUser('${user.device_id}')">
                    <div class="user-avatar">${user.username.charAt(0)}</div>
                    <div class="user-info">
                        <div class="user-name">${user.username}</div>
                        <div class="user-details">
                            <span>${user.message_count} messages</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        // Refresh users
        function refreshUsers() {
            loadUsers();
            showNotification('Users list refreshed', 'success');
        }

        // Select a user
        function selectUser(deviceId) {
            const user = allUsers.find(u => u.device_id === deviceId);
            if (!user) return;
            
            selectedUser = user;
            
            // Update UI
            updateSelectedUserUI(user);
            
            // Load messages
            if (socket) {
                socket.emit('get_user_messages', {
                    device_id: deviceId,
                    is_admin: true
                });
            }
            
            // Close sidebar on mobile
            if (window.innerWidth < 768) {
                closeSidebar();
            }
        }

        // Update selected user UI
        function updateSelectedUserUI(user) {
            // Update chat header
            document.getElementById('currentUserAvatar').textContent = user.username.charAt(0);
            document.getElementById('currentUserName').textContent = user.username;
            document.getElementById('currentUserDetails').innerHTML = `
                <i class="fas fa-id-card"></i>
                Device ID: ${user.device_id.substring(0, 12)}... |
                <i class="fas fa-comment"></i>
                ${user.message_count} messages
            `;
            
            // Show input area
            document.getElementById('inputArea').style.display = 'block';
            document.getElementById('emptyState').style.display = 'none';
            
            // Update active user in sidebar
            document.querySelectorAll('.user-item').forEach(item => {
                item.classList.remove('active');
            });
            
            const selectedItem = Array.from(document.querySelectorAll('.user-item'))
                .find(item => item.querySelector('.user-name').textContent === user.username);
            
            if (selectedItem) {
                selectedItem.classList.add('active');
            }
        }

        // Display messages
        function displayMessages(messages) {
            const container = document.getElementById('messagesContainer');
            container.innerHTML = '';
            
            if (messages.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">
                            <i class="fas fa-comments"></i>
                        </div>
                        <h3>No messages yet</h3>
                        <p>Start a conversation with ${selectedUser.username}</p>
                    </div>
                `;
                return;
            }
            
            messages.forEach(message => {
                addMessageToChat(message);
            });
            
            // Scroll to bottom
            scrollToBottom();
        }

        // Add message to chat
        function addMessageToChat(data) {
            const container = document.getElementById('messagesContainer');
            
            // Remove empty state if present
            const emptyState = document.getElementById('emptyState');
            if (emptyState && emptyState.style.display !== 'none') {
                emptyState.style.display = 'none';
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${data.is_admin ? 'admin' : 'user'}`;
            
            const time = new Date(data.timestamp).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            let content = '';
            if (data.type === 'image') {
                content = `
                    <img src="${data.message}" 
                         alt="Image" 
                         class="message-image"
                         onclick="openImageModal('${data.message}')">
                `;
            } else {
                content = `<p>${escapeHtml(data.message)}</p>`;
            }
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <div class="message-sender">${data.is_admin ? 'You (Flexia Merchant)' : data.sender}</div>
                    <div class="message-time">${time}</div>
                </div>
                <div class="message-bubble">
                    ${content}
                </div>
            `;
            
            container.appendChild(messageDiv);
            scrollToBottom();
        }

        // Send admin message
        function sendAdminMessage() {
            const input = document.getElementById('adminMessageInput');
            const message = input.value.trim();
            
            if (message && socket && selectedUser) {
                socket.emit('admin_message', {
                    device_id: selectedUser.device_id,
                    message: message,
                    type: 'text',
                    is_admin: true
                });
                
                input.value = '';
                autoResize(input);
                
                // Add message to local display immediately
                const tempMessage = {
                    id: 'temp_' + Date.now(),
                    sender: 'Flexia Merchant',
                    message: message,
                    type: 'text',
                    timestamp: new Date().toISOString(),
                    is_admin: true
                };
                
                addMessageToChat(tempMessage);
            }
        }

        // Handle admin key events
        function handleAdminKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendAdminMessage();
            }
        }

        // Image handling for admin
        function uploadAdminImage() {
            document.getElementById('adminImageInput').click();
        }

        function handleAdminImageSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            if (!file.type.match('image.*')) {
                showNotification('Please select an image file', 'error');
                return;
            }
            
            if (file.size > 10 * 1024 * 1024) {
                showNotification('Image size should be less than 10MB', 'error');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                if (socket && selectedUser) {
                    socket.emit('upload_image', {
                        device_id: selectedUser.device_id,
                        image: e.target.result,
                        filename: file.name,
                        is_admin: true
                    });
                    
                    // Add temporary message
                    const tempMessage = {
                        id: 'temp_' + Date.now(),
                        sender: 'Flexia Merchant',
                        message: 'Sending image...',
                        type: 'text',
                        timestamp: new Date().toISOString(),
                        is_admin: true
                    };
                    
                    addMessageToChat(tempMessage);
                }
            };
            reader.readAsDataURL(file);
            
            event.target.value = '';
        }

        // Clear chat
        function clearChat() {
            if (selectedUser && confirm('Clear all messages with this user?')) {
                const container = document.getElementById('messagesContainer');
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">
                            <i class="fas fa-comments"></i>
                        </div>
                        <h3>Chat cleared</h3>
                        <p>Start a new conversation with ${selectedUser.username}</p>
                    </div>
                `;
            }
        }

        // Export chat
        function exportChat() {
            if (!selectedUser) {
                showNotification('Select a user first', 'error');
                return;
            }
            
            const messages = Array.from(document.querySelectorAll('.message')).map(msg => {
                const sender = msg.querySelector('.message-sender').textContent;
                const time = msg.querySelector('.message-time').textContent;
                const text = msg.querySelector('.message-bubble p')?.textContent || '[Image]';
                return `${time} - ${sender}: ${text}`;
            }).join('\n');
            
            const blob = new Blob([messages], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `chat_${selectedUser.username}_${new Date().toISOString().split('T')[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }

        // Show quick reply templates
        function showTemplates() {
            const templates = [
                'Hello! How can I help you today?',
                'Thank you for your message!',
                'I\'ll check that for you right away.',
                'Is there anything else I can help with?',
                'Please provide more details.',
                'Your request has been processed.'
            ];
            
            const input = document.getElementById('adminMessageInput');
            const templateList = document.createElement('div');
            templateList.className = 'templates-dropdown';
            templateList.innerHTML = templates.map(t => `
                <div class="template-item" onclick="selectTemplate('${t}')">${t}</div>
            `).join('');
            
            document.body.appendChild(templateList);
            
            // Position dropdown
            const rect = input.getBoundingClientRect();
            templateList.style.position = 'fixed';
            templateList.style.left = rect.left + 'px';
            templateList.style.bottom = window.innerHeight - rect.top + 10 + 'px';
            templateList.style.zIndex = '1000';
            
            // Close on click outside
            setTimeout(() => {
                document.addEventListener('click', function closeTemplates(e) {
                    if (!templateList.contains(e.target) && e.target !== input) {
                        templateList.remove();
                        document.removeEventListener('click', closeTemplates);
                    }
                });
            }, 0);
        }

        function selectTemplate(text) {
            document.getElementById('adminMessageInput').value = text;
            autoResize(document.getElementById('adminMessageInput'));
        }

        // Image modal
        function openImageModal(src) {
            const modal = document.createElement('div');
            modal.className = 'image-modal';
            modal.innerHTML = `
                <div class="modal-overlay" onclick="this.parentElement.remove()">
                    <div class="modal-content">
                        <img src="${src}" alt="Full size">
                        <button class="close-modal" onclick="this.parentElement.parentElement.remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        // Auto-resize textarea
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }

        // Scroll to bottom
        function scrollToBottom() {
            const container = document.getElementById('messagesContainer');
            container.scrollTop = container.scrollHeight;
        }

        // Show notification
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                <span>${message}</span>
            `;
            document.body.appendChild(notification);
            
            setTimeout(() => notification.remove(), 3000);
        }

        // Escape HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.InnerHTML ;
        }

        // Logout
        function logout() {
            if (confirm('Are you sure you want to logout?')) {
                window.location.href = '/';
            }
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', initAdmin);
    </script>
</body>
</html>

Index.html

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Flexia Merchant Chat</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --primary-light: #818cf8;
            --secondary: #8b5cf6;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --dark: #1f2937;
            --light: #f8fafc;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --radius-full: 9999px;
            
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            
            --transition-fast: 150ms;
            --transition-normal: 250ms;
            --transition-slow: 350ms;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 16px;
            color: var(--gray-800);
            line-height: 1.5;
        }

        /* Main Container */
        .chat-app {
            width: 100%;
            max-width: 480px;
            height: calc(100vh - 32px);
            background: white;
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-xl);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        /* Header */
        .chat-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 20px 16px;
            position: relative;
            z-index: 10;
            box-shadow: var(--shadow-md);
        }

        .header-content {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .logo-container {
            width: 52px;
            height: 52px;
            background: white;
            border-radius: var(--radius-full);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow-lg);
        }

        .logo {
            width: 36px;
            height: 36px;
            border-radius: var(--radius-full);
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 18px;
        }

        .brand-info h1 {
            font-family: 'Poppins', sans-serif;
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 4px;
            letter-spacing: -0.3px;
        }

        .brand-info p {
            font-size: 14px;
            opacity: 0.9;
            font-weight: 400;
        }

        .user-badge {
            position: absolute;
            top: 20px;
            right: 16px;
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 8px 14px;
            border-radius: var(--radius-full);
            font-size: 13px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .user-badge i {
            font-size: 12px;
        }

        /* User Info Panel */
        .user-panel {
            background: var(--gray-100);
            padding: 14px 16px;
            border-bottom: 1px solid var(--gray-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }

        .user-details {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: var(--radius-full);
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 15px;
        }

        .user-text {
            display: flex;
            flex-direction: column;
        }

        .username {
            font-weight: 600;
            color: var(--gray-800);
        }

        .user-id {
            font-size: 11px;
            color: var(--gray-500);
        }

        .expiry-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: white;
            border-radius: var(--radius-full);
            font-weight: 500;
            font-size: 12px;
            box-shadow: var(--shadow-sm);
        }

        .expiry-indicator.warning {
            color: var(--danger);
            background: rgba(239, 68, 68, 0.1);
        }

        .expiry-indicator.success {
            color: var(--success);
            background: rgba(16, 185, 129, 0.1);
        }

        /* Messages Container */
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px 16px;
            background: linear-gradient(180deg, var(--gray-50) 0%, white 100%);
            position: relative;
            scroll-behavior: smooth;
        }

        .messages-scroll {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* Date Separator */
        .date-separator {
            text-align: center;
            margin: 16px 0;
            position: relative;
        }

        .date-separator span {
            background: white;
            padding: 6px 16px;
            border-radius: var(--radius-full);
            font-size: 13px;
            font-weight: 500;
            color: var(--gray-500);
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--gray-200);
        }

        /* Message Bubbles */
        .message {
            display: flex;
            flex-direction: column;
            max-width: 85%;
            animation: messageAppear 0.3s ease-out;
        }

        @keyframes messageAppear {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.sent {
            align-self: flex-end;
        }

        .message.received {
            align-self: flex-start;
        }

        .message-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
            padding: 0 8px;
        }

        .message-sender {
            font-size: 13px;
            font-weight: 600;
            color: var(--gray-700);
        }

        .message-time {
            font-size: 11px;
            color: var(--gray-500);
        }

        .message-bubble {
            padding: 14px 18px;
            border-radius: var(--radius-lg);
            position: relative;
            word-wrap: break-word;
            line-height: 1.5;
            box-shadow: var(--shadow-sm);
        }

        .message.sent .message-bubble {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border-bottom-right-radius: var(--radius-sm);
            border-top-left-radius: var(--radius-lg);
        }

        .message.received .message-bubble {
            background: white;
            color: var(--gray-800);
            border: 1px solid var(--gray-200);
            border-bottom-left-radius: var(--radius-sm);
            border-top-right-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
        }

        .message-bubble p {
            margin-bottom: 4px;
        }

        .message-bubble p:last-child {
            margin-bottom: 0;
        }

        /* Message Status */
        .message-status {
            display: flex;
            justify-content: flex-end;
            gap: 4px;
            margin-top: 6px;
            font-size: 11px;
            color: var(--gray-400);
        }

        /* Typing Indicator */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 18px;
            background: white;
            border-radius: var(--radius-lg);
            border: 1px solid var(--gray-200);
            width: fit-content;
            margin-left: 8px;
            box-shadow: var(--shadow-sm);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .typing-dots {
            display: flex;
            gap: 4px;
        }

        .typing-dots span {
            width: 8px;
            height: 8px;
            background: var(--gray-400);
            border-radius: var(--radius-full);
            animation: typingDot 1.4s infinite;
        }

        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typingDot {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-4px); }
        }

        /* Image Messages */
        .message-image {
            max-width: 100%;
            border-radius: var(--radius-md);
            margin-top: 8px;
            cursor: pointer;
            transition: transform var(--transition-normal);
            box-shadow: var(--shadow-md);
        }

        .message-image:hover {
            transform: scale(1.02);
        }

        /* Input Area */
        .input-area {
            padding: 16px;
            background: white;
            border-top: 1px solid var(--gray-200);
            box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
        }

        .input-wrapper {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .input-actions {
            display: flex;
            gap: 8px;
        }

        .action-btn {
            width: 48px;
            height: 48px;
            border-radius: var(--radius-full);
            background: var(--gray-100);
            border: none;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--gray-600);
            font-size: 20px;
            cursor: pointer;
            transition: all var(--transition-fast);
            flex-shrink: 0;
        }

        .action-btn:hover {
            background: var(--gray-200);
            transform: translateY(-2px);
        }

        .action-btn.primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            box-shadow: var(--shadow-md);
        }

        .action-btn.primary:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: var(--shadow-lg);
        }

        .message-input {
            flex: 1;
            min-height: 48px;
            max-height: 120px;
            padding: 14px 18px;
            border: 2px solid var(--gray-200);
            border-radius: var(--radius-full);
            font-size: 15px;
            font-family: 'Inter', sans-serif;
            resize: none;
            outline: none;
            transition: all var(--transition-fast);
            background: var(--gray-50);
        }

        .message-input:focus {
            border-color: var(--primary);
            background: white;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .message-input::placeholder {
            color: var(--gray-400);
        }

        /* Image Preview */
        .image-preview {
            margin-bottom: 16px;
            padding: 16px;
            background: var(--gray-50);
            border-radius: var(--radius-lg);
            border: 2px dashed var(--gray-300);
            position: relative;
        }

        .preview-image {
            max-width: 100%;
            max-height: 200px;
            border-radius: var(--radius-md);
            display: block;
            margin: 0 auto;
        }

        .preview-actions {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 12px;
        }

        .preview-btn {
            padding: 8px 16px;
            border-radius: var(--radius-full);
            border: none;
            font-weight: 500;
            font-size: 14px;
            cursor: pointer;
            transition: all var(--transition-fast);
        }

        .preview-btn.send {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
        }

        .preview-btn.cancel {
            background: var(--gray-200);
            color: var(--gray-700);
        }

        .preview-btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        /* Image Modal */
        .image-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            animation: modalFadeIn var(--transition-normal);
        }

        @keyframes modalFadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .modal-content {
            max-width: 90%;
            max-height: 90%;
            position: relative;
        }

        .modal-image {
            width: 100%;
            height: auto;
            border-radius: var(--radius-lg);
        }

        .close-modal {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            width: 48px;
            height: 48px;
            border-radius: var(--radius-full);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            cursor: pointer;
            transition: all var(--transition-fast);
        }

        .close-modal:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: rotate(90deg);
        }

        /* Welcome Screen */
        .welcome-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 24px;
            text-align: center;
            height: 100%;
        }

        .welcome-icon {
            width: 120px;
            height: 120px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-radius: var(--radius-full);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 48px;
            margin-bottom: 24px;
            box-shadow: var(--shadow-lg);
            animation: float 3s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        .welcome-text h2 {
            font-family: 'Poppins', sans-serif;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 12px;
            color: var(--gray-900);
        }

        .welcome-text p {
            font-size: 16px;
            color: var(--gray-600);
            margin-bottom: 32px;
            max-width: 320px;
        }

        /* Scroll to Bottom Button */
        .scroll-bottom {
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-radius: var(--radius-full);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            opacity: 0;
            transform: translateY(20px);
            transition: all var(--transition-normal);
            z-index: 5;
        }

        .scroll-bottom.visible {
            opacity: 1;
            transform: translateY(0);
        }

        .scroll-bottom:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-xl);
        }

        /* Loading State */
        .loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            gap: 20px;
        }

        .spinner {
            width: 48px;
            height: 48px;
            border: 4px solid var(--gray-200);
            border-top-color: var(--primary);
            border-radius: var(--radius-full);
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Empty State */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 24px;
            text-align: center;
            color: var(--gray-500);
        }

        .empty-icon {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }

        /* Connection Status */
        .connection-status {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 24px;
            border-radius: var(--radius-full);
            font-weight: 500;
            font-size: 14px;
            z-index: 1001;
            display: flex;
            align-items: center;
            gap: 8px;
            backdrop-filter: blur(10px);
            box-shadow: var(--shadow-lg);
            animation: slideUp 0.3s ease-out;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }

        .connection-status.connected {
            background: rgba(16, 185, 129, 0.9);
            color: white;
        }

        .connection-status.disconnected {
            background: rgba(239, 68, 68, 0.9);
            color: white;
        }

        /* Responsive Design */
        @media (max-width: 480px) {
            .chat-app {
                height: 100vh;
                max-width: 100%;
                border-radius: 0;
            }
            
            .chat-header {
                padding: 16px;
            }
            
            .brand-info h1 {
                font-size: 20px;
            }
            
            .message {
                max-width: 90%;
            }
            
            .input-area {
                padding: 12px;
            }
            
            .action-btn {
                width: 44px;
                height: 44px;
            }
        }

        @media (min-width: 768px) {
            .chat-app {
                max-width: 800px;
                height: 90vh;
            }
            
            .messages-container {
                padding: 24px;
            }
        }

        /* Dark Mode Support */
        @media (prefers-color-scheme: dark) {
            :root {
                --light: #1f2937;
                --gray-100: #111827;
                --gray-200: #1f2937;
                --gray-300: #374151;
                --gray-400: #6b7280;
                --gray-500: #9ca3af;
                --gray-600: #d1d5db;
                --gray-700: #e5e7eb;
                --gray-800: #f3f4f6;
                --gray-900: #f9fafb;
            }
            
            .chat-app {
                background: var(--gray-100);
                color: var(--gray-800);
            }
            
            .message.received .message-bubble {
                background: var(--gray-900);
                border-color: var(--gray-800);
            }
            
            .input-area {
                background: var(--gray-100);
                border-color: var(--gray-800);
            }
            
            .message-input {
                background: var(--gray-900);
                border-color: var(--gray-800);
                color: var(--gray-100);
            }
        }

        /* Smooth Scrolling */
        .messages-container {
            scroll-behavior: smooth;
            -webkit-overflow-scrolling: touch;
        }

        /* Hide scrollbar but keep functionality */
        .messages-container::-webkit-scrollbar {
            width: 6px;
        }

        .messages-container::-webkit-scrollbar-track {
            background: transparent;
        }

        .messages-container::-webkit-scrollbar-thumb {
            background: var(--gray-300);
            border-radius: var(--radius-full);
        }

        .messages-container::-webkit-scrollbar-thumb:hover {
            background: var(--gray-400);
        }

        /* iOS Safe Areas */
        @supports (padding: max(0px)) {
            body {
                padding-left: max(16px, env(safe-area-inset-left));
                padding-right: max(16px, env(safe-area-inset-right));
                padding-bottom: max(16px, env(safe-area-inset-bottom));
            }
        }
    </style>
</head>
<body>
    <div class="chat-app">
        <!-- Header -->
        <div class="chat-header">
            <div class="header-content">
                <div class="logo-container">
                    <div class="logo">FM</div>
                </div>
                <div class="brand-info">
                    <h1>Flexia Merchant</h1>
                    <p>Your personal merchant assistant</p>
                </div>
                <div class="user-badge" id="connectionStatus">
                    <i class="fas fa-circle"></i>
                    <span>Connecting...</span>
                </div>
            </div>
        </div>

        <!-- User Info -->
        <div class="user-panel">
            <div class="user-details">
                <div class="user-avatar" id="userAvatar">U</div>
                <div class="user-text">
                    <div class="username" id="username">Loading...</div>
                    <div class="user-id" id="deviceId">Device ID: ...</div>
                </div>
            </div>
            <div class="expiry-indicator success" id="expiryIndicator">
                <i class="fas fa-calendar-check"></i>
                <span id="daysLeft">7 days left</span>
            </div>
        </div>

        <!-- Messages Container -->
        <div class="messages-container" id="messagesContainer">
            <div class="messages-scroll" id="messagesScroll">
                <!-- Welcome Screen -->
                <div class="welcome-screen" id="welcomeScreen">
                    <div class="welcome-icon">
                        <i class="fas fa-comments"></i>
                    </div>
                    <div class="welcome-text">
                        <h2>Welcome to Flexia Merchant</h2>
                        <p>Start a conversation with your personal merchant assistant. Send messages, share images, and get instant support.</p>
                    </div>
                </div>
                <!-- Messages will be inserted here -->
            </div>
            
            <!-- Scroll to Bottom Button -->
            <div class="scroll-bottom" id="scrollBottom" onclick="scrollToBottom()">
                <i class="fas fa-arrow-down"></i>
            </div>
        </div>

        <!-- Image Preview -->
        <div class="image-preview" id="imagePreview" style="display: none;">
            <img class="preview-image" id="previewImage" src="" alt="Preview">
            <div class="preview-actions">
                <button class="preview-btn cancel" onclick="cancelImageUpload()">
                    <i class="fas fa-times"></i> Cancel
                </button>
                <button class="preview-btn send" onclick="sendImage()">
                    <i class="fas fa-paper-plane"></i> Send Image
                </button>
            </div>
        </div>

        <!-- Input Area -->
        <div class="input-area">
            <div class="input-wrapper">
                <div class="input-actions">
                    <button class="action-btn" onclick="openImagePicker()" title="Upload image">
                        <i class="fas fa-image"></i>
                    </button>
                    <button class="action-btn" onclick="openEmojiPicker()" title="Add emoji">
                        <i class="fas fa-smile"></i>
                    </button>
                </div>
                <textarea 
                    class="message-input" 
                    id="messageInput" 
                    placeholder="Type your message..."
                    rows="1"
                    oninput="autoResize(this)"
                    onkeydown="handleKeyDown(event)"
                ></textarea>
                <button class="action-btn primary" onclick="sendMessage()" title="Send message">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>

        <!-- Hidden File Input -->
        <input type="file" id="imageInput" accept="image/*" style="display: none;" onchange="handleImageSelect(event)">

        <!-- Image Modal -->
        <div class="image-modal" id="imageModal" onclick="closeImageModal()">
            <div class="close-modal" onclick="closeImageModal(event)">
                <i class="fas fa-times"></i>
            </div>
            <div class="modal-content">
                <img class="modal-image" id="modalImage" src="" alt="Full size">
            </div>
        </div>
    </div>

    <!-- Socket.io -->
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    
    <!-- Emoji Picker (CDN) -->
    <script src="https://cdn.jsdelivr.net/npm/emoji-picker-element@1.12.0/dist/index.min.js"></script>
    
    <script>
        // Global variables
        let socket;
        let deviceId;
        let username;
        let expiryDate;
        let selectedImage = null;
        let isTyping = false;
        let lastScrollPosition = 0;
        let typingTimeout;

        // Initialize chat application
        function initChat() {
            // Get or create device ID
            deviceId = getDeviceId();
            
            // Connect to server
            connectSocket();
            
            // Setup event listeners
            setupEventListeners();
            
            // Initialize UI
            initUI();
        }

        // Get or create device ID
        function getDeviceId() {
            let id = localStorage.getItem('deviceId');
            if (!id) {
                id = 'device_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('deviceId', id);
            }
            return id;
        }

        // Connect to Socket.io server
        function connectSocket() {
            socket = io({
                query: { device_id: deviceId },
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000
            });

            // Socket event handlers
            socket.on('connect', () => {
                updateConnectionStatus(true);
                console.log('Connected to server');
            });

            socket.on('user_info', (data) => {
                updateUserInfo(data);
                hideWelcomeScreen();
            });

            socket.on('receive_message', (data) => {
                addMessage(data);
                hideTypingIndicator();
            });

            socket.on('error', (data) => {
                showNotification(data.message, 'error');
            });

            socket.on('disconnect', () => {
                updateConnectionStatus(false);
            });

            socket.on('connect_error', () => {
                updateConnectionStatus(false);
            });
        }

        // Update connection status
        function updateConnectionStatus(connected) {
            const statusElement = document.getElementById('connectionStatus');
            if (connected) {
                statusElement.innerHTML = '<i class="fas fa-circle" style="color: #10b981;"></i><span>Connected</span>';
                statusElement.style.color = '#10b981';
            } else {
                statusElement.innerHTML = '<i class="fas fa-circle" style="color: #ef4444;"></i><span>Connecting...</span>';
                statusElement.style.color = '#ef4444';
            }
        }

        // Update user info display
        function updateUserInfo(data) {
            username = data.username;
            expiryDate = new Date(data.expires_at);
            
            // Update UI elements
            document.getElementById('username').textContent = username;
            document.getElementById('deviceId').textContent = `ID: ${deviceId.substring(0, 12)}...`;
            document.getElementById('userAvatar').textContent = username.charAt(0).toUpperCase();
            
            // Update expiry indicator
            updateExpiryIndicator();
        }

        // Update expiry indicator
        function updateExpiryIndicator() {
            const now = new Date();
            const daysLeft = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
            const indicator = document.getElementById('expiryIndicator');
            
            document.getElementById('daysLeft').textContent = `${daysLeft} day${daysLeft !== 1 ? 's' : ''} left`;
            
            if (daysLeft <= 2) {
                indicator.className = 'expiry-indicator warning';
            } else if (daysLeft <= 7) {
                indicator.className = 'expiry-indicator';
            } else {
                indicator.className = 'expiry-indicator success';
            }
        }

        // Hide welcome screen
        function hideWelcomeScreen() {
            const welcomeScreen = document.getElementById('welcomeScreen');
            welcomeScreen.style.display = 'none';
        }

        // Add message to chat
        function addMessage(data) {
            const messagesScroll = document.getElementById('messagesScroll');
            
            // Create message element
            const messageElement = createMessageElement(data);
            
            // Add to chat
            messagesScroll.appendChild(messageElement);
            
            // Scroll to bottom
            scrollToBottom();
        }

        // Create message element
        function createMessageElement(data) {
            const isSent = !data.is_admin;
            const time = new Date(data.timestamp).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
            
            let content = '';
            if (data.type === 'image') {
                content = `
                    <img src="${data.message}" 
                         alt="Shared image" 
                         class="message-image"
                         onclick="openImageModal('${data.message}')"
                         loading="lazy">
                `;
            } else {
                content = `<p>${escapeHtml(data.message)}</p>`;
            }
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <div class="message-sender">${isSent ? 'You' : data.sender}</div>
                    <div class="message-time">${time}</div>
                </div>
                <div class="message-bubble">
                    ${content}
                </div>
                ${isSent ? '<div class="message-status"><i class="fas fa-check"></i></div>' : ''}
            `;
            
            return messageDiv;
        }

        // Escape HTML to prevent XSS
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Send message
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (message && socket) {
                // Clear input
                input.value = '';
                autoResize(input);
                
                // Send via socket
                socket.emit('send_message', {
                    device_id: deviceId,
                    message: message,
                    type: 'text'
                });
                
                // Show typing indicator for bot
                showTypingIndicator();
            }
        }

        // Show typing indicator
        function showTypingIndicator() {
            const messagesScroll = document.getElementById('messagesScroll');
            const existingIndicator = document.querySelector('.typing-indicator');
            
            if (!existingIndicator) {
                const indicator = document.createElement('div');
                indicator.className = 'typing-indicator';
                indicator.innerHTML = `
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    <span>Flexia Merchant is typing...</span>
                `;
                messagesScroll.appendChild(indicator);
                scrollToBottom();
            }
            
            // Clear existing timeout
            if (typingTimeout) {
                clearTimeout(typingTimeout);
            }
            
            // Remove indicator after 5 seconds
            typingTimeout = setTimeout(hideTypingIndicator, 5000);
        }

        // Hide typing indicator
        function hideTypingIndicator() {
            const indicator = document.querySelector('.typing-indicator');
            if (indicator) {
                indicator.remove();
            }
            if (typingTimeout) {
                clearTimeout(typingTimeout);
            }
        }

        // Image handling
        function openImagePicker() {
            document.getElementById('imageInput').click();
        }

        function handleImageSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            // Validate file type
            if (!file.type.match('image.*')) {
                showNotification('Please select an image file', 'error');
                return;
            }
            
            // Validate file size (max 10MB)
            if (file.size > 10 * 1024 * 1024) {
                showNotification('Image size should be less than 10MB', 'error');
                return;
            }
            
            // Show preview
            const reader = new FileReader();
            reader.onload = function(e) {
                selectedImage = {
                    data: e.target.result,
                    file: file,
                    name: file.name
                };
                
                document.getElementById('previewImage').src = e.target.result;
                document.getElementById('imagePreview').style.display = 'block';
                
                // Scroll to show preview
                scrollToBottom();
            };
            reader.readAsDataURL(file);
            
            // Reset input
            event.target.value = '';
        }

        function cancelImageUpload() {
            selectedImage = null;
            document.getElementById('imagePreview').style.display = 'none';
        }

        function sendImage() {
            if (!selectedImage || !socket) return;
            
            socket.emit('upload_image', {
                device_id: deviceId,
                image: selectedImage.data,
                filename: selectedImage.name
            });
            
            // Hide preview
            cancelImageUpload();
            
            // Show typing indicator for bot
            showTypingIndicator();
        }

        // Image modal
        function openImageModal(src) {
            document.getElementById('modalImage').src = src;
            document.getElementById('imageModal').style.display = 'flex';
        }

        function closeImageModal(event) {
            if (event) {
                event.stopPropagation();
            }
            document.getElementById('imageModal').style.display = 'none';
        }

        // Auto-resize textarea
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }

        // Handle key events
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        // Scroll to bottom
        function scrollToBottom() {
            const container = document.getElementById('messagesContainer');
            container.scrollTop = container.scrollHeight;
        }

        // Show notification
        function showNotification(message, type = 'info') {
            // Implementation for showing notifications
            console.log(`${type}: ${message}`);
        }

        // Initialize UI
        function initUI() {
            // Update expiry indicator every hour
            setInterval(updateExpiryIndicator, 3600000);
            
            // Check scroll position
            document.getElementById('messagesContainer').addEventListener('scroll', checkScrollPosition);
        }

        // Check scroll position for scroll-to-bottom button
        function checkScrollPosition() {
            const container = document.getElementById('messagesContainer');
            const scrollBottomBtn = document.getElementById('scrollBottom');
            const scrollHeight = container.scrollHeight;
            const scrollTop = container.scrollTop;
            const clientHeight = container.clientHeight;
            
            // Show scroll-to-bottom button if not at bottom
            if (scrollHeight - scrollTop - clientHeight > 100) {
                scrollBottomBtn.classList.add('visible');
            } else {
                scrollBottomBtn.classList.remove('visible');
            }
        }

        // Setup event listeners
        function setupEventListeners() {
            // Prevent context menu on images
            document.addEventListener('contextmenu', function(e) {
                if (e.target.classList.contains('message-image')) {
                    e.preventDefault();
                }
            });
            
            // Close modal with escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    closeImageModal();
                }
            });
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', initChat);
        // Emoji picker functionality
let emojiPicker = null;

// Initialize emoji picker
function initEmojiPicker() {
    if (typeof EmojiPicker === 'undefined') {
        console.warn('Emoji picker library not loaded');
        return;
    }
    
    emojiPicker = new EmojiPicker({
        theme: 'auto',
        skinToneEmoji: '🖐️',
        autoHide: true,
        emojiSize: '24px',
        emojisPerRow: 8,
        rows: 6,
        initialCategory: 'people',
        i18n: {
            search: 'Search emojis...',
            categories: {
                recents: 'Recent',
                people: 'People',
                nature: 'Nature',
                food: 'Food',
                activity: 'Activity',
                travel: 'Travel',
                objects: 'Objects',
                symbols: 'Symbols',
                flags: 'Flags'
            }
        }
    });
    
    emojiPicker.addEventListener('emoji-click', event => {
        const input = document.getElementById('messageInput');
        const emoji = event.detail.unicode;
        const cursorPos = input.selectionStart;
        const textBefore = input.value.substring(0, cursorPos);
        const textAfter = input.value.substring(cursorPos);
        
        input.value = textBefore + emoji + textAfter;
        input.focus();
        input.setSelectionRange(cursorPos + emoji.length, cursorPos + emoji.length);
        autoResize(input);
        
        hideEmojiPicker();
    });
}

// Open emoji picker
function openEmojiPicker() {
    const input = document.getElementById('messageInput');
    
    // If emoji picker library not loaded, show fallback
    if (typeof EmojiPicker === 'undefined') {
        showNativeEmojiPicker();
        return;
    }
    
    // Initialize picker if not already done
    if (!emojiPicker) {
        initEmojiPicker();
    }
    
    // Create or show emoji picker container
    let pickerContainer = document.getElementById('emojiPickerContainer');
    if (!pickerContainer) {
        pickerContainer = document.createElement('div');
        pickerContainer.id = 'emojiPickerContainer';
        pickerContainer.style.cssText = `
            position: absolute;
            bottom: 80px;
            right: 20px;
            width: 350px;
            max-width: 90vw;
            height: 400px;
            max-height: 60vh;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            z-index: 1000;
            overflow: hidden;
            border: 1px solid #e5e7eb;
            display: none;
        `;
        document.body.appendChild(pickerContainer);
    }
    
    // Add emoji picker to container
    pickerContainer.innerHTML = '';
    pickerContainer.appendChild(emojiPicker);
    
    // Position and show
    const inputRect = input.getBoundingClientRect();
    pickerContainer.style.bottom = `${window.innerHeight - inputRect.top + 60}px`;
    pickerContainer.style.right = '20px';
    pickerContainer.style.display = 'block';
    
    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: #f3f4f6;
        border: none;
        color: #6b7280;
        font-size: 20px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1001;
    `;
    closeBtn.onclick = hideEmojiPicker;
    pickerContainer.appendChild(closeBtn);
    
    // Click outside to close
    setTimeout(() => {
        document.addEventListener('click', closeOnClickOutside);
    }, 0);
}

// Hide emoji picker
function hideEmojiPicker() {
    const pickerContainer = document.getElementById('emojiPickerContainer');
    if (pickerContainer) {
        pickerContainer.style.display = 'none';
    }
    document.removeEventListener('click', closeOnClickOutside);
}

// Close when clicking outside
function closeOnClickOutside(event) {
    const pickerContainer = document.getElementById('emojiPickerContainer');
    if (pickerContainer && !pickerContainer.contains(event.target) && 
        !event.target.closest('.action-btn')) {
        hideEmojiPicker();
    }
}

// Fallback for mobile devices
function showNativeEmojiPicker() {
    const input = document.getElementById('messageInput');
    input.focus();
    
    // Try to trigger mobile keyboard emoji view
    if ('virtualKeyboard' in navigator) {
        navigator.virtualKeyboard.show();
    }
    
    // Show instruction for desktop
    if (!/Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
        showNotification('Use Windows key + . or Ctrl + Cmd + Space for emojis', 'info', 3000);
    }
}

// CSS for emoji picker
function addEmojiPickerStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Emoji picker styles */
        emoji-picker {
            --background: white;
            --border-color: #e5e7eb;
            --border-radius: 12px;
            --category-emoji-size: 24px;
            --category-emoji-padding: 4px;
            --category-font-size: 12px;
            --category-font-color: #6b7280;
            --category-font-weight: 500;
            --emoji-size: 24px;
            --emoji-padding: 8px;
            --indicator-color: #6366f1;
            --input-border-color: #e5e7eb;
            --input-border-radius: 8px;
            --input-font-color: #374151;
            --input-font-size: 14px;
            --input-padding: 12px;
            --num-columns: 8;
            --outline-color: #6366f1;
            width: 100%;
            height: 100%;
        }
        
        /* Mobile responsive */
        @media (max-width: 480px) {
            #emojiPickerContainer {
                width: 95vw !important;
                right: 2.5vw !important;
                height: 350px !important;
            }
            
            emoji-picker {
                --num-columns: 6;
                --emoji-size: 28px;
            }
        }
    `;
    document.head.appendChild(style);
}
    </script>
</body>
</html>

Server.py
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
                'is_admin': bool(row['is_admin'])
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
            'is_admin': False
        }
        
        emit('receive_message', user_msg, room=device_id)
        
        # Auto-reply from Flexia Merchant
        socketio.sleep(1)
        
        auto_reply_id = save_message(
            device_id, 
            'Flexia Merchant', 
            'Thank you for your message! I\'ll get back to you soon.', 
            'text', 
            True
        )
        
        auto_reply = {
            'id': auto_reply_id,
            'sender': 'Flexia Merchant',
            'message': 'Thank you for your message! I\'ll get back to you soon.',
            'type': 'text',
            'timestamp': datetime.now().isoformat(),
            'is_admin': True
        }
        
        emit('receive_message', auto_reply, room=device_id)
        
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
        
        # Check if user is expired
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
        
        # Save message with image
        message_id = save_message(
            device_id,
            user['username'],
            f'/uploads/{unique_filename}',
            'image',
            False
        )
        
        # Send to user
        image_msg = {
            'id': message_id,
            'sender': user['username'],
            'message': f'/uploads/{unique_filename}',
            'type': 'image',
            'timestamp': datetime.now().isoformat(),
            'is_admin': False
        }
        
        emit('receive_message', image_msg, room=device_id)
        
        logger.info(f"🖼️ Image uploaded by {user['username']}: {filename}")
    
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
        
        if not is_admin or not device_id or not message:
            return
        
        # Verify admin (simple check - in production use proper auth)
        if data.get('admin_password') != admin_password:
            return
        
        # Save admin message
        message_id = save_message(device_id, 'Flexia Merchant', message, message_type, True)
        
        # Send to user
        admin_msg = {
            'id': message_id,
            'sender': 'Flexia Merchant',
            'message': message,
            'type': message_type,
            'timestamp': datetime.now().isoformat(),
            'is_admin': True
        }
        
        emit('receive_message', admin_msg, room=device_id)
        
        logger.info(f"👑 Admin message sent to {device_id[:8]}...: {message[:50]}...")
    
    except Exception as e:
        logger.error(f"❌ Admin message error: {str(e)}")

@socketio.on('get_all_users')
def handle_get_users(data):
    try:
        is_admin = data.get('is_admin', False)
        admin_password = data.get('admin_password')
        
        if not is_admin or admin_password != admin_password:
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
        admin_password = data.get('admin_password')
        
        if not is_admin or admin_password != admin_password or not device_id:
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
        admin_password = data.get('admin_password')
        
        if not is_admin or admin_password != admin_password or not device_id:
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
             Why IS It That Users Don't Recieve admin response in real time and the auto response is not necessary