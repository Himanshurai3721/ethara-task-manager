"""
Tasks blueprint  –  /api/projects/<id>/tasks  and  /api/tasks
"""

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.models.models import Project, ProjectMember, Task, TaskStatus, TaskPriority, db
from app.utils.auth import auth_required, project_member_required, project_admin_required

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api")


# ──────────────────────────────────────────────────────────── helpers ──

def _parse_deadline(value: str):
    """Parse an ISO-8601 deadline string. Raises ValueError on bad input."""
    if not value:
        return None
    # Accept both "2025-06-01T00:00:00" and "2025-06-01T00:00:00Z"
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _assert_assignee_is_member(project_id: int, user_id: int) -> bool:
    """Return True if user_id is the project creator or a member."""
    project = Project.query.get(project_id)
    if project and project.created_by == user_id:
        return True
    return ProjectMember.query.filter_by(
        project_id=project_id, user_id=user_id
    ).first() is not None


# ──────────────────────────────── GET /api/projects/<id>/tasks ──

@tasks_bp.route("/projects/<int:project_id>/tasks", methods=["GET"])
@project_member_required
def list_tasks(current_user, project_id):
    """
    Return tasks for a project.

    Query params:
        status       todo | in_progress | done
        assigned_to  user_id (int)
        priority     low | medium | high
    """
    Project.query.get_or_404(project_id)

    query = Task.query.filter_by(project_id=project_id)

    status = request.args.get("status")
    if status:
        if status not in TaskStatus.ALL:
            return jsonify({"error": f"Invalid status. Choose from: {TaskStatus.ALL}"}), 400
        query = query.filter_by(status=status)

    assigned_to = request.args.get("assigned_to")
    if assigned_to:
        query = query.filter_by(assigned_to=int(assigned_to))

    priority = request.args.get("priority")
    if priority:
        if priority not in TaskPriority.ALL:
            return jsonify({"error": f"Invalid priority. Choose from: {TaskPriority.ALL}"}), 400
        query = query.filter_by(priority=priority)

    tasks = query.order_by(Task.created_at.desc()).all()
    return jsonify({"tasks": [t.to_dict() for t in tasks]}), 200


# ─────────────────────────────── POST /api/projects/<id>/tasks ──

