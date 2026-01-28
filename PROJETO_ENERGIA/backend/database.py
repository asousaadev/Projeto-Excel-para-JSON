from sqlite3 import OperationalError # Importação mantida, mas não utilizada no código atual
import psycopg2
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
# Correção da linha de importação:
from psycopg2 import OperationalError as PSQLOperationalError 

load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

def conecta():
    """Estabelece conexão com o banco de dados PostgreSQL usando psycopg2."""
    try:
        # psycop2 usa OperationalError para falhas de conexão
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "energia_db"),
            user=os.getenv("DB_USER", "user"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        print("Conexão com o banco de dados estabelecida com sucesso.")
        return conn
    except PSQLOperationalError as e: # Captura o erro específico do psycopg2
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Exemplo de uso
if __name__ == "__main__":
    connection = conecta()
    if connection:
        # Você pode usar a conexão aqui
        connection.close()
