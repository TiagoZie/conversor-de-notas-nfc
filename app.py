from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
import sqlite3
import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import datetime
import re

app = Flask(__name__)
app.secret_key = "20197431209uwdquw9ex83u"

DB_FILE = "database.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

       
        c.execute("""
        CREATE TABLE IF NOT EXISTS perfis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            agencia_banco TEXT,
            nome_banco TEXT,
            numero_conta TEXT,
            matricula TEXT,
            cpf TEXT,
            tipo_servidor TEXT,
            cargo TEXT
        )
        """)

      
        c.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            nome_secretaria TEXT,
            nome_secretario TEXT,
            cargo_secretario TEXT,
            cidade_partida TEXT,
            numero_solicitacao INTEGER
        )
        """)
        c.execute("SELECT COUNT(*) FROM configs")
        if c.fetchone()[0] == 0:
            c.execute("""
            INSERT INTO configs (id, nome_secretaria, nome_secretario, cargo_secretario, cidade_partida, numero_solicitacao)
            VALUES (1, '', '', '', '', 1)
            """)


        c.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            razao_social TEXT,
            valor_total TEXT,
            data_hora TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()


init_db()


# =====================================================
#  Funções auxiliares
# =====================================================
def get_db_row(query, params=()):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        row = c.fetchone()
        cols = [desc[0] for desc in c.description] if c.description else []
        return dict(zip(cols, row)) if row else None


def get_db_rows(query, params=()):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        rows = c.fetchall()
        cols = [desc[0] for desc in c.description] if c.description else []
        return [dict(zip(cols, r)) for r in rows]


def execute_db(query, params=()):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        return c.lastrowid


# =====================================================
#  Configurações
# =====================================================
def get_configs():
    cfg = get_db_row("SELECT * FROM configs WHERE id = 1")
    return cfg or {
        "nome_secretaria": "",
        "nome_secretario": "",
        "cargo_secretario": "",
        "cidade_partida": "",
        "numero_solicitacao": 1
    }


def save_configs(nome_secretaria, nome_secretario, cargo_secretario, cidade_partida, numero_solicitacao):
    execute_db("""
        UPDATE configs
        SET nome_secretaria = ?, nome_secretario = ?, cargo_secretario = ?, cidade_partida = ?, numero_solicitacao = ?
        WHERE id = 1
    """, (nome_secretaria, nome_secretario, cargo_secretario, cidade_partida, numero_solicitacao))


def incrementar_numero_solicitacao():
    cfg = get_configs()
    novo_num = (cfg.get("numero_solicitacao") or 0) + 1
    execute_db("UPDATE configs SET numero_solicitacao = ? WHERE id = 1", (novo_num,))
    return cfg.get("numero_solicitacao")


# =====================================================
#  Perfis
# =====================================================
def ler_perfis():
    return get_db_rows("SELECT * FROM perfis")


def adicionar_perfil(nome, agencia_banco, nome_banco, numero_conta, matricula, cpf, tipo_servidor, cargo):
    execute_db("""
        INSERT INTO perfis (nome, agencia_banco, nome_banco, numero_conta, matricula, cpf, tipo_servidor, cargo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, agencia_banco, nome_banco, numero_conta, matricula, cpf, tipo_servidor, cargo))


