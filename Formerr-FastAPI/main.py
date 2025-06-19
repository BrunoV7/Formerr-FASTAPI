"""
Formerr API - Sistema de Criação e Gerenciamento de Formulários
=============================================================

Este é o arquivo principal da aplicação FastAPI do Formerr.
Desenvolvido por: BrunoV7

Funcionalidades principais:
- Criação e gerenciamento de formulários
- Sistema de autenticação OAuth (GitHub)
- Submissões de formulários
- Webhooks para integração
- Sistema de email
- Analytics e métricas

Estrutura da aplicação:
- /auth - Rotas de autenticação
- /api/forms - Gerenciamento de formulários
- /api/submissions - Submissões dos formulários
- /api/webhooks - Integração com webhooks
- /api/email - Sistema de email
- /api/analytics - Analytics e métricas
- /api/public - APIs públicas
"""

from fastapi import FastAPI
from datetime import datetime
import os
import psutil

# Importação das configurações da aplicação
from app.config import settings

# Importação dos middlewares para CORS e sessões
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Importação de todos os roteadores da aplicação
from app.public.routes import router as public_router
from app.auth.routes import router as auth_router
from app.forms.routes import router as forms_router
from app.submissions.routes import router as submissions_router
from app.webhooks.routes import router as webhooks_router
from app.email.routes import router as email_router
from app.analytics.routes import router as analytics_router

# Criação da instância principal do FastAPI
app = FastAPI(
    title="Formerr API",
    description="Sistema profissional de criação e gerenciamento de formulários",
    version="1.0.0",
    docs_url="/docs",  # Documentação Swagger UI
    redoc_url="/redoc"  # Documentação ReDoc alternativa
)

# Configuração do middleware CORS (Cross-Origin Resource Sharing)
# Permite que o frontend acesse a API de diferentes domínios
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Em produção, especificar domínios permitidos
    allow_credentials=True,  # Permite envio de cookies e headers de autenticação
    allow_methods=["*"],  # Permite todos os métodos HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permite todos os headers
)

# Configuração do middleware de sessão para OAuth
# Necessário para manter estado durante o fluxo de autenticação
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET  # Chave secreta para criptografar sessões
)

# Registro de todos os roteadores da aplicação
# Cada roteador gerencia um conjunto específico de funcionalidades

# APIs públicas - acessíveis sem autenticação
app.include_router(public_router, prefix="/api/public", tags=["🌐 APIs Públicas"])

# Sistema de autenticação - GitHub OAuth
app.include_router(auth_router, prefix="/auth", tags=["🔐 Autenticação"])

# Gerenciamento de formulários - CRUD completo
app.include_router(forms_router, prefix="/api/forms", tags=["📝 Formulários"])

# Submissões de formulários - dados enviados pelos usuários
app.include_router(submissions_router, prefix="/api/submissions", tags=["📊 Submissões"])

# Webhooks - integração com sistemas externos
app.include_router(webhooks_router, prefix="/api/webhooks", tags=["🔗 Webhooks"])

# Sistema de email - envio de notificações
app.include_router(email_router, prefix="/api/email", tags=["📧 Email"])

# Analytics - métricas e relatórios
app.include_router(analytics_router, prefix="/api/analytics", tags=["📊 Analytics"])

@app.get("/")
async def root():
    """
    Endpoint raiz da API - Informações básicas do sistema
    
    Returns:
        dict: Informações sobre o status e versão da API
    """
    return {
        "message": "Formerr API funcionando corretamente",
        "status": "online",
        "version": "1.0.0",
        "desenvolvedor": "BrunoV7",
        "timestamp": datetime.utcnow().isoformat(),
        "documentacao": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Endpoint de health check - Verifica o status da aplicação e recursos do sistema
    
    Este endpoint é usado para:
    - Monitoramento da aplicação
    - Load balancers verificarem se o serviço está saudável
    - Métricas de performance do sistema
    
    Returns:
        dict: Informações detalhadas sobre o status do sistema
    """
    # Coleta informações de memória do sistema
    memory = psutil.virtual_memory()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "sistema": {
            "memoria_uso_percentual": memory.percent,
            "memoria_disponivel_gb": round(memory.available / (1024 ** 3), 2),
            "cpu_uso_percentual": psutil.cpu_percent(interval=1),
            "disco_uso_percentual": psutil.disk_usage('/').percent
        },
        "servicos": {
            "api": "funcionando",
            "autenticacao": "ativo",
            "email": "configurado"
        }
    }

if __name__ == "__main__":
    """
    Ponto de entrada da aplicação quando executada diretamente
    
    Configurações de desenvolvimento:
    - host="0.0.0.0": Permite acesso de qualquer IP (útil para desenvolvimento)
    - port=8000: Porta padrão da aplicação
    - reload=True: Reinicia automaticamente quando arquivos são modificados
    """
    import uvicorn
    
    print("� Iniciando Formerr API...")
    print("� Documentação disponível em: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
