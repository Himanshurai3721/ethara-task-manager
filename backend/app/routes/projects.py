"""
Projects blueprint  –  /api/projects
"""

from flask import Blueprint, jsonify, request

from app.models.models import Project, ProjectMember, User, db
from app.utils.auth import (
    admin_required,
    auth_required,
    project_admin_required,
    project_member_required,
)

projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


# ─────────────────────────────────────────────────── GET /api/projects ──

@projects_bp.route("", methods=["GET"])
@auth_required
def list_projects(current_user):
    """
    Return all projects visible to the current user.

    - System admins see every project they created.
    - Members see projects where they are a member or creator.
    """
    if current_user.role == "admin":
        projects = Project.query.filter_by(created_by=current_user.id).all()
    else:
        member_ids = [
            m.project_id
            for m in ProjectMember.query.filter_by(user_id=current_user.id).all()
        ]
        created_ids = [
            p.id
            for p in Project.query.filter_by(created_by=current_user.id).all()
        ]
        all_ids = list(set(member_ids + created_ids))
        projects = Project.query.filter(Project.id.in_(all_ids)).all() if all_ids else []

    return jsonify({"projects": [p.to_dict(include_members=True) for p in projects]}), 200


# ────────────────────────────────────────────────── POST /api/projects ──

@projects_bp.route("", methods=["POST"])
@admin_required
def create_project(current_user):
    """
    Create a new project.  Admin only.

    Body (JSON):
        name         str  required
        description  str  optional
    """
    data = request.get_json(silent=True) or {}

    if not data.get("name", "").strip():
        return jsonify({"error": "Project name is required"}), 400

    project = Project(
        name=data["name"].strip(),
        description=data.get("description", "").strip(),
        created_by=current_user.id,
    )
    db.session.add(project)
    db.session.flush()  # get project.id before committing

    # Auto-add creator as project admin
    db.session.add(ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="admin",
    ))
    db.session.commit()

    return jsonify({
        "message": "Project created successfully",
        "project": project.to_dict(include_members=True),
    }), 201


# ──────────────────────────────────────── GET /api/projects/<project_id> ──

@projects_bp.route("/<int:project_id>", methods=["GET"])
@project_member_required
def get_project(current_user, project_id):
    """Return a single project with its members."""
    project = Project.query.get_or_404(project_id)
    return jsonify({"project": project.to_dict(include_members=True)}), 200


# ──────────────────────────────────────── PUT /api/projects/<project_id> ──

@projects_bp.route("/<int:project_id>", methods=["PUT"])
@project_admin_required
def update_project(current_user, project_id):
    """
    Update project name / description.  Project admin only.

    Body (JSON):
        name         str  optional
        description  str  optional
    """
    project = Project.query.get_or_404(project_id)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        if not data["name"].strip():
            return jsonify({"error": "Project name cannot be empty"}), 400
        project.name = data["name"].strip()

    if "description" in data:
        project.description = data["description"].strip()

    db.session.commit()
    return jsonify({
        "message": "Project updated successfully",
        "project": project.to_dict(include_members=True),
    }), 200


# ─────────────────────────────────────── DELETE /api/projects/<project_id> ──

@projects_bp.route("/<int:project_id>", methods=["DELETE"])
@project_admin_required
def delete_project(current_user, project_id):
    """Delete a project and all its tasks/members.  Project admin only."""
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted successfully"}), 200


# ──────────────────────────── GET /api/projects/<project_id>/members ──

@projects_bp.route("/<int:project_id>/members", methods=["GET"])
@project_member_required
def list_members(current_user, project_id):
    """Return all members of a project."""
    Project.query.get_or_404(project_id)
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    return jsonify({"members": [m.to_dict() for m in members]}), 200


# ─────────────────────────────────────── POST /api/projects/<project_id>/members ──

@projects_bp.route("/<int:project_id>/members", methods=["POST"])
@project_admin_required
def add_member(current_user, project_id):
    """
    Add a user to a project.  Project admin only.

    Body (JSON):
        user_id  int  required
        role     str  optional  "admin" | "member"  (default: "member")
    """
    Project.query.get_or_404(project_id)
    data = request.get_json(silent=True) or {}

    if not data.get("user_id"):
        return jsonify({"error": "'user_id' is required"}), 400

    target_user = User.query.get(data["user_id"])
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    if ProjectMember.query.filter_by(project_id=project_id, user_id=data["user_id"]).first():
        return jsonify({"error": "User is already a member of this project"}), 409

    role = data.get("role", "member")
    if role not in ("admin", "member"):
        role = "member"

    member = ProjectMember(project_id=project_id, user_id=data["user_id"], role=role)
    db.session.add(member)
    db.session.commit()

    return jsonify({
        "message": "Member added successfully",
        "member":  member.to_dict(),
    }), 201


# ──────────────── DELETE /api/projects/<project_id>/members/<user_id> ──

@projects_bp.route("/<int:project_id>/members/<int:user_id>", methods=["DELETE"])
@project_admin_required
def remove_member(current_user, project_id, user_id):
    """Remove a user from a project.  Project admin only."""
    project = Project.query.get_or_404(project_id)

    if project.created_by == user_id:
        return jsonify({"error": "Cannot remove the project creator"}), 400

    member = ProjectMember.query.filter_by(
        project_id=project_id, user_id=user_id
    ).first()
    if not member:
        return jsonify({"error": "Member not found"}), 404

    db.session.delete(member)
    db.session.commit()
    return jsonify({"message": "Member removed successfully"}), 200
