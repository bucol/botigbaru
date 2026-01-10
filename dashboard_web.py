"""
Web Dashboard for Instagram Bot
Simple Flask dashboard untuk monitor dan control bot
"""

from flask import Flask, render_template_string, jsonify, request, redirect, url_for
from functools import wraps
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Simple auth
DASHBOARD_USER = os.getenv('DASHBOARD_USER', 'admin')
DASHBOARD_PASS = os.getenv('DASHBOARD_PASS', 'admin123')

# Bot controller reference (will be set from main.py)
bot_controller = None

def set_bot_controller(controller):
    global bot_controller
    bot_controller = controller


# HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Bot Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); }
    </style>
</head>
<body class="gradient-bg min-h-screen text-white">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold">📱 Instagram Bot</h1>
                <p class="text-white/70">Dashboard Control Panel</p>
            </div>
            <div class="flex gap-2">
                <button onclick="refreshData()" class="px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30">
                    🔄 Refresh
                </button>
                <a href="/logout" class="px-4 py-2 bg-red-500/50 rounded-lg hover:bg-red-500/70">
                    🚪 Logout
                </a>
            </div>
        </div>
        
        <!-- Status Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="card rounded-xl p-4">
                <div class="flex justify-between items-center">
                    <div>
                        <p class="text-white/70 text-sm">Status</p>
                        <p id="status" class="text-2xl font-bold">Loading...</p>
                    </div>
                    <div id="status-icon" class="text-4xl">⏳</div>
                </div>
            </div>
            <div class="card rounded-xl p-4">
                <div class="flex justify-between items-center">
                    <div>
                        <p class="text-white/70 text-sm">Account</p>
                        <p id="account" class="text-2xl font-bold">-</p>
                    </div>
                    <div class="text-4xl">👤</div>
                </div>
            </div>
            <div class="card rounded-xl p-4">
                <div class="flex justify-between items-center">
                    <div>
                        <p class="text-white/70 text-sm">Uptime</p>
                        <p id="uptime" class="text-2xl font-bold">-</p>
                    </div>
                    <div class="text-4xl">⏱️</div>
                </div>
            </div>
            <div class="card rounded-xl p-4">
                <div class="flex justify-between items-center">
                    <div>
                        <p class="text-white/70 text-sm">Today Actions</p>
                        <p id="total-actions" class="text-2xl font-bold">0</p>
                    </div>
                    <div class="text-4xl">📊</div>
                </div>
            </div>
        </div>
        
        <!-- Actions Grid -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <div class="card rounded-xl p-4 text-center">
                <div class="text-3xl mb-2">❤️</div>
                <p class="text-white/70 text-sm">Likes</p>
                <p id="likes" class="text-xl font-bold">0</p>
            </div>
            <div class="card rounded-xl p-4 text-center">
                <div class="text-3xl mb-2">👥</div>
                <p class="text-white/70 text-sm">Follows</p>
                <p id="follows" class="text-xl font-bold">0</p>
            </div>
            <div class="card rounded-xl p-4 text-center">
                <div class="text-3xl mb-2">💬</div>
                <p class="text-white/70 text-sm">Comments</p>
                <p id="comments" class="text-xl font-bold">0</p>
            </div>
            <div class="card rounded-xl p-4 text-center">
                <div class="text-3xl mb-2">📖</div>
                <p class="text-white/70 text-sm">Stories</p>
                <p id="stories" class="text-xl font-bold">0</p>
            </div>
            <div class="card rounded-xl p-4 text-center">
                <div class="text-3xl mb-2">✉️</div>
                <p class="text-white/70 text-sm">DMs</p>
                <p id="dms" class="text-xl font-bold">0</p>
            </div>
        </div>
        
        <!-- Control Panel -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <!-- Quick Actions -->
            <div class="card rounded-xl p-6">
                <h2 class="text-xl font-bold mb-4">⚡ Quick Actions</h2>
                <div class="grid grid-cols-2 gap-3">
                    <button onclick="toggleBot()" id="toggle-btn" 
                        class="px-4 py-3 bg-green-500/50 rounded-lg hover:bg-green-500/70 font-semibold">
                        ▶️ Start
                    </button>
                    <button onclick="rotateAccount()" 
                        class="px-4 py-3 bg-blue-500/50 rounded-lg hover:bg-blue-500/70 font-semibold">
                        🔄 Rotate Account
                    </button>
                    <button onclick="runAction('like')" 
                        class="px-4 py-3 bg-pink-500/50 rounded-lg hover:bg-pink-500/70 font-semibold">
                        ❤️ Auto Like
                    </button>
                    <button onclick="runAction('follow')" 
                        class="px-4 py-3 bg-purple-500/50 rounded-lg hover:bg-purple-500/70 font-semibold">
                        👥 Auto Follow
                    </button>
                    <button onclick="runAction('story')" 
                        class="px-4 py-3 bg-orange-500/50 rounded-lg hover:bg-orange-500/70 font-semibold">
                        📖 View Stories
                    </button>
                    <button onclick="runAction('dm')" 
                        class="px-4 py-3 bg-cyan-500/50 rounded-lg hover:bg-cyan-500/70 font-semibold">
                        ✉️ Send DMs
                    </button>
                </div>
            </div>
            
            <!-- Schedule Action -->
            <div class="card rounded-xl p-6">
                <h2 class="text-xl font-bold mb-4">📅 Schedule Action</h2>
                <form onsubmit="scheduleAction(event)">
                    <div class="mb-3">
                        <label class="block text-white/70 text-sm mb-1">Action Type</label>
                        <select id="action-type" class="w-full px-3 py-2 bg-white/20 rounded-lg text-white">
                            <option value="like">Like by Hashtag</option>
                            <option value="follow">Follow Users</option>
                            <option value="comment">Comment</option>
                            <option value="story">View Stories</option>
                            <option value="dm">Send DMs</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="block text-white/70 text-sm mb-1">Target (hashtag/username)</label>
                        <input type="text" id="action-target" placeholder="photography" 
                            class="w-full px-3 py-2 bg-white/20 rounded-lg text-white placeholder-white/50">
                    </div>
                    <button type="submit" 
                        class="w-full px-4 py-3 bg-gradient-to-r from-pink-500 to-purple-500 rounded-lg font-semibold hover:opacity-90">
                        ➕ Add to Schedule
                    </button>
                </form>
            </div>
        </div>
        
        <!-- Activity Log -->
        <div class="card rounded-xl p-6 mt-8">
            <h2 class="text-xl font-bold mb-4">📋 Recent Activity</h2>
            <div id="activity-log" class="space-y-2 max-h-64 overflow-y-auto">
                <p class="text-white/50">No recent activity</p>
            </div>
        </div>
    </div>
    
    <script>
        // Fetch and update data
        async function refreshData() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                
                // Update status
                document.getElementById('status').textContent = data.paused ? 'Paused' : (data.running ? 'Running' : 'Stopped');
                document.getElementById('status-icon').textContent = data.paused ? '⏸️' : (data.running ? '🟢' : '🔴');
                document.getElementById('account').textContent = data.current_account || '-';
                document.getElementById('uptime').textContent = data.uptime || '-';
                
                // Update actions
                const actions = data.actions || {};
                document.getElementById('likes').textContent = actions.likes || 0;
                document.getElementById('follows').textContent = actions.follows || 0;
                document.getElementById('comments').textContent = actions.comments || 0;
                document.getElementById('stories').textContent = actions.stories || 0;
                document.getElementById('dms').textContent = actions.dms || 0;
                
                const total = Object.values(actions).reduce((a, b) => a + b, 0);
                document.getElementById('total-actions').textContent = total;
                
                // Update toggle button
                const toggleBtn = document.getElementById('toggle-btn');
                if (data.running && !data.paused) {
                    toggleBtn.textContent = '⏸️ Pause';
                    toggleBtn.className = 'px-4 py-3 bg-yellow-500/50 rounded-lg hover:bg-yellow-500/70 font-semibold';
                } else {
                    toggleBtn.textContent = '▶️ Start';
                    toggleBtn.className = 'px-4 py-3 bg-green-500/50 rounded-lg hover:bg-green-500/70 font-semibold';
                }
                
            } catch (e) {
                console.error('Error fetching status:', e);
            }
        }
        
        async function toggleBot() {
            await fetch('/api/toggle', { method: 'POST' });
            refreshData();
        }
        
        async function rotateAccount() {
            await fetch('/api/rotate', { method: 'POST' });
            refreshData();
        }
        
        async function runAction(action) {
            const target = prompt('Enter target (hashtag or username):');
            if (!target) return;
            
            await fetch('/api/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, target })
            });
            
            alert(`${action} action started for ${target}`);
            refreshData();
        }
        
        async function scheduleAction(e) {
            e.preventDefault();
            const action = document.getElementById('action-type').value;
            const target = document.getElementById('action-target').value;
            
            if (!target) {
                alert('Please enter a target');
                return;
            }
            
            await fetch('/api/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, target })
            });
            
            alert('Action scheduled!');
            document.getElementById('action-target').value = '';
        }
        
        // Initial load and auto refresh
        refreshData();
        setInterval(refreshData, 10000);
    </script>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Instagram Bot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    </style>
