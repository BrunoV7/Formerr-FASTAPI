# app/auth/service.py - BEAST MODE AUTH
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from app.config import settings
from app.auth.models import UserRole, Permission, ROLE_PERMISSIONS, ROLE_LIMITS


def create_jwt_token(user_data: Dict[str, Any]) -> str:
    """Cria JWT token com dados do usuário + role info"""
    to_encode = user_data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": f"{settings.APP_NAME}-{settings.DEVELOPER}"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifica e decodifica JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except ExpiredSignatureError:
        print("🚨 JWT Token expirado")
        return None
    except InvalidTokenError as e:
        print(f"🚨 JWT Token inválido: {e}")
        return None
    except Exception as e:
        print(f"🚨 Erro JWT inesperado: {e}")
        return None


def create_user_payload(github_user: Dict[str, Any], primary_email: str, user_role: UserRole = UserRole.FREE) -> Dict[
    str, Any]:
    """Cria payload do usuário para JWT com role info"""
    permissions = ROLE_PERMISSIONS.get(user_role, [])
    limits = ROLE_LIMITS.get(user_role, {})

    return {
        "github_id": github_user["id"],
        "username": github_user["login"],
        "name": github_user.get("name") or github_user["login"],
        "email": primary_email or github_user.get("email"),
        "avatar_url": github_user["avatar_url"],
        "github_url": github_user["html_url"],

        # 🔥 BEAST MODE: Role & Permissions
        "role": user_role.value,
        "permissions": [p.value for p in permissions],
        "limits": limits,

        # Metadata
        "created_at": datetime.utcnow().isoformat(),
        "user_type": "github_user",
        "sprint_version": "brunov7_beast_mode_2025",
        "is_brunov7": github_user["login"] == "BrunoV7"
    }


def check_permission(user_data: Dict[str, Any], required_permission: Permission) -> bool:
    """Verifica se usuário tem permissão específica"""
    user_permissions = user_data.get("permissions", [])
    return required_permission.value in user_permissions


def check_usage_limit(user_data: Dict[str, Any], limit_type: str, current_usage: int) -> bool:
    """Verifica se usuário pode executar ação baseado nos limites"""
    limits = user_data.get("limits", {})
    max_allowed = limits.get(limit_type, 0)

    # -1 significa unlimited (Enterprise/Admin)
    if max_allowed == -1:
        return True

    return current_usage < max_allowed


class RoleManager:
    """Gerenciador de roles e permissões"""

    @staticmethod
    def can_create_form(user_data: Dict[str, Any], current_form_count: int) -> Dict[str, Any]:
        """Verifica se pode criar formulário"""
        can_create = check_permission(user_data, Permission.CREATE_FORM)
        within_limit = check_usage_limit(user_data, "max_forms", current_form_count)

        return {
            "allowed": can_create and within_limit,
            "reason": "ok" if (can_create and within_limit) else "limit_exceeded" if can_create else "no_permission",
            "current_count": current_form_count,
            "max_allowed": user_data.get("limits", {}).get("max_forms", 0),
            "role": user_data.get("role", "unknown")
        }

    @staticmethod
    def can_export_data(user_data: Dict[str, Any]) -> bool:
        """Verifica se pode exportar dados"""
        return check_permission(user_data, Permission.EXPORT_DATA)

    @staticmethod
    def can_use_webhooks(user_data: Dict[str, Any]) -> bool:
        """Verifica se pode usar webhooks"""
        return check_permission(user_data, Permission.USE_WEBHOOKS)

    @staticmethod
    def get_user_capabilities(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retorna todas as capacidades do usuário"""
        role = user_data.get("role", "free")
        permissions = user_data.get("permissions", [])
        limits = user_data.get("limits", {})

        return {
            "role": role,
            "is_brunov7": user_data.get("is_brunov7", False),
            "capabilities": {
                "can_create_forms": Permission.CREATE_FORM.value in permissions,
                "can_delete_forms": Permission.DELETE_FORM.value in permissions,
                "can_export_data": Permission.EXPORT_DATA.value in permissions,
                "can_use_webhooks": Permission.USE_WEBHOOKS.value in permissions,
                "can_use_api": Permission.USE_API.value in permissions,
                "can_custom_branding": Permission.CUSTOM_BRANDING.value in permissions,
                "can_manage_team": Permission.MANAGE_TEAM.value in permissions,
                "is_admin": Permission.MANAGE_USERS.value in permissions
            },
            "limits": limits,
            "upgrade_benefits": RoleManager._get_upgrade_benefits(role)
        }

    @staticmethod
    def _get_upgrade_benefits(current_role: str) -> Dict[str, Any]:
        """Benefícios de upgrade"""
        if current_role == UserRole.FREE.value:
            return {
                "next_tier": "pro",
                "benefits": [
                    "Unlimited forms",
                    "10k submissions/month",
                    "Data export",
                    "Webhooks integration",
                    "API access"
                ]
            }
        elif current_role == UserRole.PRO.value:
            return {
                "next_tier": "enterprise",
                "benefits": [
                    "Unlimited submissions",
                    "Team collaboration",
                    "Custom branding",
                    "Priority support"
                ]
            }
        else:
            return {"message": "You have the highest tier!"}


# Instances
role_manager = RoleManager()