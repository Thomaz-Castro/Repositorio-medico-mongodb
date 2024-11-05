import PySimpleGUI as sg
import pacientes
import bcrypt
from pymongo import MongoClient
import smtplib
import email.message
import json
import random
import string

# Conectar ao MongoDB Atlas
client = MongoClient('mongodb+srv://root:jeremias@cluster0.rrw7f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['proj']
collection = db['adm']

# Variáveis de autenticação de email
senha_gmail = 'tobs rkop wrft bmov'
gmail_from = 'felipemoraiscorrea@gmail.com'

def verificar_login(nome, senha):
    funcionario = collection.find_one({'nome': nome})
    if funcionario and bcrypt.checkpw(senha.encode(), funcionario['hash_senha'].encode()):
        return True
    return False

def pretty_2FA_email(recipient_name, verification_code):
   # Começa a construção da string HTML
    html = f"""<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Código de Verificação</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: auto;
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        h2 {{
            color: #333333;
        }}
        .code {{
            background-color: #e7f3fe;
            border: 1px solid #b3d7ff;
            color: #31708f;
            padding: 10px;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            border-radius: 4px;
            margin: 20px 0;
        }}
        p {{
            color: #555555;
            line-height: 1.6;
        }}
        .footer {{
            font-size: 12px;
            color: #aaaaaa;
            text-align: center;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Olá, {recipient_name}!</h2>
        <p>Seu código de verificação é:</p>
        <div class="code">{verification_code}</div>
        <p>Por favor, use este código para concluir seu processo de verificação.</p>
        <div class="footer">Se você não solicitou este código, pode ignorar este e-mail.</div>
    </div>
</body>
</html>"""

    return html

def pretty_share(json_data):
    # Converte a string JSON em um dicionário
    data = json.loads(json_data)
    
    # Começa a construção da string HTML
    html = '<html>\n<head>\n<style>\n'
    html += 'table { width: 100%; border-collapse: collapse; }\n'
    html += 'th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }\n'
    html += 'th { background-color: #f2f2f2; }\n'
    html += '</style>\n</head>\n<body>\n'
    html += '<h2>Informações do Paciente</h2>\n'
    html += '<table>\n<tr>\n'
    
    # Cria os cabeçalhos da tabela
    for key in data.keys():
        html += f'<th>{key.capitalize()}</th>\n'
    html += '</tr>\n<tr>\n'
    
    # Adiciona os dados na tabela
    for value in data.values():
        html += f'<td>{value}</td>\n'
    html += '</tr>\n</table>\n</body>\n</html>'
    
    return html


def criar_funcionario(nome, senha, email):
    hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
    collection.insert_one({
        'nome': nome,
        'hash_senha': hash_senha.decode(),
        'gmail': email
    })
    sg.popup("Funcionário criado com sucesso!")

def consultar_func():
    funcionarios = list(collection.find({}, {'nome': 1, 'gmail': 1}))
    return funcionarios

def obter_email_funcionario(nome_funcionario):
    funcionario = collection.find_one({'nome': nome_funcionario}, {'gmail': 1})
    if funcionario:
        return funcionario['gmail']
    else:
        sg.popup("Funcionário não encontrado.")
        return None

def enviar_email(email_from, email_to, paciente_dados, senha):  
    msg = email.message.Message()
    msg['Subject'] = "Compartilhamento Médico"
    msg['From'] = email_from
    msg['To'] = email_to
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(paciente_dados)

    with smtplib.SMTP('smtp.gmail.com: 587') as envia:
        envia.starttls()
        envia.login(msg['From'], senha)
        envia.sendmail(msg['From'], [msg['To']], msg.as_string().encode('utf-8'))
    sg.popup('Email enviado com sucesso!')

def email_2FA(numero, gmail_from, gmail_to, senha):
    msg = email.message.Message()
    msg['Subject'] = "Código de validação de dois fatores"
    msg['From'] = gmail_from
    msg['To'] = gmail_to
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(numero)

    with smtplib.SMTP('smtp.gmail.com: 587') as envia:
        envia.starttls()
        envia.login(msg['From'], senha)
        envia.sendmail(msg['From'], [msg['To']], msg.as_string().encode('utf-8'))

def login_window():
    layout = [
        [sg.Text("Digite seu nome"), sg.Input(key="-NOME-")],
        [sg.Text("Digite sua senha"), sg.Input(key="-SENHA-", password_char="*")],
        [sg.Button("Login"), sg.Button("Sair")]
    ]
    return sg.Window("Login do Sistema", layout, finalize=True)

def auth_2fa_window():
    layout = [
        [sg.Text("Digite o código de verificação 2FA enviado ao seu email")],
        [sg.Input(key="-CODIGO-")],
        [sg.Button("Verificar"), sg.Button("Sair")]
    ]
    return sg.Window("Verificação de Dois Fatores", layout, finalize=True)

def main_window():
    layout = [
        [sg.Button("Criar Funcionário"), sg.Button("Consultar Registros Médicos"), sg.Button("Compartilhar Registros")],
        [sg.Button("Sair")]
    ]
    return sg.Window("Menu Principal", layout, finalize=True)

def criar_funcionario_window():
    layout = [
        [sg.Text("Nome do Funcionário"), sg.Input(key="-NOME_FUNC-")],
        [sg.Text("Senha"), sg.Input(key="-SENHA_FUNC-", password_char="*")],
        [sg.Text("Email"), sg.Input(key="-EMAIL_FUNC-")],
        [sg.Button("Criar"), sg.Button("Sair")]
    ]
    return sg.Window("Criar Funcionário", layout, finalize=True)

def consultar_funcionario_window():
    funcionarios = consultar_func()
    nomes_func = [func['nome'] for func in funcionarios]
    layout = [
        [sg.Text("Selecione o Funcionário")],
        [sg.Listbox(nomes_func, key="-FUNCIONARIO-", size=(30, 6))],
        [sg.Button("Consultar"), sg.Button("Sair")]
    ]
    return sg.Window("Consultar Funcionário", layout, finalize=True)

def selecionar_paciente_window():
    pacientes_dados = pacientes.listar_pacientes_descriptografados()
    nomes_pacientes = [paciente['nome'] for paciente in pacientes_dados]
    layout = [
        [sg.Text("Selecione o Paciente")],
        [sg.Listbox(nomes_pacientes, key="-PACIENTE-", size=(30, 6))],
        [sg.Button("Selecionar"), sg.Button("Sair")]
    ]
    return sg.Window("Selecionar Paciente", layout, finalize=True)

def consultar_registros_medicos():
    registros = pacientes.listar_pacientes_descriptografados()
    
    # Verifica se há registros para evitar erros
    if not registros:
        sg.popup("Nenhum registro encontrado.")
        return

    # Extrai os cabeçalhos a partir das chaves do primeiro registro
    headers = list(registros[0].keys())

    # Extrai os valores dos registros para exibir em tabela
    data = [[registro[key] for key in headers] for registro in registros]

    layout = [
        [sg.Text("Registros Médicos")],
        [sg.Table(values=data, headings=headers, display_row_numbers=False, auto_size_columns=True, 
                  justification='center', num_rows=min(10, len(data)), key="-TABELA-")],
        [sg.Button("Fechar")]
    ]

    window = sg.Window("Registros Médicos", layout, finalize=True)
    event, values = window.read()
    window.close()


# Janela de Login Inicial
#window = login_window()
window = main_window()

# Loop principal do programa
while True:
    event, values = window.read()
    
    if event == sg.WINDOW_CLOSED:
        break

    if event == "Login":
        nome = values["-NOME-"]
        senha = values["-SENHA-"]
        if verificar_login(nome, senha):
            caracteres = string.ascii_letters + string.digits
            numero_2fa = ''.join(random.choices(caracteres, k=8)).strip()
            gmail_to = collection.find_one({'nome': nome}).get('gmail')
            email_2FA(pretty_2FA_email(nome, numero_2fa), gmail_from, gmail_to, senha_gmail)
            window.close()
            window = auth_2fa_window()
        else:
            sg.popup("Login inválido")

    elif event == "Verificar":
        codigo_usuario = values["-CODIGO-"]
        if codigo_usuario == numero_2fa:
            sg.popup("Código correto! Acesso concedido.")
            window.close()
            window = main_window()
        else:
            sg.popup("Código incorreto")

    elif event == "Criar Funcionário":
        window.close()
        window = criar_funcionario_window()

    elif event == "Consultar Registros Médicos":
        consultar_registros_medicos()

    elif event == "Compartilhar Registros":
        window.close()
        window = consultar_funcionario_window()

    elif event == "Criar":
        nome_func = values["-NOME_FUNC-"]
        senha_func = values["-SENHA_FUNC-"]
        email_func = values["-EMAIL_FUNC-"]
        criar_funcionario(nome_func, senha_func, email_func)
        window.close()
        window = main_window()

    elif event == "Consultar":
        funcionario = values["-FUNCIONARIO-"][0]
        window.close()
        window = selecionar_paciente_window()

    elif event == "Selecionar":
        paciente_selecionado = values["-PACIENTE-"][0]
        paciente_dados = json.dumps(next(p for p in pacientes.listar_pacientes_descriptografados() if p['nome'] == paciente_selecionado), indent=4)
        email_func = obter_email_funcionario(funcionario)
        if email_func:
            enviar_email(gmail_from, email_func, pretty_share(paciente_dados), senha_gmail)
        window.close()
        window = main_window()

    elif event == "Sair":
        break

# Fechar o cliente MongoDB
client.close()
window.close()