@tasks_bp.route("/projects/<int:project_id>/tasks", methods=["POST"])
@project_member_required
def create_task(current_user, project_id):
    """
    Create a task inside a project.  Any project member may create tasks.

    Body (JSON):
        title        str   required
        description  str   optional
        status       str   optional  todo | in_progress | done  (default: todo)
        priority     str   optional  low | medium | high        (default: medium)
        deadline     str   optional  ISO-8601 datetime
        assigned_to  int   optional  user_id (must be a project member)
    """
    Project.query.get_or_404(project_id)
    data = request.get_json(silent=True) or {}

    if not data.get("title", "").strip():
        return jsonify({"error": "Task title is required"}), 400

    status = data.get("status", TaskStatus.TODO)
    if status not in TaskStatus.ALL:
        return jsonify({"error": f"Invalid status. Choose from: {TaskStatus.ALL}"}), 400

    priority = data.get("priority", TaskPriority.MEDIUM)
    if priority not in TaskPriority.ALL:
        return jsonify({"error": f"Invalid priority. Choose from: {TaskPriority.ALL}"}), 400

    deadline = None
    if data.get("deadline"):
        try:
            deadline = _parse_deadline(data["deadline"])
        except ValueError:
            return jsonify({"error": "Invalid deadline format. Use ISO-8601 (e.g. 2025-06-01T00:00:00)"}), 400

    assigned_to = data.get("assigned_to")
    if assigned_to is not None:
        if not _assert_assignee_is_member(project_id, assigned_to):
            return jsonify({"error": "Assigned user is not a member of this project"}), 400

    task = Task(
        project_id=project_id,
        title=data["title"].strip(),
        description=data.get("description", "").strip(),
        status=status,
        priority=priority,
        deadline=deadline,
        assigned_to=assigned_to,
        created_by=current_user.id,
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({
        "message": "Task created successfully",
        "task":    task.to_dict(),
    }), 201


# ──────────────────────────────────────── GET /api/tasks/<task_id> ──

@tasks_bp.route("/tasks/<int:task_id>", methods=["GET"])
@auth_required
def get_task(current_user, task_id):
    """Return a single task.  Caller must be a project member."""
    task = Task.query.get_or_404(task_id)

    is_member = _assert_assignee_is_member(task.project_id, current_user.id)
    if not is_member and current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    return jsonify({"task": task.to_dict()}), 200


# ──────────────────────────────────────── PUT /api/tasks/<task_id> ──

@tasks_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@auth_required
def update_task(current_user, task_id):
    """
    Update a task.

    - Any project member can update the **status** field.
    - Only the task creator, assignee, project admin, or system admin
      can update all other fields.

    Body (JSON):  all fields optional
        title        str
        description  str
        status       todo | in_progress | done
        priority     low | medium | high
        deadline     ISO-8601 str  (null to clear)
        assigned_to  int  (null to unassign)
    """
    task = Task.query.get_or_404(task_id)

    # Verify caller is at least a project member
    if not _assert_assignee_is_member(task.project_id, current_user.id) \
            and current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Determine privilege level
    is_task_creator = task.created_by == current_user.id
    is_assignee     = task.assigned_to == current_user.id
    is_padmin       = ProjectMember.query.filter_by(
        project_id=task.project_id, user_id=current_user.id, role="admin"
    ).first() is not None
    is_sysadmin     = current_user.role == "admin"
    can_edit_all    = is_task_creator or is_assignee or is_padmin or is_sysadmin

    # ── status (any member) ──────────────────────────────────────────────────
    if "status" in data:
        if data["status"] not in TaskStatus.ALL:
            return jsonify({"error": f"Invalid status. Choose from: {TaskStatus.ALL}"}), 400
        task.status = data["status"]

    # ── privileged fields ────────────────────────────────────────────────────
    if not can_edit_all and any(k in data for k in ("title", "description", "priority", "deadline", "assigned_to")):
        return jsonify({"error": "Only the task creator, assignee, or project admin can edit task details"}), 403

    if "title" in data:
        if not data["title"].strip():
            return jsonify({"error": "Title cannot be empty"}), 400
        task.title = data["title"].strip()

    if "description" in data:
        task.description = data["description"].strip()

    if "priority" in data:
        if data["priority"] not in TaskPriority.ALL:
            return jsonify({"error": f"Invalid priority. Choose from: {TaskPriority.ALL}"}), 400
        task.priority = data["priority"]

    if "deadline" in data:
        if data["deadline"] is None:
            task.deadline = None
        else:
            try:
                task.deadline = _parse_deadline(data["deadline"])
            except ValueError:
                return jsonify({"error": "Invalid deadline format. Use ISO-8601"}), 400

    if "assigned_to" in data:
        if data["assigned_to"] is None:
            task.assigned_to = None
        else:
            if not _assert_assignee_is_member(task.project_id, data["assigned_to"]):
                return jsonify({"error": "Assigned user is not a member of this project"}), 400
            task.assigned_to = data["assigned_to"]

    db.session.commit()
    return jsonify({
        "message": "Task updated successfully",
        "task":    task.to_dict(),
    }), 200


# ─────────────────────────────────────── DELETE /api/tasks/<task_id> ──

@tasks_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@auth_required
def delete_task(current_user, task_id):
    """Delete a task.  Only task creator, project admin, or system admin."""
    task = Task.query.get_or_404(task_id)

    is_task_creator = task.created_by == current_user.id
    is_padmin = ProjectMember.query.filter_by(
        project_id=task.project_id, user_id=current_user.id, role="admin"
    ).first() is not None

    if not (is_task_creator or is_padmin or current_user.role == "admin"):
        return jsonify({"error": "Permission denied"}), 403

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted successfully"}), 200


# ──────────────────────────────────────── GET /api/my-tasks ──

@tasks_bp.route("/my-tasks", methods=["GET"])
@auth_required
def my_tasks(current_user):
    """
    Return all tasks assigned to the current user.

    Query params:
        status  todo | in_progress | done
    """
    query = Task.query.filter_by(assigned_to=current_user.id)

    status = request.args.get("status")
    if status:
        if status not in TaskStatus.ALL:
            return jsonify({"error": f"Invalid status. Choose from: {TaskStatus.ALL}"}), 400
        query = query.filter_by(status=status)

    # Sort: tasks with a deadline first (ascending), then by created_at desc
    tasks = query.order_by(
        Task.deadline.asc(),
        Task.created_at.desc(),
    ).all()

    return jsonify({"tasks": [t.to_dict() for t in tasks]}), 200
