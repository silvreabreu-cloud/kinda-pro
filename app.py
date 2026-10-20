import os, json, base64
from flask import Flask, request, session, redirect, jsonify, render_template_string
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = 'kinda-pro-2026'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
socketio = SocketIO(app, cors_allowed_origins="*")

ADMIN_PASS = os.environ.get("ADMIN_PASS", "923729647")

def load_config():
    try:
        with open('config.json','r') as f: return json.load(f)
    except:
        return {"whatsapp":"923729647","produtos":[
            {"id":1,"nome":"T-shirt Kinda Pro","preco":15000,"stock":20,"cat":"Roupas","foto":""},
            {"id":2,"nome":"Boné Kinda","preco":7500,"stock":15,"cat":"Acessórios","foto":""}
        ]}
def save_config(c):
    with open('config.json','w') as f: json.dump(c,f,indent=2)

config = load_config()

LOGIN_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:sans-serif;background:#0a0a0a;color:white;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.card{background:#111;border:1px solid #222;padding:40px;border-radius:20px;width:350px;text-align:center}
input{width:100%;padding:14px;background:#1a1a1a;border:1px solid #333;border-radius:10px;color:white;margin:10px 0}button{width:100%;padding:14px;background:white;color:black;border:0;border-radius:10px;font-weight:700}</style></head>
<body><div class="card"><h1>KINDA PRO</h1><form method="POST"><input name="pass" type="password" placeholder="Senha" required><button>ENTRAR</button></form></div></body></html>
"""

ADMIN_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{font-family:Inter,sans-serif;background:#0a0a0a;color:white;margin:0}
.header{background:#111;border-bottom:1px solid #222;padding:15px 20px;display:flex;justify-content:space-between;position:sticky;top:0}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;padding:20px}.stat{background:#111;border:1px solid #222;padding:20px;border-radius:15px}.stat h3{margin:0;color:#888;font-size:12px}.stat p{margin:5px 0 0;font-size:22px;font-weight:700}
.container{padding:20px;max-width:1200px;margin:0 auto}.card{background:#111;border:1px solid #222;border-radius:15px;padding:20px;margin-bottom:20px}
table{width:100%;border-collapse:collapse}th{color:#888;text-align:left;padding:10px;font-size:11px}td{padding:8px;border-top:1px solid #222}
input,select{background:#1a1a1a;border:1px solid #333;color:white;padding:8px;border-radius:8px;width:100%}
.btn{padding:8px 12px;border-radius:8px;border:0;cursor:pointer;font-weight:600;font-size:12px}
.btn-white{background:white;color:black}.btn-red{background:#ff2222;color:white}.btn-dark{background:#222;color:white;border:1px solid #333}
.prod-img{width:50px;height:50px;object-fit:cover;border-radius:8px;background:#222}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:15px}@media(max-width:700px){.grid2,.stats{grid-template-columns:1fr}}
</style></head><body>
<div class="header"><b>KINDA PRO • ADMIN</b><div><a href="/" style="color:#888;text-decoration:none;margin-right:15px">Loja</a><a href="/admin/logout" style="color:#ff4444;text-decoration:none">Sair</a></div></div>
<div class="container">
<div class="stats"><div class="stat"><h3>PRODUTOS</h3><p>{{ total_prod }}</p></div><div class="stat"><h3>VALOR STOCK</h3><p>{{ total_valor }} Kz</p></div><div class="stat"><h3>WHATSAPP</h3><p>{{ whatsapp }}</p></div></div>

<div class="grid2">
<div class="card">
<h3>➕ Adicionar Produto com Foto</h3>
<form id="addForm" enctype="multipart/form-data">
<input name="nome" placeholder="Nome" required style="margin-bottom:8px">
<div class="grid2"><input name="preco" type="number" placeholder="Preço Kz" required><input name="stock" type="number" placeholder="Stock" required></div>
<input name="cat" placeholder="Categoria" style="margin-top:8px">
<input name="foto_url" placeholder="Link da foto (opcional) - ex: https://i.imgur.com/..." style="margin-top:8px">
<label style="font-size:11px;color:#888;margin-top:8px;display:block">OU envia foto do celular:</label>
<input type="file" name="foto_file" accept="image/*" style="margin-top:5px">
<button class="btn btn-white" style="margin-top:10px;width:100%">Adicionar com Foto</button>
</form>
</div>
<div class="card">
<h3>⚙️ Config</h3>
<form id="configForm"><input name="whatsapp" value="{{ whatsapp }}"><input name="nova_senha" type="password" placeholder="Nova senha (opcional)" style="margin-top:8px"><button class="btn btn-dark" style="width:100%;margin-top:10px">Salvar</button></form>
</div>
</div>

<div class="card">
<h3>📦 Produtos - Editar com Foto</h3>
<table><tr><th>FOTO</th><th>NOME</th><th>PREÇO</th><th>STOCK</th><th>FOTO URL</th><th>AÇÃO</th></tr>
{% for p in produtos %}
<tr>
<td>{% if p.foto %}<img src="{{ p.foto }}" class="prod-img">{% else %}<div class="prod-img"></div>{% endif %}</td>
<td><input value="{{ p.nome }}" id="nome_{{ p.id }}"></td>
<td><input type="number" value="{{ p.preco }}" id="preco_{{ p.id }}" style="width:80px"></td>
<td><input type="number" value="{{ p.stock }}" id="stock_{{ p.id }}" style="width:60px"></td>
<td><input value="{{ p.foto }}" id="foto_{{ p.id }}" placeholder="link foto" style="width:120px"></td>
<td><button class="btn btn-white" onclick="salvar({{ p.id }})">💾</button><button class="btn btn-red" onclick="apagar({{ p.id }})">🗑️</button></td>
</tr>
{% endfor %}
</table>
</div>
</div>
<script>
async function salvar(id){
 const data={id:id,nome:document.getElementById('nome_'+id).value,preco:parseInt(document.getElementById('preco_'+id).value),stock:parseInt(document.getElementById('stock_'+id).value),foto:document.getElementById('foto_'+id).value};
 await fetch('/admin/api/produto',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
 alert('Salvo!'); location.reload();
}
async function apagar(id){if(!confirm('Apagar?'))return;await fetch('/admin/api/produto/delete/'+id,{method:'POST'});location.reload();}
document.getElementById('addForm').onsubmit=async(e)=>{
 e.preventDefault();
 const fd=new FormData(e.target);
 const res=await fetch('/admin/api/produto/add',{method:'POST',body:fd});
 const j=await res.json();
 if(j.ok) location.reload(); else alert('Erro: '+j.error);
}
document.getElementById('configForm').onsubmit=async(e)=>{
 e.preventDefault();const fd=new FormData(e.target);
 await fetch('/admin/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({whatsapp:fd.get('whatsapp'),nova_senha:fd.get('nova_senha')})});
 alert('Salvo!');location.reload();
}
</script></body></html>
"""

LOJA_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:sans-serif;background:#0a0a0a;color:white;padding:15px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}.card{background:#111;border:1px solid #222;border-radius:15px;overflow:hidden}.card img{width:100%;height:160px;object-fit:cover;background:#222}.info{padding:12px}.btn{padding:10px;background:white;color:black;border-radius:8px;text-decoration:none;display:block;text-align:center;margin-top:8px;font-weight:700;font-size:13px}</style>
</head><body><h2>KINDA PRO • Loja</h2><p>Pedidos: {{ whatsapp }}</p>
<div class="grid">{% for p in produtos %}<div class="card">{% if p.foto %}<img src="{{ p.foto }}">{% else %}<div style="height:160px;background:#222"></div>{% endif %}<div class="info"><b style="font-size:14px">{{ p.nome }}</b><br><span style="color:#888;font-size:12px">{{ p.cat }}</span><br><b>{{ p.preco }} Kz</b><br><span style="font-size:11px;color:#666">Stock {{ p.stock }}</span><a class="btn" href="https://wa.me/244{{ whatsapp }}?text=Quero {{ p.nome }} - {{ p.preco }}Kz">WhatsApp</a></div></div>{% endfor %}</div>
<br><a href="/admin/login" style="color:#333">Admin</a></body></html>
"""

@app.route('/admin/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form.get('pass')==config.get('admin_pass',ADMIN_PASS) or request.form.get('pass')==ADMIN_PASS:
            session['admin']=True; return redirect('/admin/produtos')
        return render_template_string(LOGIN_PAGE)
    return render_template_string(LOGIN_PAGE)

@app.route('/admin/produtos')
def admin():
    if not session.get('admin'): return redirect('/admin/login')
    total=len(config['produtos']); total_valor=sum(p['preco']*p['stock'] for p in config['produtos'])
    return render_template_string(ADMIN_PAGE, produtos=config['produtos'], total_prod=total, total_valor=total_valor, whatsapp=config['whatsapp'])

@app.route('/admin/api/produto', methods=['POST'])
def api_edit():
    if not session.get('admin'): return jsonify({"error":"no auth"}),401
    data=request.json
    for p in config['produtos']:
        if p['id']==data['id']: p.update(data)
    save_config(config); return jsonify({"ok":True})

@app.route('/admin/api/produto/add', methods=['POST'])
def api_add():
    if not session.get('admin'): return jsonify({"error":"no auth"}),401
    nome=request.form.get('nome'); preco=int(request.form.get('preco',0)); stock=int(request.form.get('stock',0)); cat=request.form.get('cat',''); foto_url=request.form.get('foto_url','')
    foto=foto_url
    if 'foto_file' in request.files:
        f=request.files['foto_file']
        if f.filename!='':
            filename=secure_filename(f.filename)
            path=os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(path)
            foto=f"/static/uploads/{filename}"
    data={"id":max([p['id'] for p in config['produtos']],default=0)+1,"nome":nome,"preco":preco,"stock":stock,"cat":cat,"foto":foto}
    config['produtos'].append(data); save_config(config); return jsonify({"ok":True})

@app.route('/admin/api/produto/delete/<int:id>', methods=['POST'])
def api_del(id):
    if not session.get('admin'): return jsonify({"error":"no auth"}),401
    config['produtos']=[p for p in config['produtos'] if p['id']!=id]; save_config(config); return jsonify({"ok":True})

@app.route('/admin/api/config', methods=['POST'])
def api_conf():
    if not session.get('admin'): return jsonify({"error":"no auth"}),401
    data=request.json
    if data.get('whatsapp'): config['whatsapp']=data['whatsapp']
    if data.get('nova_senha'): config['admin_pass']=data['nova_senha']
    save_config(config); return jsonify({"ok":True})

@app.route('/admin/logout')
def logout(): session.pop('admin',None); return redirect('/admin/login')

@app.route('/')
def loja(): return render_template_string(LOJA_PAGE, produtos=config['produtos'], whatsapp=config['whatsapp'])

if __name__=='__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
