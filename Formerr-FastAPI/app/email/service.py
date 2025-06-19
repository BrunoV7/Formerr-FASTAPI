import os
import random
import string
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from mailjet_rest import Client
from app.config import settings


class EmailService:
    """Beast Mode Email Service com Mailjet"""

    def __init__(self):
        self.api_key = os.getenv('MJ_APIKEY_PUBLIC', '')
        self.api_secret = os.getenv('MJ_APIKEY_PRIVATE', '')
        self.client = Client(auth=(self.api_key, self.api_secret), version='v3.1')
        self.from_email = "noreply@formerr.brunov7.dev"  # Seu domínio
        self.from_name = "Formerr - BrunoV7"

    def generate_auth_code(self, length: int = 6) -> str:
        """Gera código de 6 dígitos"""
        return ''.join(random.choices(string.digits, k=length))

    async def send_form_invitation(
            self,
            to_email: str,
            to_name: str,
            form_title: str,
            form_url: str,
            sender_name: str,
            custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia convite para preencher formulário"""

        subject = f"📝 Você foi convidado(a) para preencher: {form_title}"

        text_content = f"""
Olá {to_name}!

{sender_name} convidou você para preencher o formulário: "{form_title}"

{custom_message or "Por favor, acesse o link abaixo para responder:"}

🔗 Link do formulário: {form_url}

Este convite foi enviado pelo Formerr - a plataforma de formulários mais avançada do Brasil.

---
Formerr by BrunoV7 🚀
https://formerr.brunov7.dev
        """

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Convite para Formulário</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
        .content {{ background: white; padding: 30px; border: 1px solid #e1e5e9; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
        .footer {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; font-size: 14px; color: #666; }}
        .badge {{ background: #28a745; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Convite para Formulário</h1>
            <span class="badge">FORMERR BEAST MODE</span>
        </div>

        <div class="content">
            <h2>Olá {to_name}! 👋</h2>

            <p><strong>{sender_name}</strong> convidou você para preencher o formulário:</p>

            <h3 style="color: #667eea;">"{form_title}"</h3>

            {f'<p style="background: #f8f9fa; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0;"><em>{custom_message}</em></p>' if custom_message else ''}

            <p>Clique no botão abaixo para acessar o formulário:</p>

            <a href="{form_url}" class="button">🚀 Preencher Formulário</a>

            <p><small>Ou copie e cole este link no seu navegador:<br>
            <code style="background: #f8f9fa; padding: 5px; border-radius: 4px;">{form_url}</code></small></p>
        </div>

        <div class="footer">
            <p><strong>Formerr by BrunoV7</strong> 🔥<br>
            A plataforma de formulários mais avançada do Brasil</p>
            <p><a href="https://formerr.brunov7.dev">formerr.brunov7.dev</a></p>
        </div>
    </div>
</body>
</html>
        """

        data = {
            'Messages': [{
                "From": {
                    "Email": self.from_email,
                    "Name": self.from_name
                },
                "To": [{
                    "Email": to_email,
                    "Name": to_name
                }],
                "Subject": subject,
                "TextPart": text_content,
                "HTMLPart": html_content,
                "CustomID": f"form_invitation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }]
        }

        try:
            result = self.client.send.create(data=data)
            return {
                "success": True,
                "status_code": result.status_code,
                "message_id": result.json().get('Messages', [{}])[0].get('MessageID'),
                "to": to_email,
                "subject": subject
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "to": to_email
            }

    async def send_auth_code(
            self,
            to_email: str,
            to_name: str,
            auth_code: str,
            form_title: str,
            expires_in_minutes: int = 10
    ) -> Dict[str, Any]:
        """Envia código de autenticação de 6 dígitos"""

        subject = f"🔐 Código de Acesso: {auth_code} - {form_title}"

        text_content = f"""
Olá {to_name}!

Seu código de acesso para o formulário "{form_title}" é:

🔐 CÓDIGO: {auth_code}

Este código expira em {expires_in_minutes} minutos.

Se você não solicitou este código, ignore este email.

---
Formerr by BrunoV7 🚀
        """

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Código de Acesso</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
        .content {{ background: white; padding: 30px; border: 1px solid #e1e5e9; text-align: center; }}
        .code {{ background: #f8f9fa; border: 2px dashed #28a745; padding: 30px; margin: 30px 0; border-radius: 10px; }}
        .code-number {{ font-size: 36px; font-weight: bold; color: #28a745; letter-spacing: 8px; font-family: 'Courier New', monospace; }}
        .footer {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; font-size: 14px; color: #666; }}
        .warning {{ background: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Código de Acesso</h1>
            <p>Formerr Beast Mode Security</p>
        </div>

        <div class="content">
            <h2>Olá {to_name}! 👋</h2>

            <p>Seu código de acesso para o formulário:</p>
            <h3 style="color: #28a745;">"{form_title}"</h3>

            <div class="code">
                <p>Seu código é:</p>
                <div class="code-number">{auth_code}</div>
            </div>

            <div class="warning">
                ⏰ <strong>Este código expira em {expires_in_minutes} minutos</strong>
            </div>

            <p>Digite este código na página do formulário para continuar.</p>
        </div>

        <div class="footer">
            <p><strong>Formerr by BrunoV7</strong> 🔥<br>
            Segurança de nível enterprise</p>
            <p>Se você não solicitou este código, ignore este email.</p>
        </div>
    </div>
</body>
</html>
        """

        data = {
            'Messages': [{
                "From": {
                    "Email": self.from_email,
                    "Name": self.from_name
                },
                "To": [{
                    "Email": to_email,
                    "Name": to_name or "Usuário"
                }],
                "Subject": subject,
                "TextPart": text_content,
                "HTMLPart": html_content,
                "CustomID": f"auth_code_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }]
        }

        try:
            result = self.client.send.create(data=data)
            return {
                "success": True,
                "status_code": result.status_code,
                "message_id": result.json().get('Messages', [{}])[0].get('MessageID'),
                "to": to_email,
                "code": auth_code,
                "expires_in": expires_in_minutes
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "to": to_email
            }

    async def send_submission_notification(
            self,
            to_email: str,
            form_title: str,
            submitter_name: str,
            submission_count: int,
            form_id: str
    ) -> Dict[str, Any]:
        """Notifica owner sobre nova submissão"""

        subject = f"🎉 Nova resposta em '{form_title}'"

        dashboard_url = f"https://formerr.brunov7.dev/dashboard/forms/{form_id}"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Nova Submissão</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
        .content {{ background: white; padding: 30px; border: 1px solid #e1e5e9; }}
        .stats {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .button {{ display: inline-block; background: #ff6b6b; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Nova Submissão!</h1>
        </div>

        <div class="content">
            <h2>Boa notícia! 📈</h2>

            <p>Você recebeu uma nova resposta no formulário:</p>
            <h3 style="color: #ff6b6b;">"{form_title}"</h3>

            <div class="stats">
                <p><strong>👤 Respondido por:</strong> {submitter_name or "Anônimo"}</p>
                <p><strong>📊 Total de respostas:</strong> {submission_count}</p>
                <p><strong>⏰ Data:</strong> {datetime.utcnow().strftime('%d/%m/%Y às %H:%M')} UTC</p>
            </div>

            <p>Veja os detalhes no seu dashboard:</p>
            <a href="{dashboard_url}" class="button">📊 Ver Dashboard</a>
        </div>
    </div>
</body>
</html>
        """

        data = {
            'Messages': [{
                "From": {
                    "Email": self.from_email,
                    "Name": self.from_name
                },
                "To": [{
                    "Email": to_email,
                    "Name": "Formerr User"
                }],
                "Subject": subject,
                "HTMLPart": html_content,
                "CustomID": f"submission_notification_{form_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }]
        }

        try:
            result = self.client.send.create(data=data)
            return {
                "success": True,
                "status_code": result.status_code,
                "notification_sent": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Instance
email_service = EmailService()