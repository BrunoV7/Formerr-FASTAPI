from enum import Enum
from typing import List, Dict, Any


class UserRole(str, Enum):
    FREE = "free"  # 3 forms, 100 submissions/month
    PRO = "pro"  # Unlimited forms, 10k submissions/month
    ENTERPRISE = "enterprise"  # Everything + team features
    ADMIN = "admin"  # Platform admin


class Permission(str, Enum):
    # Form permissions
    CREATE_FORM = "create_form"
    DELETE_FORM = "delete_form"
    EXPORT_DATA = "export_data"

    # Team permissions
    INVITE_MEMBERS = "invite_members"
    MANAGE_TEAM = "manage_team"

    # Advanced features
    USE_WEBHOOKS = "use_webhooks"
    USE_API = "use_api"
    CUSTOM_BRANDING = "custom_branding"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"


ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.FREE: [
        Permission.CREATE_FORM,
    ],
    UserRole.PRO: [
        Permission.CREATE_FORM,
        Permission.DELETE_FORM,
        Permission.EXPORT_DATA,
        Permission.USE_WEBHOOKS,
        Permission.USE_API,
    ],
    UserRole.ENTERPRISE: [
        Permission.CREATE_FORM,
        Permission.DELETE_FORM,
        Permission.EXPORT_DATA,
        Permission.USE_WEBHOOKS,
        Permission.USE_API,
        Permission.CUSTOM_BRANDING,
        Permission.INVITE_MEMBERS,
        Permission.MANAGE_TEAM,
    ],
    UserRole.ADMIN: list(Permission)  # All permissions
}

ROLE_LIMITS: Dict[UserRole, Dict[str, int]] = {
    UserRole.FREE: {
        "max_forms": 3,
        "max_submissions_per_month": 100,
        "max_questions_per_form": 10,
        "max_file_size_mb": 5,
    },
    UserRole.PRO: {
        "max_forms": 100,
        "max_submissions_per_month": 10000,
        "max_questions_per_form": 100,
        "max_file_size_mb": 50,
    },
    UserRole.ENTERPRISE: {
        "max_forms": -1,  # Unlimited
        "max_submissions_per_month": -1,  # Unlimited
        "max_questions_per_form": -1,  # Unlimited
        "max_file_size_mb": 500,
    },
    UserRole.ADMIN: {
        "max_forms": -1,
        "max_submissions_per_month": -1,
        "max_questions_per_form": -1,
        "max_file_size_mb": 1000,
    }
}