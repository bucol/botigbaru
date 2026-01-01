from flask import Flask, request, render_template, redirect, url_for
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Integrasi core (asumsi di folder sama)
from dashboard import login_menu, feature_auto_like, feature_auto_dm, etc  # Import function dari dashboard kalau perlu, atau call os.system('python dashboard.py') kalau simple
# Untuk simple, gua bikin route call function dashboard, tapi adjust kalau perlu

@app.route('/')
def home():
    return render_template('index.html')  # Buat index.html simple

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    # Call login_menu atau lm.login_account
    lm = LoginManager()
    client, success = lm.login_account(username, password)
    if success:
        return "Login sukses!"
    return "Login gagal!"

# Tambah route lain seperti /auto_like, call feature_auto_like()

# Buat index.html di templates/
if not os.path.exists('templates'):
    os.makedirs('templates')
with open('templates/index.html', 'w') as f:
    f.write("""
    <html>
    <body>
    <form action="/login" method="post">
    Username: <input name="username"><br>
    Password: <input name="password" type="password"><br>
    <input type="submit" value="Login">
    </form>
    </body>
    </html>
    """)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)