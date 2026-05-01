"""
Authentication blueprint  –  /api/auth
"""

from flask import Blueprint, jsonify, request

from app.models.models import User, db
from app.utils.auth import auth_required, generate_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ──────────────────────────────────────────────────────────── POST /register ──

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user.

    Body (JSON):
        username  str  required
        email     str  required
        password  str  required
        role      str  optional  "admin" | "member"  (default: "member")

    Returns 201 with token + user on success.
    """
    data = request.get_json(silent=True) or {}

    # ── validation ──────────────────────────────────────────────────────────
    for field in ("username", "email", "password"):
        if not data.get(field, "").strip():
            return jsonify({"error": f"'{field}' is required"}), 400

    if len(data["password"]) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already taken"}), 409

    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "Email already registered"}), 409

    # ── create user ─────────────────────────────────────────────────────────
    role = data.get("role", "member")
    if role not in ("admin", "member"):
        role = "member"

    user = User(
        username=data["username"].strip(),
        email=data["email"].lower().strip(),
        role=role,
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "token":   generate_token(user.id),
        "user":    user.to_dict(),
    }), 201


# ─────────────────────────────────────────────────────────────── POST /login ──

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user and return a JWT.

    Body (JSON):
        username  str  required
        password  str  required

    Returns 200 with token + user on success.
    """
    data = request.get_json(silent=True) or {}

    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=data["username"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({
        "message": "Login successful",
        "token":   generate_token(user.id),
        "user":    user.to_dict(),
    }), 200


# ──────────────────────────────────────────────────────────────── GET /me ──

@auth_bp.route("/me", methods=["GET"])
@auth_required
def me(current_user):
    """Return the authenticated user's profile."""
    return jsonify({"user": current_user.to_dict()}), 200


# ─────────────────────────────────────────────────────────── GET /users ──

@auth_bp.route("/users", methods=["GET"])
@auth_required
def list_users(current_user):
    """
    Return all users (authenticated users only).
    Useful for populating assignment dropdowns.
    """
    users = User.query.order_by(User.username).all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200
