from cryptography.fernet import Fernet
from pymongo import MongoClient
import os

# Função para gerar ou carregar a chave
def load_or_create_key():
    key_file = 'secret.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as file:
            key = file.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as file:
            file.write(key)
    return key

# Carregar a chave
key = load_or_create_key()
fernet = Fernet(key)

# Configuração do MongoDB
client = MongoClient('mongodb+srv://root:jeremias@cluster0.rrw7f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['proj']
collection = db['pacientes']

def criar_registro_paciente(nome, tratamento, historico):
    """Cria um registro de paciente criptografado no banco de dados."""
    # Criptografar os dados
    nome_criptografado = fernet.encrypt(nome.encode())
    tra_criptografado = fernet.encrypt(tratamento.encode())
    his_criptografado = fernet.encrypt(historico.encode())

    # Criar documento e inserir no MongoDB
    document = {
        "nome": nome_criptografado,
        "tratamento": tra_criptografado,
        "historico": his_criptografado
    }
    collection.insert_one(document)

def listar_pacientes_descriptografados():
    """Retorna uma lista de pacientes descriptografados como JSON."""
    pacientes_encontrados = list(collection.find())
    pacientes_descriptografados = []

    # Descriptografar cada campo e preparar o JSON para cada paciente
    for paciente in pacientes_encontrados:
        paciente_descriptografado = {
            "nome": fernet.decrypt(paciente["nome"]).decode(),
            "tratamento": fernet.decrypt(paciente["tratamento"]).decode(),
            "historico": fernet.decrypt(paciente["historico"]).decode()
        }
        pacientes_descriptografados.append(paciente_descriptografado)
    
    return pacientes_descriptografados

def buscar_paciente_por_nome(nome):
    """Busca um paciente por nome e retorna o registro descriptografado, ou None se não encontrado."""
    pacientes = listar_pacientes_descriptografados()
    for paciente in pacientes:
        if paciente["nome"] == nome:
            return paciente
    return None
