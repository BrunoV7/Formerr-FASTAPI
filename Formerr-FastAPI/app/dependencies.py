"""
Dependencies da Aplicação Formerr
===============================

Este arquivo contém as dependências reutilizáveis do FastAPI para:
- Autenticação de usuários
- Verificação de permissões
- Validação de tokens JWT

Dependencies são funções que podem ser injetadas automaticamente
nas rotas do FastAPI usando o sistema de Dependency Injection.

Autor: BrunoV7
"""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, Request, status
from app.auth.service import verify_jwt_token, check_permission
from app.auth.models import Permission


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency para obter o usuário atualmente autenticado
    
    Esta função:
    1. Extrai o token JWT do header Authorization
    2. Verifica se o token é válido
    3. Retorna os dados do usuário
    4. Levanta exceção se o token for inválido
    
    Args:
        request: Objeto Request do FastAPI
        
    Returns:
        Dict contendo os dados do usuário autenticado
        
    Raises:
        HTTPException: Se o token for inválido ou não fornecido
        
    Exemplo de uso:
        @app.get("/perfil")
        async def get_profile(user: dict = Depends(get_current_user)):
            return {"usuario": user["name"]}
    """
    auth_header = request.headers.get("authorization")
    
    # Verifica se o header Authorization está presente
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação necessário. Use: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extrai o token do header (remove "Bearer ")
    token = auth_header.split(" ")[1]
    
    # Verifica a validade do token
    user_data = verify_jwt_token(token)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_data


async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Dependency para obter usuário opcional
    
    Útil para rotas que podem funcionar tanto com usuário autenticado
    quanto com usuário anônimo (ex: visualização pública de formulários).
    
    Args:
        request: Objeto Request do FastAPI
        
    Returns:
        Dict com dados do usuário se autenticado, None caso contrário
        
    Exemplo de uso:
        @app.get("/formulario/publico/{form_id}")
        async def view_form(form_id: str, user: dict = Depends(get_optional_user)):
            # Se user é None, mostra versão pública
            # Se user existe, mostra versão personalizada
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        # Se não conseguir obter o usuário, retorna None (usuário anônimo)
        return None


def require_permission(permission: Permission):
    """
    Factory de dependency para exigir permissão específica
    
    Esta função retorna uma dependency que verifica se o usuário
    tem uma permissão específica antes de permitir acesso à rota.
    
    Args:
        permission: Permissão requerida (enum Permission)
        
    Returns:
        Function: Dependency que verifica a permissão
        
    Exemplo de uso:
        @app.delete("/formulario/{form_id}")
        async def delete_form(
            form_id: str,
            user: dict = Depends(require_permission(Permission.DELETE_FORMS))
        ):
            # Apenas usuários com permissão DELETE_FORMS podem acessar
    """
    def check_user_permission(current_user: Dict[str, Any] = Depends(get_current_user)):
        """
        Verifica se o usuário atual possui a permissão necessária
        
        Args:
            current_user: Dados do usuário (injetado automaticamente)
            
        Returns:
            Dict: Dados do usuário se tiver permissão
            
        Raises:
            HTTPException: Se o usuário não tiver a permissão necessária
        """
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{permission.value}' necessária para esta ação. "
                       f"Verifique seu plano ou entre em contato com o administrador."
            )
        return current_user

    return check_user_permission


# ==========================================
# DEPENDENCIES ESPECÍFICAS POR FUNCIONALIDADE
# ==========================================

def require_export_permission():
    """
    Dependency para operações de exportação de dados
    
    Usuários precisam ter permissão de exportação para:
    - Baixar dados de submissões em CSV/Excel
    - Gerar relatórios
    - Fazer backup de formulários
    """
    return require_permission(Permission.EXPORT_DATA)


def require_webhook_permission():
    """
    Dependency para operações com webhooks
    
    Usuários precisam ter permissão de webhooks para:
    - Criar webhooks
    - Configurar integrações
    - Gerenciar callbacks
    """
    return require_permission(Permission.USE_WEBHOOKS)


def require_admin_permission():
    """
    Dependency para operações administrativas
    
    Apenas administradores podem:
    - Gerenciar outros usuários
    - Acessar métricas globais
    - Configurar permissões
    """
    return require_permission(Permission.MANAGE_USERS)