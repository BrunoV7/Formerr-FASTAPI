"""
Rotas de Autenticação - Sistema OAuth com GitHub
==============================================

Este módulo implementa o sistema de autenticação da aplicação usando:
- GitHub OAuth 2.0 para login social
- JWT (JSON Web Tokens) para manutenção de sessão
- Sistema de permissões baseado em roles

Fluxo de autenticação:
1. Usuário acessa /auth/github
2. É redirecionado para GitHub
3. GitHub redireciona para /auth/github/callback
4. Sistema cria/atualiza usuário e gera JWT
5. Usuário é redirecionado para frontend com token

Autor: BrunoV7
"""

from typing import Dict, Any
import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from app.config import settings
from app.auth.service import create_jwt_token, create_user_payload
from app.dependencies import get_current_user

# Criação do roteador para rotas de autenticação
router = APIRouter()

# Configuração do cliente OAuth para GitHub
# GitHub usa OAuth 2.0 padrão (não OpenID Connect)
oauth = OAuth()
oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    # URLs específicas do GitHub OAuth
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    client_kwargs={
        'scope': 'user:email',  # Permissões solicitadas: dados básicos + email
        'token_endpoint_auth_method': 'client_secret_post'
    }
)


@router.get("/github")
async def github_auth(request: Request):
    """Inicia GitHub OAuth flow"""
    return await oauth.github.authorize_redirect(request, settings.OAUTH_CALLBACK_URL)


@router.get("/github/callback")
async def github_callback(request: Request):
    """GitHub OAuth callback"""
    try:
        # Get access token
        token = await oauth.github.authorize_access_token(request)

        # Fetch user data from GitHub API
        async with httpx.AsyncClient() as client:
            # Get user info
            user_response = await client.get(
                'https://api.github.com/user',
                headers={'Authorization': f'token {token["access_token"]}'}
            )
            user_data = user_response.json()

            # Get user emails
            email_response = await client.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'token {token["access_token"]}'}
            )
            emails = email_response.json()

        # Find primary email
        primary_email = next(
            (email['email'] for email in emails if email.get('primary')),
            None
        )

        # Create JWT payload and token
        jwt_payload = create_user_payload(user_data, primary_email)
        jwt_token = create_jwt_token(jwt_payload)

        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{settings.FRONTEND_SUCCESS_URL}?token={jwt_token}",
            status_code=302
        )

    except Exception as e:
        print(f"❌ OAuth Error: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_ERROR_URL}?reason=oauth_failed",
            status_code=302
        )


@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retorna informações do usuário autenticado"""
    return {
        "user": current_user,
        "authenticated": True,
        "session_time": current_user.get("created_at"),
        "github_profile": f"https://github.com/{current_user.get('username')}",
        "is_brunov7": current_user.get("username") == "BrunoV7"
    }


@router.post("/logout")
async def logout():
    """Logout endpoint"""
    return {
        "message": "Logout realizado com sucesso",
        "action": "remove_token_from_frontend"
    }


@router.get("/test")
async def test_auth(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Test protected endpoint"""
    return {
        "message": f"🎉 Olá {current_user['name']}! Auth funcionando!",
        "user": current_user["username"],
        "github_id": current_user["github_id"],
        "domain": "auth",
        "brunov7_detected": current_user.get("username") == "BrunoV7"
    }