# =====================================================
#  Extração dos dados da nota
# =====================================================
def extrair_dados(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        razao = soup.find("div", class_="txtTopo")
        valor = soup.find("span", class_="totalNumb txtMax")
        numero_tag = soup.find("strong", string=re.compile(r"N[úu]mero", re.I))
        if numero_tag:
            numero_nota = numero_tag.next_sibling.strip()
        else:
            numero_nota = "Indisponível"
        razao_social = razao.text.strip() if razao else "Não encontrado"
        valor_total = valor.text.strip() if valor else "0,00"
        data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        itens = [{
            "numero": numero_nota,
            "data": data_hora.split()[0],
            "descricao": "Despesa (extraída)",
            "valor": valor_total
        }]

        return razao_social, valor_total, data_hora, itens, numero_nota

    except Exception as e:
        return f"Erro: {e}", None, None, [], None


# =====================================================
#  Rotas
# =====================================================
@app.route("/")
def home():
    return redirect(url_for("index"))


@app.route("/configs", methods=["GET", "POST"])
def configs():
    cfg = get_configs()
    if request.method == "POST":
        nome_secretaria = request.form["nome_secretaria"]
        nome_secretario = request.form["nome_secretario"]
        cargo_secretario = request.form["cargo_secretario"]
        cidade_partida = request.form["cidade_partida"]
        numero_solicitacao = int(request.form["numero_solicitacao"])

        save_configs(nome_secretaria, nome_secretario, cargo_secretario, cidade_partida, numero_solicitacao)
        flash("Configurações atualizadas com sucesso!", "success")
        return redirect(url_for("configs"))
    return render_template("configs.html", configs=cfg)


@app.route("/perfis", methods=["GET", "POST"])
def perfis():
    if request.method == "POST":
        nome = request.form["nome"]
        matricula = request.form["matricula"]
        cpf = request.form["cpf"]
        agencia = request.form["agencia_banco"]
        banco = request.form["nome_banco"]
        conta = request.form["numero_conta"]
        tipo_servidor = request.form["tipo_servidor"]
        cargo = request.form["cargo"]

        adicionar_perfil(nome, agencia, banco, conta, matricula, cpf, tipo_servidor, cargo)
        return redirect(url_for("index"))

    return render_template("perfis.html")


@app.route("/add_url_session", methods=["POST"])
def add_url_session():
    """Adiciona uma URL à lista na sessão via AJAX."""
    if 'urls' not in session:
        session['urls'] = []
    
    url = request.json.get('url')
    if not url:
        return {"status": "error", "message": "No URL provided"}, 400
    
    session['urls'].append(url)
    session.modified = True  # Marcar sessão como modificada
    return {"status": "success", "url_added": url, "count": len(session['urls'])}


@app.route("/clear_urls_session", methods=["POST"])
def clear_urls_session():
    """Limpa a lista de URLs da sessão."""
    session['urls'] = []
    session['itens'] = []
    session['combined_valor_total'] = "0,00"
    session['combined_razoes'] = []
    session['last_data_hora'] = None
    session.modified = True
    return {"status": "success"}


@app.route("/index", methods=["GET", "POST"])
def index():
    perfis = ler_perfis()
    if request.method == "POST":
        # Processamento do formulário principal (botão GERAR)
        urls = session.get("urls", [])
        if not urls:
            flash("Nenhuma nota foi adicionada. Adicione pelo menos uma URL.", "error")
            return redirect(url_for("index"))

        cidade_destino = request.form["cidade_destino"]
        tipo_solicitacao = request.form["tipo_solicitacao"]
        perfil_index = int(request.form["perfil"])

        # Salva dados da viagem na sessão
        session["cidade_destino"] = cidade_destino
        session["tipo_solicitacao"] = tipo_solicitacao
        session["perfil_index"] = perfil_index

        all_itens = []
        all_razoes = set()
        total_valor = 0.0
        last_data_hora = None
        errored_urls = []

        # Itera e processa todas as URLs
        for url in urls:
            razao_social, valor_str, data_hora, itens, numero_nota = extrair_dados(url)
            
            if "Erro:" in razao_social or valor_str is None:
                errored_urls.append(url)
                continue 

            all_itens.extend(itens)
            all_razoes.add(razao_social)
            try:
                # Converte valor monetário brasileiro (ex: "1.234,56") para float
                clean_valor = valor_str.replace('.', '').replace(',', '.')
                total_valor += float(clean_valor)
            except (ValueError, TypeError):
                errored_urls.append(f"{url} (valor inválido: {valor_str})")
                continue
            
            last_data_hora = data_hora

        if errored_urls:
            flash(f"Algumas URLs falharam: {', '.join(errored_urls)}", "error")

        if not all_itens:
            flash("Nenhuma nota pôde ser processada com sucesso.", "error")
            return redirect(url_for("index"))

        # Formata o valor total de volta para o formato brasileiro
        valor_total_combined = f"{total_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # Salva resultados combinados na sessão para o PDF e resultado.html
        session["itens"] = all_itens
        session["combined_valor_total"] = valor_total_combined
        session["combined_razoes"] = list(all_razoes)
        session["last_data_hora"] = last_data_hora
        session["all_urls"] = urls # Salva para mostrar em resultado.html

        return render_template("resultado.html", 
                               urls=urls, 
                               razoes_sociais=list(all_razoes),
                               valor_total=valor_total_combined, 
                               data_hora=last_data_hora,
                               perfil=perfis[perfil_index], 
                               perfil_index=perfil_index,
                               itens=all_itens, 
                               tipo_solicitacao=tipo_solicitacao,
                               cidade_destino=cidade_destino)
    
    # Método GET: Apenas exibe a página
    # Limpa a sessão ao carregar a página inicial para começar do zero
    # Ou, para persistir, passamos as URLs existentes:
    added_urls = session.get('urls', [])
    if not added_urls: # Se for a primeira visita, zera tudo
         session['urls'] = []
         session['itens'] = []
         
    return render_template("index.html", perfis=perfis, added_urls=session.get('urls', []))


# =====================================================
# PDF
# =====================================================
@app.route("/gerar_pdf/<int:perfil_index>")
def gerar_pdf(perfil_index):
    perfis = ler_perfis()
    if perfil_index >= len(perfis):
        flash("Erro de perfil. Tente novamente.", "error")
        return redirect(url_for("index"))
        
    perfil = perfis[perfil_index]
    cfg = get_configs()

    numero_solicitacao = incrementar_numero_solicitacao()
    
    # Pega os dados COMBINADOS da sessão
    tipo_solicitacao = session.get("tipo_solicitacao", "")
    cidade_destino = session.get("cidade_destino", "")
    itens = session.get("itens", [])
    valor_total = session.get("combined_valor_total", "0,00")

    # Se não houver itens (sessão expirou ou erro), volta ao início
    if not itens:
        flash("Não há itens para gerar o PDF. Sessão expirou ou erro.", "error")
        return redirect(url_for("index"))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x_left = 90  
    x_center = width / 2
    y = height - 70

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(x_center, y, "PREFEITURA MUNICIPAL DE SÃO MATEUS DO SUL")
    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(x_center, y, "AVS – AUTORIZAÇÃO DE VIAGENS A SERVIÇO")
    y -= 35

    c.setFont("Helvetica", 10)
    c.drawString(x_left, y, "( ) adiantamento    ( ) ressarcimento")
    if "adiant" in tipo_solicitacao.lower():
        c.drawString(x_left + 9, y, "X")
    elif "ress" in tipo_solicitacao.lower():
        c.drawString(x_left + 85, y, "X")
    y -= 25

    c.drawString(x_left, y, f"Solicitação nº {numero_solicitacao:03d}")
    y -= 20
    c.drawString(x_left, y, f"Secretaria: {cfg.get('nome_secretaria')}")
    y -= 25
    c.drawString(x_left, y, f"Nome: {perfil['nome']}       CPF: {perfil['cpf']}")
    y -= 20
    c.drawString(x_left, y, f"Cargo: {perfil['cargo']}       Matrícula: {perfil['matricula']}")
    y -= 25

    tipo = perfil.get("tipo_servidor", "").lower()
    tipos = ["efetivo", "comissionado", "agente politico", "conselheiro municipal"]
    c.drawString(x_left, y, "Servidor:")
    base_x = x_left + 65
    espacos = [0, 55, 138, 224]
    for i, t in enumerate(tipos):
        mark = "x" if t == tipo else " "
        c.drawString(base_x + espacos[i], y, f"({mark}) {t}")
    y -= 35

    c.drawString(x_left, y, f"Serviço a ser realizado: Viagem para {cidade_destino}")
    y -= 20
    c.drawString(x_left, y, f"Destino: {cidade_destino}")
    y -= 20
    c.drawString(x_left, y, "Meio de Transporte: (  ) Veículo Oficial   (  ) Coletivo   (  ) Outros")
    y -= 35

    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_left, y, "Descrição de Valores:")
    y -= 15

    headers = ["Número da nota", "Data", "Descrição", "Valor total"]
    col_widths = [100, 90, 230, 90]
    row_height = 18
    table_x = x_left - 25
    table_y = y
    
    # NÃO HÁ MAIS FALLBACK - 'itens' deve vir preenchido da sessão
    
    c.setFont("Helvetica-Bold", 9)
    cx = table_x + 5
    for i, h in enumerate(headers):
        c.drawString(cx, table_y - 12, h)
        cx += col_widths[i]
    table_y -= row_height

    c.setFont("Helvetica", 9)
    start_y = table_y

    for it in itens:
        numero = it.get("numero", "1")
        data = it.get("data", "")
        desc = it.get("descricao", "")[:40]
        valor = it.get("valor", "")

        c.drawString(table_x + 5, start_y - 12, numero)
        c.drawString(table_x + 110, start_y - 12, data)
        c.drawString(table_x + 200, start_y - 12, desc)
        c.drawRightString(table_x + 505, start_y - 12, valor)

        start_y -= row_height

    total_rows = len(itens) + 1
    total_height = total_rows * row_height
    total_width = sum(col_widths)

    c.rect(table_x, table_y - (len(itens) * row_height), total_width, total_height)

    for i in range(total_rows ):
        y_line = table_y - (i * row_height)
        c.line(table_x, y_line, table_x + total_width, y_line)
        
    x_pos = table_x
    for w in col_widths:
        x_pos += w
        c.line(x_pos, table_y, x_pos, table_y - (len(itens) * row_height))

    total_y = table_y - (len(itens) * row_height) - 25
    c.setFont("Helvetica-Bold", 10)
    c.rect(table_x + total_width - 120, total_y, 120, 20)
    # Usa o 'valor_total' combinado vindo da sessão
    c.drawRightString(table_x + total_width - 10, total_y + 6, f"Total: {valor_total}")
    y = total_y - 50


    c.setFont("Helvetica", 10)
    c.drawString(x_left, y, f"C/C {perfil['numero_conta']}  – Ag. {perfil['agencia_banco']}  – Banco {perfil['nome_banco']}")
    y -= 50

    data_atual = datetime.date.today().strftime("%d/%m/%Y")
    c.drawString(x_left, y, f"{cfg.get('cidade_partida', 'São Mateus do Sul')}, {data_atual}")
    y -= 70

    c.line(x_left, y, x_left + 200, y)
    c.drawString(x_left, y - 12, "Assinatura do servidor solicitante")
    c.line(x_left + 250, y, x_left + 450, y)
    c.drawString(x_left + 250, y - 12, f"{cfg['nome_secretario']}")
    c.drawString(x_left + 250, y - 26, f"{cfg['cargo_secretario']}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="avs.pdf", mimetype="application/pdf")
    #return send_file(buffer, as_attachment=False, mimetype="application/pdf") #caso precise editar sem baixar toda vez



if __name__ == "__main__":
    app.run(debug=True)