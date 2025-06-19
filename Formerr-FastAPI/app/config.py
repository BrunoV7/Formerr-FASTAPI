"""
Configurações da Aplicação Formerr
================================

Este arquivo centraliza todas as configurações da aplicação, incluindo:
- Configurações de autenticação (OAuth, JWT)
- Configurações de banco de dados
- Configurações de CORS
- URLs de callback e redirecionamento

Todas as configurações sensíveis devem ser definidas através de variáveis de ambiente
no arquivo .env para maior segurança.

Autor: BrunoV7
"""

import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()


class Settings:
    """
    Classe de configurações da aplicação
    
    Centraliza todas as configurações necessárias para o funcionamento da API.
    Utiliza variáveis de ambiente para configurações sensíveis.
    """
    
    # ==========================================
    # CONFIGURAÇÕES GERAIS DA APLICAÇÃO
    # ==========================================
    APP_NAME: str = "Formerr API"
    DEVELOPER: str = "BrunoV7"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # ==========================================
    # CONFIGURAÇÕES DE AUTENTICAÇÃO
    # ==========================================
    
    # GitHub OAuth - Obtenha em: https://github.com/settings/applications/new
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    
    # JWT (JSON Web Token) - Para autenticação stateless
    JWT_SECRET: str = os.getenv("JWT_SECRET", "seu-jwt-secret-super-seguro-aqui")
    JWT_ALGORITHM: str = "HS256"  # Algoritmo de assinatura
    JWT_EXPIRE_DAYS: int = 30  # Token expira em 30 dias
    
    # Sessões - Para OAuth callback state
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "sua-session-secret-super-segura-aqui")
    
    # ==========================================
    # CONFIGURAÇÕES DE BANCO DE DADOS
    # ==========================================
    
    # URL completa de conexão com PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Configurações individuais (caso necessário)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "formerr_db")
    
    # ==========================================
    # CONFIGURAÇÕES DE CORS
    # ==========================================
    
    # Domínios permitidos para acessar a API
    # Em produção, especifique apenas os domínios necessários
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",    # React dev
        "http://localhost:5173",    # Vite dev
        "http://localhost:4173",    # Vite preview
        "http://localhost:8080",    # Vue dev
        # Adicione seus domínios de produção aqui
    ]
    
    # ==========================================
    # URLs DE REDIRECIONAMENTO
    # ==========================================
    
    # URLs do frontend para redirecionamento após OAuth
    FRONTEND_SUCCESS_URL: str = os.getenv("FRONTEND_SUCCESS_URL", "http://localhost:3000/auth/success")
    FRONTEND_ERROR_URL: str = os.getenv("FRONTEND_ERROR_URL", "http://localhost:3000/auth/error")
    
    # URL de callback do OAuth (deve estar registrada no GitHub)
    OAUTH_CALLBACK_URL: str = os.getenv("OAUTH_CALLBACK_URL", "http://localhost:8000/auth/github/callback")


# Instância global das configurações
# Esta instância deve ser importada por toda a aplicação
settings = Settings()