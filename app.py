from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO
import sqlite3, random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kinda-pro-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

WPP_NUM = "244923729647"
FRETE_PADRAO = 3000

def get_db():
    conn = sqlite3.connect('kinda.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS produtos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nome TEXT, kg INTEGER, saco INTEGER,
                  origem TEXT, icon TEXT, cor TEXT, ativo INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  cliente TEXT, telefone TEXT, bairro TEXT,
                  produtos TEXT, total INTEGER, frete INTEGER,
                  status TEXT, lat REAL, lng REAL, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config
                 (chave TEXT PRIMARY KEY, valor TEXT)''')
    c.execute("SELECT COUNT(*) FROM produtos")
    if c.fetchone()[0]==0:
        prods=[("Milho Amarelo",800,35000,"Huambo","🌽","#FFF9C4"),("Feijão Manteiga",1500,65000,"Bié","🫘","#EFEBE9"),("Arroz Nacional",1200,50000,"Cuanza Sul","🍚","#FFF8E1"),("Mandioca Fresca",500,18000,"Uíge","🥔","#FFF3E0"),("Tomate",700,14000,"Benguela","🍅","#FFEBEE"),("Cebola",900,18000,"Cunene","🧅","#F3E5F5")]
        c.executemany("INSERT INTO produtos (nome,kg,saco,origem,icon,cor) VALUES (?,?,?,?,?,?)", prods)
        c.execute("INSERT OR IGNORE INTO config (chave,valor) VALUES ('wpp',?)", (WPP_NUM,))
    conn.commit()
    conn.close()

init_db()

BASE = """
<style>
*{font-family:system-ui;box-sizing:border-box;margin:0}
body{background:#F6F7F3}
.header{background:#fff;padding:12px 18px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 1px 10px #0001;position:sticky;top:0;z-index:20}
.nav a{margin:0 4px;text-decoration:none;font-weight:700;font-size:12px;color:#1B5E20;padding:6px 10px;border-radius:20px;background:#E8F5E9}
.card{background:#fff;border-radius:16px;padding:14px;box-shadow:0 2px 8px #00000006}
.btn{background:#1B5E20;color:#fff;border:none;padding:10px 14px;border-radius:20px;font-weight:700;cursor:pointer}
.btn-red{background:#C62828}.btn-whats{background:#25D366;width:100%;padding:14px;border-radius:12px;font-weight:900}
input,select{width:100%;padding:12px;border-radius:10px;border:1px solid #ddd;margin:5px 0}
table{width:100%;background:#fff;border-radius:12px;border-collapse:collapse;overflow:hidden}
th{background:#1B5E20;color:#fff;padding:10px;text-align:left;font-size:12px} td{padding:8px;border-bottom:1px solid #eee;font-size:12px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px}
</style>
"""

@app.route("/")
def loja():
    conn = get_db()
    produtos = conn.execute("SELECT * FROM produtos WHERE ativo=1").fetchall()
    conf = conn.execute("SELECT valor FROM config WHERE chave='wpp'").fetchone()
    wpp = conf['valor'] if conf else WPP_NUM
    conn.close()
    return render_template_string(BASE + """
<div class="header"><div><b style="color:#1B5E20">KINDA</b> <small>Express</small></div><div class="nav"><a href="/admin">ADMIN</a><a href="/mapa">MAPA</a></div></div>
<div style="padding:10px"><div style="display:flex;background:#E8F5E9;padding:4px;border-radius:30px;width:fit-content;margin:0 auto">
<button id="bRet" class="btn" style="background:#2E7D32" onclick="setModo('retalho')">RETAILHO</button>
<button id="bGro" class="btn" style="background:transparent;color:#666" onclick="setModo('grosso')">GROSSO</button></div></div>
<div class="grid" id="grid"></div>
<div style="background:#fff;border-radius:20px 20px 0 0;padding:18px;position:sticky;bottom:0;box-shadow:0 -5px 20px #0002">
<div style="display:flex;justify-content:space-between"><b>Seu pedido</b><small id="freteInfo">Frete 3.000 Kz</small></div>
<div id="lista" style="margin:10px 0;color:#555;font-size:13px">Carrinho vazio</div>
<div style="display:flex;justify-content:space-between"><span>Total</span><b id="total" style="font-size:20px;color:#1B5E20">0 Kz</b></div>
<input id="nome" placeholder="Nome completo"><input id="tel" placeholder="Telefone 9xx"><input id="bairro" placeholder="Bairro">
<button class="btn-whats" onclick="finalizar()">FINALIZAR NO WHATSAPP {{wpp}} →</button></div>
<script>
let modo='retalho',carrinho=[];let produtos={{produtos|tojson}};let wpp="{{wpp}}";
function render(){let h="";produtos.forEach((p,i)=>{let pr=modo=='retalho'?p.kg:p.saco;h+=`<div class=card><div style="font-size:30px;background:${p.cor};width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 6px">${p.icon}</div><b>${p.nome}</b><br><small>${p.origem}</small><div style="color:#2E7D32;font-weight:900;margin:6px 0">${pr.toLocaleString()} Kz</div><button class=btn onclick="add(${i})">Adicionar</button></div>`;});document.getElementById("grid").innerHTML=h;}
function setModo(m){modo=m;document.getElementById("bRet").style.background=m=='retalho'?'#2E7D32':'transparent';document.getElementById("bRet").style.color=m=='retalho'?'#fff':'#666';document.getElementById("bGro").style.background=m=='grosso'?'#2E7D32':'transparent';document.getElementById("bGro").style.color=m=='grosso'?'#fff':'#666';render();}
function add(i){let p=produtos[i];let pr=modo=='retalho'?p.kg:p.saco;carrinho.push({nome:p.nome,preco:pr,icon:p.icon});atualizar();}
function atualizar(){let s=carrinho.reduce((a,b)=>a+b.preco,0);let frete=s>=50000||s==0?0:3000;document.getElementById("total").innerText=(s+frete).toLocaleString()+" Kz";document.getElementById("freteInfo").innerText=frete==0?"Frete Grátis!":"Frete 3.000 Kz";document.getElementById("lista").innerHTML=carrinho.length==0?"Carrinho vazio":carrinho.map(c=>`${c.icon} ${c.nome} - ${c.preco} Kz`).join("<br>");}
async function finalizar(){if(carrinho.length==0){alert("Carrinho vazio");return;}let s=carrinho.reduce((a,b)=>a+b.preco,0);let frete=s>=50000?0:3000;navigator.geolocation.getCurrentPosition(async pos=>{let data={cliente:nome.value,telefone:tel.value,bairro:bairro.value,produtos:JSON.stringify(carrinho),total:s,frete:frete,lat:pos.coords.latitude,lng:pos.coords.longitude};let r=await fetch("/api/pedido",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});let j=await r.json();let txt=`*PEDIDO KINDA #${j.id}*%0A`+carrinho.map(c=>`• ${c.icon} ${c.nome} - ${c.preco} Kz`).join("%0A")+`%0A*Total:* ${s+frete} Kz%0A*Cliente:* ${nome.value}%0A*Tel:* ${tel.value}`;window.open(`https://wa.me/${wpp}?text=${txt}`,"_blank");window.location="/mapa?id="+j.id;},async()=>{let data={cliente:nome.value,telefone:tel.value,bairro:bairro.value,produtos:JSON.stringify(carrinho),total:s,frete:frete,lat:-8.8383,lng:13.2344};let r=await fetch("/api/pedido",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});let j=await r.json();let txt=`*PEDIDO KINDA #${j.id}*%0A`+carrinho.map(c=>`• ${c.icon} ${c.nome} - ${c.preco} Kz`).join("%0A")+`%0A*Total:* ${s+frete} Kz`;window.open(`https://wa.me/${wpp}?text=${txt}`,"_blank");window.location="/mapa?id="+j.id;});}
render();
</script>
""", produtos=[dict(p) for p in produtos], wpp=wpp)

@app.route("/admin")
def admin_home():
    conn=get_db()
    total_pedidos=conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    total_produtos=conn.execute("SELECT COUNT(*) FROM produtos WHERE ativo=1").fetchone()[0]
    total_vendas=conn.execute("SELECT SUM(total+frete) FROM pedidos").fetchone()[0] or 0
    conn.close()
    return render_template_string(BASE + """
<div class="header"><b>KINDA ADMIN</b><div class="nav"><a href="/">LOJA</a><a href="/admin/produtos">PRODUTOS</a><a href="/admin/pedidos">PEDIDOS</a><a href="/admin/sistema">SISTEMA</a></div></div>
<div style="padding:15px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
<div class="card"><b>{{total_pedidos}}</b><br><small>Pedidos</small></div><div class="card"><b>{{total_produtos}}</b><br><small>Produtos</small></div><div class="card"><b>{{total_vendas}} Kz</b><br><small>Vendas</small></div></div>
<div style="padding:15px"><div class="card"><a href="/admin/produtos" class="btn">📦 Editar Preços e Produtos</a><br><br><a href="/admin/pedidos" class="btn" style="background:#1565C0">📋 Ver Pedidos</a><br><br><a href="/admin/sistema" class="btn" style="background:#6A1B9A">⚙️ Controle Sistema</a><br><br><a href="/mapa" class="btn" style="background:#EF6C00">🗺️ Mapa Tempo Real</a></div></div>
""", total_pedidos=total_pedidos, total_produtos=total_produtos, total_vendas=total_vendas)

@app.route("/admin/produtos", methods=["GET","POST"])
def admin_produtos():
    conn=get_db()
    if request.method=="POST":
        if 'add' in request.form:
            conn.execute("INSERT INTO produtos (nome,kg,saco,origem,icon,cor) VALUES (?,?,?,?,?,?)",(request.form['nome'],request.form['kg'],request.form['saco'],request.form['origem'],request.form['icon'],request.form['cor']))
        elif 'edit' in request.form:
            conn.execute("UPDATE produtos SET nome=?,kg=?,saco=?,origem=?,icon=?,cor=? WHERE id=?",(request.form['nome'],request.form['kg'],request.form['saco'],request.form['origem'],request.form['icon'],request.form['cor'],request.form['id']))
        elif 'del' in request.form:
            conn.execute("UPDATE produtos SET ativo=0 WHERE id=?",(request.form['id'],))
        conn.commit()
    produtos=conn.execute("SELECT * FROM produtos WHERE ativo=1").fetchall()
    conn.close()
    return render_template_string(BASE + """
<div class="header"><b>Produtos - Editar Preços</b><div class="nav"><a href="/admin">Dashboard</a><a href="/">Loja</a></div></div>
<div style="padding:15px">
<div class="card"><h3>➕ Novo Produto</h3><form method="POST"><input name="nome" placeholder="Nome" required><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><input name="kg" type="number" placeholder="Preço kg" required><input name="saco" type="number" placeholder="Preço saco" required></div><div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px"><input name="origem" placeholder="Origem"><input name="icon" placeholder="Emoji" value="📦"><input name="cor" placeholder="#FFF9C4" value="#E8F5E9"></div><button name="add" class="btn" style="margin-top:8px">Adicionar</button></form></div><br>
<table><tr><th>Icon</th><th>Nome</th><th>kg</th><th>saco</th><th>Origem</th><th>Ações</th></tr>
{% for p in produtos %}
<tr><form method="POST"><td><input name="icon" value="{{p['icon']}}" style="width:50px"></td><td><input name="nome" value="{{p['nome']}}" style="width:120px"></td><td><input name="kg" type="number" value="{{p['kg']}}" style="width:70px"></td><td><input name="saco" type="number" value="{{p['saco']}}" style="width:80px"></td><td><input name="origem" value="{{p['origem']}}" style="width:70px"></td><td><input type="hidden" name="id" value="{{p['id']}}"><input type="hidden" name="cor" value="{{p['cor']}}"><button name="edit" class="btn" style="padding:5px 8px;font-size:11px">Salvar</button><button name="del" class="btn btn-red" style="padding:5px 8px;font-size:11px" onclick="return confirm('Apagar?')">X</button></td></form></tr>
{% endfor %}</table></div>
""", produtos=produtos)

@app.route("/admin/pedidos", methods=["GET","POST"])
def admin_pedidos():
    conn=get_db()
    if request.method=="POST":
        conn.execute("UPDATE pedidos SET status=? WHERE id=?",(request.form['status'],request.form['id']))
        conn.commit()
    pedidos=conn.execute("SELECT * FROM pedidos ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(BASE + """
<div class="header"><b>Pedidos</b><div class="nav"><a href="/admin">Dashboard</a></div></div>
<div style="padding:10px"><table><tr><th>ID</th><th>Cliente</th><th>Tel</th><th>Bairro</th><th>Total</th><th>Status</th><th>Mapa</th></tr>
{% for p in pedidos %}
<tr><td>#{{p['id']}}</td><td>{{p['cliente']}}</td><td><a href="https://wa.me/{{p['telefone']}}">{{p['telefone']}}</a></td><td>{{p['bairro']}}</td><td>{{p['total']+p['frete']}} Kz</td><td><form method="POST"><input type="hidden" name="id" value="{{p['id']}}"><select name="status" onchange="this.form.submit()"><option>{{p['status']}}</option><option>Recebido</option><option>A caminho</option><option>Entregue</option><option>Cancelado</option></select></form></td><td><a href="/mapa?id={{p['id']}}" class="btn" style="padding:4px 8px;font-size:10px">Mapa</a></td></tr>
{% endfor %}</table></div>
""", pedidos=pedidos)

@app.route("/admin/sistema", methods=["GET","POST"])
def admin_sistema():
    conn=get_db()
    if request.method=="POST":
        if 'wpp' in request.form:
            conn.execute("INSERT OR REPLACE INTO config (chave,valor) VALUES ('wpp',?)",(request.form['wpp'],))
        if 'limpar' in request.form:
            conn.execute("DELETE FROM pedidos")
        conn.commit()
    wpp=conn.execute("SELECT valor FROM config WHERE chave='wpp'").fetchone()
    conn.close()
    return render_template_string(BASE + """
<div class="header"><b>Sistema</b><div class="nav"><a href="/admin">Dashboard</a></div></div>
<div style="padding:15px;display:grid;gap:15px">
<div class="card"><h3>WhatsApp</h3><form method="POST"><input name="wpp" value="{{wpp[0] if wpp else '244923729647'}}"><button class="btn">Salvar</button></form></div>
<div class="card"><h3>Banco</h3><form method="POST" onsubmit="return confirm('Apagar todos pedidos?')"><button name="limpar" class="btn btn-red">Limpar Pedidos</button></form></div>
</div>
""", wpp=wpp)

@app.route("/api/pedido", methods=["POST"])
def criar_pedido():
    d=request.json
    conn=get_db()
    conn.execute("INSERT INTO pedidos (cliente,telefone,bairro,produtos,total,frete,status,lat,lng,data) VALUES (?,?,?,?,?,?,?,?,?,?)",(d['cliente'],d['telefone'],d['bairro'],d['produtos'],d['total'],d['frete'],'Recebido',d['lat'],d['lng'],datetime.now().strftime("%d/%m %H:%M")))
    id=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit();conn.close()
    return jsonify({"id":id})

@app.route("/api/pedido/<int:id>")
def get_pedido(id):
    conn=get_db()
    p=conn.execute("SELECT * FROM pedidos WHERE id=?",(id,)).fetchone()
    conn.close()
    return jsonify(dict(p)) if p else jsonify({"erro":"nao"})

@app.route("/mapa")
def mapa():
    return render_template_string("""
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mapa Kinda</title><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<style>body{margin:0;font-family:system-ui}#map{height:65vh}#info{padding:15px;background:#fff}</style></head><body>
<div style="padding:10px;background:#1B5E20;color:#fff;display:flex;justify-content:space-between"><b>KINDA EXPRESS AO VIVO</b><div><a href="/" style="color:#fff;margin-right:10px">Loja</a><a href="/admin" style="color:#fff">Admin</a></div></div>
<div id="map"></div><div id="info"><b id="status">Localizando...</b><br><small id="det"></small><div id="cli" style="margin-top:8px;background:#E8F5E9;padding:10px;border-radius:10px"></div></div>
<script>
let id=new URLSearchParams(window.location.search).get('id')||1;
let map=L.map('map').setView([-8.8383,13.2344],12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
let cliM,motoM;
fetch('/api/pedido/'+id).then(r=>r.json()).then(p=>{
 document.getElementById('cli').innerText=p.cliente+' - '+p.bairro+' - '+(p.total+p.frete)+' Kz';
 let cLat=L.latLng(p.lat,p.lng);
 cliM=L.marker(cLat).addTo(map).bindPopup('Cliente').openPopup();
 motoM=L.marker([-8.8383,13.2344],{icon:L.divIcon({html:'🛵',className:'',iconSize:[30,30]})}).addTo(map);
 map.fitBounds([cLat,[-8.8383,13.2344]],{padding:[40,40]});
});
let socket=io();
socket.on('posicao',d=>{if(d.id==id && motoM){motoM.setLatLng([d.lat,d.lng]);document.getElementById('status').innerText='🛵 '+d.status+' - '+d.dist+'km';}});
setInterval(()=>{socket.emit('pedir_pos',{id:id})},2000);
</script></body></html>
""")

@socketio.on('pedir_pos')
def pos(data):
    conn=get_db()
    row=conn.execute("SELECT lat,lng FROM pedidos WHERE id=?",(data['id'],)).fetchone()
    conn.close()
    if not row: return
    cli_lat,cli_lng=row['lat'],row['lng']
    lat=-8.8383+(cli_lat+8.8383)*random.uniform(0.2,0.95)
    lng=13.2344+(cli_lng-13.2344)*random.uniform(0.2,0.95)
    socketio.emit('posicao',{"id":data['id'],"lat":lat,"lng":lng,"dist":round(random.uniform(0.5,3.9),1),"status":random.choice(["Saiu para entrega","A caminho","Chegando","No bairro"])})

if __name__=="__main__":
    print("=== KINDA RODANDO ===")
    print("Loja: http://localhost:8000")
    print("Admin Produtos: http://localhost:8000/admin/produtos")
    print("WhatsApp: 244923729647")
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)
