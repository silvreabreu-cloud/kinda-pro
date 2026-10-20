import os
from flask import Flask, request, session, redirect
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = 'kinda-super-secreto-2026'

socketio = SocketIO(app, cors_allowed_origins="*")

# SENHA - pode ser mudada no Render em Environment
ADMIN_PASS = os.environ.get("ADMIN_PASS", "923729647")

WHATSAPP = "923729647"

produtos = [
    {"id": 1, "nome": "T-shirt Kinda", "preco": 5000, "stock": 10},
    {"id": 2, "nome": "Boné Kinda", "preco": 3500, "stock": 15},
]

LOGIN_HTML = """
<div style="max-width:400px;margin:100px auto;padding:30px;border:1px solid #ccc;border-radius:10px;font-family:sans-serif;text-align:center">
<h2>🔐 Admin Kinda Pro</h2>
<form method="POST">
<input name="pass" type="password" placeholder="Digite a senha" style="width:100%;padding:12px;margin:10px 0" required><br>
<button style="width:100%;padding:12px;background:black;color:white;border:0;border-radius:5px">ENTRAR</button>
</form>
<p style="font-size:12px;color:#666">Senha padrão: 923729647</p>
</div>
"""

@app.route('/admin/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pass') == ADMIN_PASS:
            session['admin'] = True
            return redirect('/admin/produtos')
        return LOGIN_HTML + "<p style='color:red'>❌ Senha errada!</p>"
    return LOGIN_HTML

@app.route('/admin/produtos')
def admin_prod():
    if not session.get('admin'):
        return redirect('/admin/login')
    html = f"""
    <div style="font-family:sans-serif;padding:20px">
    <h1>Admin Kinda - {len(produtos)} produtos</h1>
    <a href='/'>Ver loja</a> | <a href='/admin/logout'>Sair</a> | WhatsApp: {WHATSAPP}
    <hr>
    <pre>{produtos}</pre>
    <hr>
    <p>Senha atual: {ADMIN_PASS}</p>
    </div>
    """
    return html

@app.route('/admin/logout')
def logout():
    session.pop('admin', None)
    return redirect('/admin/login')

@app.route('/')
def loja():
    return f"<h1>Kinda Loja - WhatsApp {WHATSAPP}</h1><p>Admin: /admin/login</p><p>{produtos}</p>"

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
