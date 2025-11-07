Microframework Utilizado:
Flask
Bibliotecas utilizadas:
Sqlite3
Requests
BeautifulSoup
Reportlab
BytesIO
Datetime
RE

NO TERMINAL LINUX
-source .venv/bin/activate
-pip install -r requirements.txt
-python app.py

NO TERMINAL WINDOWS (POWERSHELL)
-Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
-python -m venv .venv
-.venv\Scripts\activate
(ainda no .venv)
-pip install -r requirements.txt
-python app.py


COMANDOS ÚTEIS PARA O VENV:
-deactivate (para sair do venv)
-rm -rf .venv (para apagar o venv, para resolver problemas)
-python3 -m venv .venv (criar venv)
-rm -rf __pycache__/ (as vezes  os python lembra caminhos)
-unset MONGO_URL
-echo $MONGO_URL

É necessário desativar as extensões de bloquear anúncios 
Após acessar o http://127.0.0.1:5000/index, caso não abra automaticamente com o comando, o acesso ao sistema pode ser acessado por esse link.
