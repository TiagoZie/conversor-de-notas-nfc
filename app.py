from flask import Flask, render_template, request, redirect, url_for, send_file
import csv
import os
import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)

ARQUIVO_PERFIS = 'perfis.csv'

# Criar arquivo se não existir
if not os.path.exists(ARQUIVO_PERFIS):
    with open(ARQUIVO_PERFIS, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Nome", "Agenciabanco", "NomeBanco", "NumeroConta", "Matricula", "CPF"])


@app.route("/configs", methods=["GET", "POST"])
def configs():
    return render_template("configs.html")


def ler_perfis():
    perfis = []
    with open(ARQUIVO_PERFIS, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            perfis.append(row)
    return perfis


def adicionar_perfil(nome, agencia_banco, nome_banco, numero_conta, matricula, cpf):
    with open(ARQUIVO_PERFIS, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([nome, agencia_banco, nome_banco, numero_conta, matricula, cpf])


def extrair_dados(url):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, como Gecko) "
                "Chrome/127.0.0.1 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        razao_social = soup.find("div", class_="txtTopo").text.strip()
        valor_total = soup.find("span", class_="totalNumb txtMax").text.strip()

        bloco = soup.find("h4", string=lambda t: t and "Informações gerais da Nota" in t)
        data_hora = None

        if bloco:
            li = bloco.find_next("li")  
            if li:
                texto = li.get_text(" ", strip=True)
                if "Emissão:" in texto:
                    parte = texto.split("Emissão:")[1]
                    data_hora = parte.split("-")[0].strip()

        return razao_social, valor_total, data_hora

    except Exception as e:
        return f"Erro ao acessar a URL: {e}", None


@app.route("/", methods=["GET", "POST"])
def index():
    perfis = ler_perfis()
    if request.method == "POST":
        url = request.form.get("url")
        perfil_index = int(request.form.get("perfil"))
        perfil_selecionado = perfis[perfil_index]

        razao_social, valor_total, data_hora = extrair_dados(url)

        return render_template(
            "resultado.html",
            url=url,
            razao_social=razao_social,
            valor_total=valor_total,
            data_hora=data_hora,
            perfil=perfil_selecionado,
            perfil_index=perfil_index
        )

    return render_template("index.html", perfis=perfis)


@app.route("/perfis", methods=["GET", "POST"])
def perfis():
    if request.method == "POST":
        nome = request.form.get("nome")
        agencia_banco = request.form.get("agencia_banco")
        nome_banco = request.form.get("nome_banco")
        numero_conta = request.form.get("numero_conta")
        matricula = request.form.get("matricula")
        cpf = request.form.get("cpf")

        adicionar_perfil(nome, agencia_banco, nome_banco, numero_conta, matricula, cpf)
        return redirect(url_for("index"))

    return render_template("perfis.html")


@app.route("/gerar_pdf/<int:perfil_index>", methods=["GET"])
def gerar_pdf(perfil_index):
    perfis = ler_perfis()
    perfil = perfis[perfil_index]

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(300, 800, "PREFEITURA MUNICIPAL DE SÃO MATEUS DO SUL")

    c.setFont("Helvetica", 11)
    c.drawCentredString(300, 780, "AVS – AUTORIZAÇÃO DE VIAGENS A SERVIÇO")

    c.setFont("Helvetica", 10)
    c.drawString(50, 740, f"Nome: {perfil['Nome']} CPF: {perfil['CPF']}")
    c.drawString(50, 725, f"Cargo: {perfil.get('Cargo', 'XXXXX')} Matrícula: {perfil['Matricula']}")
    c.drawString(50, 710, f"Destino: {perfil.get('Destino', 'XXXXX')}")
    c.drawString(50, 695, f"Meio de Transporte: {perfil.get('MeioTransporte', 'Outros')}")

    c.drawString(50, 670, "Descrição de Valores:")
    c.drawString(50, 655, "Data: 29/07/2025 - Almoço - R$ 160,00")
    c.drawString(50, 640, "Data: 29/07/2025 - Jantar - R$ 160,00")
    c.drawString(50, 625, "Total: R$ 320,00")

    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="avs.pdf", mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True)