</head>
<body class="gradient-bg min-h-screen flex items-center justify-center">
    <div class="bg-white/10 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md">
        <div class="text-center mb-8">
            <div class="text-6xl mb-4">📱</div>
            <h1 class="text-2xl font-bold text-white">Instagram Bot</h1>
            <p class="text-white/70">Login to Dashboard</p>
        </div>
        
        {% if error %}
        <div class="bg-red-500/50 text-white px-4 py-2 rounded-lg mb-4">
            {{ error }}
        </div>
        {% endif %}
        
        <form method="POST">
            <div class="mb-4">
                <label class="block text-white/70 text-sm mb-2">Username</label>
                <input type="text" name="username" required
                    class="w-full px-4 py-3 bg-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="Enter username">
            </div>
            <div class="mb-6">
                <label class="block text-white/70 text-sm mb-2">Password</label>
                <input type="password" name="password" required
                    class="w-full px-4 py-3 bg-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="Enter password">
            </div>
            <button type="submit"
                class="w-full px-4 py-3 bg-gradient-to-r from-pink-500 to-purple-500 rounded-lg font-semibold text-white hover:opacity-90">
                Login
            </button>
        </form>
    </div>
</body>
</html>
"""

# Session storage (simple)
sessions = {}

def check_auth():
    """Check if user is authenticated"""
    session_id = request.cookies.get('session_id')
    return session_id and session_id in sessions

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == DASHBOARD_USER and password == DASHBOARD_PASS:
            import uuid
            session_id = str(uuid.uuid4())
            sessions[session_id] = username
            
            response = redirect(url_for('dashboard'))
            response.set_cookie('session_id', session_id, httponly=True)
            return response
        else:
            error = 'Invalid username or password'
            
    return render_template_string(LOGIN_HTML, error=error)


@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    if session_id in sessions:
        del sessions[session_id]
    response = redirect(url_for('login'))
    response.delete_cookie('session_id')
    return response


@app.route('/')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/status')
@login_required
def api_status():
    if bot_controller:
        return jsonify(bot_controller.get_status())
    return jsonify({
        'running': False,
        'paused': False,
        'current_account': None,
        'uptime': None,
        'actions': {'likes': 0, 'follows': 0, 'comments': 0, 'stories': 0, 'dms': 0}
    })


@app.route('/api/toggle', methods=['POST'])
@login_required
def api_toggle():
    if bot_controller:
        if bot_controller.paused:
            bot_controller.resume()
        else:
            bot_controller.pause()
        return jsonify({'success': True, 'paused': bot_controller.paused})
    return jsonify({'success': False, 'error': 'Bot not initialized'})


@app.route('/api/rotate', methods=['POST'])
@login_required
def api_rotate():
    if bot_controller:
        success = bot_controller.rotate_account()
        return jsonify({'success': success})
    return jsonify({'success': False})


@app.route('/api/action', methods=['POST'])
@login_required
def api_action():
    data = request.json
    action = data.get('action')
    target = data.get('target')
    
    if bot_controller and action and target:
        bot_controller.scheduler.add_task(action, target, priority=1)
        return jsonify({'success': True})
    return jsonify({'success': False})


@app.route('/api/schedule', methods=['POST'])
@login_required
def api_schedule():
    data = request.json
    action = data.get('action')
    target = data.get('target')
    
    if bot_controller and action and target:
        bot_controller.scheduler.add_task(action, target)
        return jsonify({'success': True})
    return jsonify({'success': False})


def run_dashboard(controller=None, host='0.0.0.0', port=5000):
    """Run the web dashboard"""
    global bot_controller
    bot_controller = controller
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    run_dashboard()
