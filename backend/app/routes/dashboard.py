"""
Dashboard blueprint  –  /api/dashboard

Provides summary statistics for the authenticated user's projects and tasks.
"""

from datetime import datetime

from flask import Blueprint, jsonify

from app.models.models import Project, ProjectMember, Task, TaskStatus, db
from app.utils.auth import auth_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


# ──────────────────────────────────────────────────────────── helpers ──

def _user_project_ids(user) -> list:
    """Return all project IDs visible to *user*."""
    member_ids = [
        m.project_id
        for m in ProjectMember.query.filter_by(user_id=user.id).all()
    ]
    created_ids = [
        p.id
        for p in Project.query.filter_by(created_by=user.id).all()
    ]
    return list(set(member_ids + created_ids))


# ──────────────────────────────────────── GET /api/dashboard/summary ──

@dashboard_bp.route("/summary", methods=["GET"])
@auth_required
def summary(current_user):
    """
    Return a full dashboard summary.

    Response shape:
    {
        "projects": {
            "total": int
        },
        "tasks": {
            "total":       int,
            "todo":        int,
            "in_progress": int,
            "done":        int,
            "overdue":     int
        },
        "my_tasks": {
            "total":       int,
            "todo":        int,
            "in_progress": int,
            "done":        int,
            "overdue":     int
        }
    }
    """
    project_ids = _user_project_ids(current_user)
    now = datetime.utcnow()

    if not project_ids:
        empty = {"total": 0, "todo": 0, "in_progress": 0, "done": 0, "overdue": 0}
        return jsonify({
            "projects": {"total": 0},
            "tasks":    empty,
            "my_tasks": empty,
        }), 200

    def _counts(base_query):
        total       = base_query.count()
        todo        = base_query.filter(Task.status == TaskStatus.TODO).count()
        in_progress = base_query.filter(Task.status == TaskStatus.IN_PROGRESS).count()
        done        = base_query.filter(Task.status == TaskStatus.DONE).count()
        overdue     = base_query.filter(
            Task.deadline < now,
            Task.status != TaskStatus.DONE,
        ).count()
        return {
            "total":       total,
            "todo":        todo,
            "in_progress": in_progress,
            "done":        done,
            "overdue":     overdue,
        }

    project_tasks = Task.query.filter(Task.project_id.in_(project_ids))
    my_tasks      = Task.query.filter(Task.assigned_to == current_user.id)

    return jsonify({
        "projects": {"total": len(project_ids)},
        "tasks":    _counts(project_tasks),
        "my_tasks": _counts(my_tasks),
    }), 200


# ──────────────────────────────────────── GET /api/dashboard/overdue ──

@dashboard_bp.route("/overdue", methods=["GET"])
@auth_required
def overdue_tasks(current_user):
    """Return all overdue tasks across the user's projects."""
    project_ids = _user_project_ids(current_user)
    if not project_ids:
        return jsonify({"tasks": []}), 200

    now = datetime.utcnow()
    tasks = (
        Task.query
        .filter(
            Task.project_id.in_(project_ids),
            Task.deadline < now,
            Task.status != TaskStatus.DONE,
        )
        .order_by(Task.deadline.asc())
        .all()
    )
    return jsonify({"tasks": [t.to_dict() for t in tasks]}), 200


# ──────────────────────────────────────── GET /api/dashboard/recent ──

@dashboard_bp.route("/recent", methods=["GET"])
@auth_required
def recent_tasks(current_user):
    """Return the 10 most recently created tasks across the user's projects."""
    project_ids = _user_project_ids(current_user)
    if not project_ids:
        return jsonify({"tasks": []}), 200

    tasks = (
        Task.query
        .filter(Task.project_id.in_(project_ids))
        .order_by(Task.created_at.desc())
        .limit(10)
        .all()
    )
    return jsonify({"tasks": [t.to_dict() for t in tasks]}), 200
