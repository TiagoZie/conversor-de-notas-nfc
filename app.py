from flask import Flask, render_template, request, redirect, url_for
import csv
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

ARQUIVO_PERFIS = 'perfis.csv'

# Cria o arquivo CSV se não existir
if not os.path.exists(ARQUIVO_PERFIS):
    with open(ARQUIVO_PERFIS, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Nome", "DadosBancarios", "Matricula", "CPF"])

# Função para ler todos os perfis cadastrados no CSV
# Deve ser utilizada sempre que precisar listar ou acessar os perfis existentes
def ler_perfis():
    perfis = []  # Lista que armazenará os perfis
    # Abre o arquivo CSV no modo leitura
    with open(ARQUIVO_PERFIS, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)  # Lê cada linha do CSV como um dicionário (chave = cabeçalho)
        for row in reader:
            perfis.append(row)  # Adiciona cada perfil lido à lista
    return perfis  # Retorna a lista completa de perfis

# Função para adicionar um novo perfil ao CSV
# Deve ser utilizada quando o usuário cadastrar um perfil novo
def adicionar_perfil(nome, dados_bancarios, matricula, cpf):
    # Abre o arquivo CSV no modo append (adicionar ao final do arquivo)
    with open(ARQUIVO_PERFIS, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Escreve os dados do novo perfil como uma nova linha no CSV
        writer.writerow([nome, dados_bancarios, matricula, cpf])

# Função para extrair dados de uma página web
# Deve ser utilizada quando se quer coletar informações de uma URL específica
def extrair_dados(url):
    try:
        # Define headers para simular um navegador e evitar bloqueios do site
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, como Gecko) "
                          "Chrome/127.0.0.1 Safari/537.36"
        }
        # Faz requisição HTTP à URL fornecida
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Garante que a requisição foi bem-sucedida
        soup = BeautifulSoup(response.text, 'html.parser')  # Analisa o HTML da página
        # Extrai o conteúdo do elemento <div> com classe "txtTopo"
        razao_social = soup.find("div", class_="txtTopo").text.strip()
        # Extrai o conteúdo do elemento <span> com classe "totalNumb txtMax"
        valor_total = soup.find("span", class_="totalNumb txtMax").text.strip()
        return razao_social, valor_total  # Retorna os dados extraídos
    except Exception as e:
        # Retorna uma mensagem de erro caso a requisição ou parsing falhem
        return f"Erro ao acessar a URL: {e}", None

@app.route("/", methods=["GET", "POST"])
def index():
    perfis = ler_perfis()
    if request.method == "POST":
        url = request.form.get("url")
        perfil_index = int(request.form.get("perfil"))
        perfil_selecionado = perfis[perfil_index]

        razao_social, valor_total = extrair_dados(url)

        return render_template("resultado.html",
                               url=url,
                               razao_social=razao_social,
                               valor_total=valor_total,
                               perfil=perfil_selecionado)
    return render_template("index.html", perfis=perfis)

@app.route("/perfis", methods=["GET", "POST"])
def perfis():
    if request.method == "POST":
        nome = request.form.get("nome")
        dados_bancarios = request.form.get("dados_bancarios")
        matricula = request.form.get("matricula")
        cpf = request.form.get("cpf")
        adicionar_perfil(nome, dados_bancarios, matricula, cpf)
        return redirect(url_for("index"))
    return render_template("perfis.html")

if __name__ == "__main__":
    app.run(debug=True)
