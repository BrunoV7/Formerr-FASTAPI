from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import redis
import json
from app.email.service import email_service


# Redis para cache de códigos (ou use in-memory dict para desenvolvimento)
class AuthCodeManager:
    """Gerenciador de códigos de autenticação"""

    def __init__(self):
        # Para desenvolvimento, usar dict em memória
        # Em produção, usar Redis
        self.codes_cache: Dict[str, Dict[str, Any]] = {}

    def generate_and_send_code(
            self,
            email: str,
            form_id: str,
            form_title: str,
            user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Gera e envia código por email"""

        # Gerar código
        auth_code = email_service.generate_auth_code()

        # Criar chave única
        cache_key = f"auth_code:{form_id}:{email}"

        # Dados do código
        code_data = {
            "code": auth_code,
            "email": email,
            "form_id": form_id,
            "form_title": form_title,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
            "attempts": 0,
            "max_attempts": 3,
            "used": False
        }

        # Salvar no cache (10 minutos)
        self.codes_cache[cache_key] = code_data

        # Enviar email
        email_result = email_service.send_auth_code(
            to_email=email,
            to_name=user_name or "Usuário",
            auth_code=auth_code,
            form_title=form_title,
            expires_in_minutes=10
        )

        return {
            "success": True,
            "code_sent": email_result.get("success", False),
            "email": email,
            "expires_in": 10,
            "form_id": form_id,
            "cache_key": cache_key  # Para debug
        }

    def verify_code(
            self,
            email: str,
            form_id: str,
            submitted_code: str
    ) -> Dict[str, Any]:
        """Verifica código submetido"""

        cache_key = f"auth_code:{form_id}:{email}"
        code_data = self.codes_cache.get(cache_key)

        if not code_data:
            return {
                "valid": False,
                "reason": "code_not_found",
                "message": "Código não encontrado. Solicite um novo código."
            }

        # Verificar se já foi usado
        if code_data.get("used"):
            return {
                "valid": False,
                "reason": "code_already_used",
                "message": "Este código já foi utilizado."
            }

        # Verificar expiração
        expires_at = datetime.fromisoformat(code_data["expires_at"])
        if datetime.utcnow() > expires_at:
            # Limpar código expirado
            del self.codes_cache[cache_key]
            return {
                "valid": False,
                "reason": "code_expired",
                "message": "Código expirado. Solicite um novo código."
            }

        # Verificar tentativas
        if code_data["attempts"] >= code_data["max_attempts"]:
            del self.codes_cache[cache_key]
            return {
                "valid": False,
                "reason": "max_attempts_exceeded",
                "message": "Muitas tentativas. Solicite um novo código."
            }

        # Incrementar tentativas
        code_data["attempts"] += 1

        # Verificar código
        if submitted_code == code_data["code"]:
            # Marcar como usado
            code_data["used"] = True
            code_data["used_at"] = datetime.utcnow().isoformat()

            return {
                "valid": True,
                "message": "Código válido! Acesso liberado.",
                "form_id": form_id,
                "email": email,
                "authenticated_at": datetime.utcnow().isoformat()
            }
        else:
            return {
                "valid": False,
                "reason": "invalid_code",
                "message": f"Código incorreto. Tentativas restantes: {code_data['max_attempts'] - code_data['attempts']}",
                "attempts_remaining": code_data["max_attempts"] - code_data["attempts"]
            }

    def cleanup_expired_codes(self):
        """Limpa códigos expirados (executar periodicamente)"""
        now = datetime.utcnow()
        expired_keys = []

        for key, data in self.codes_cache.items():
            expires_at = datetime.fromisoformat(data["expires_at"])
            if now > expires_at:
                expired_keys.append(key)

        for key in expired_keys:
            del self.codes_cache[key]

        return len(expired_keys)


# Instance
auth_code_manager = AuthCodeManager()