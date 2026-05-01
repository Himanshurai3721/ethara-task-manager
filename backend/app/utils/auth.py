"""
JWT helpers and route-protection decorators.

Decorators inject the resolved `current_user` as the first positional
argument so routes never have to call get_current_user() themselves.

Usage:
    @auth_required
    def my_route(current_user):
        ...

    @admin_required
    def admin_route(current_user):
        ...

    @project_member_required
    def member_route(current_user, project_id):
        ...

    @project_admin_required
    def padmin_route(current_user, project_id):
        ...
"""

from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, jsonify, request

from app.models.models import Project, ProjectMember, User


# ──────────────────────────────────────────────────────────── token helpers ──

def generate_token(user_id: int) -> str:
    """Return a signed JWT for *user_id* valid for 24 hours."""
    payload = {
        "user_id": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token: str):
    """
    Decode *token* and return its payload.

    Returns None on expiry or any other JWT error.
    """
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _extract_user_from_request():
    """
    Pull the Bearer token from the Authorization header and return the
    matching User, or None if the token is missing / invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[len("Bearer "):]
    payload = decode_token(token)
    if not payload:
        return None

    return User.query.get(payload.get("user_id"))


# ─────────────────────────────────────────────────────────────── decorators ──

def auth_required(f):
    """Require a valid JWT. Injects `current_user` as first arg."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = _extract_user_from_request()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        return f(user, *args, **kwargs)
    return wrapper


def admin_required(f):
    """Require a valid JWT **and** system-admin role."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = _extract_user_from_request()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        if user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(user, *args, **kwargs)
    return wrapper


def project_member_required(f):
    """
    Require membership (or ownership / system-admin) in the project
    identified by the `project_id` URL parameter.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = _extract_user_from_request()
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        project_id = kwargs.get("project_id")
        if project_id is not None:
            project = Project.query.get(project_id)
            if not project:
                return jsonify({"error": "Project not found"}), 404

            is_owner  = project.created_by == user.id
            is_member = ProjectMember.query.filter_by(
                project_id=project_id, user_id=user.id
            ).first() is not None
            is_sysadmin = user.role == "admin"

            if not (is_owner or is_member or is_sysadmin):
                return jsonify({"error": "Project membership required"}), 403

        return f(user, *args, **kwargs)
    return wrapper


def project_admin_required(f):
    """
    Require project-admin role (project creator, project-level admin
    member, or system admin) for the `project_id` URL parameter.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = _extract_user_from_request()
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        project_id = kwargs.get("project_id")
        if project_id is not None:
            project = Project.query.get(project_id)
            if not project:
                return jsonify({"error": "Project not found"}), 404

            is_owner = project.created_by == user.id
            is_padmin = ProjectMember.query.filter_by(
                project_id=project_id, user_id=user.id, role="admin"
            ).first() is not None
            is_sysadmin = user.role == "admin"

            if not (is_owner or is_padmin or is_sysadmin):
                return jsonify({"error": "Project admin access required"}), 403

        return f(user, *args, **kwargs)
    return wrapper
