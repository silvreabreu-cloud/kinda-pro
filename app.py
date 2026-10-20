import os
from flask import Flask, request, session, redirect, url_for, render_template_string
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = 'kinda-2026-seguro'  # troca depois
socketio = SocketIO(app, cors_allowed_origins="*")

# --- SENHA GERADA PELO TEU EMAIL ---
# Senha = silvreabreu-cloud + 2026
ADMIN_USER = "silvreabreu-cloud"
ADMIN_PASS = os.environ.get("ADMIN_PASS", "silvestreabreu@2026!")

# --- CONFIGS DA LOJA ---
WHATSAPP = "923729647"

produtos = [
    {"id": 1, "nome": "T-shirt Kinda", "preco": 5000, "stock": 10},
    {"id": 2, "nome": "Boné Kinda", "preco": 3500, "stock": 15},
]

LOGIN_HTML = """
<form method="POST" style="padding:50px;font-family:sans-serif">
<h2>Admin Kinda</h2>
<input name="user" placeholder="Usuário"><br><br>
<input name="pass" type="password" placeholder="Senha"><br><br>
<button>Entrar</button>
</form>
"""

@app.route('/admin/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form['user'] == ADMIN_USER and request.form['pass'] == ADMIN_PASS:
            session['admin'] = True
            return redirect('/admin/produtos')
        return "Senha errada! <a href='/admin/login'>tentar novamente</a>"
    return LOGIN_HTML

@app.route('/admin/produtos')
def admin_prod():
    if not session.get('admin'):
        return redirect('/admin/login')
    return f"<h1>Admin - {len(produtos)} produtos</h1><a href='/'>Ver loja</a> | <a href='/admin/logout'>Sair</a><br><br>{produtos}"

@app.route('/admin/logout')
def logout():
    session.pop('admin', None)
    return redirect('/admin/login')

@app.route('/')
def loja():
    return f"<h1>Kinda Loja - WhatsApp {WHATSAPP}</h1>{produtos}"

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
