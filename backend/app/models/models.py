"""
Database models for Team Task Manager.

Tables:
    users           - Registered users (admin / member roles)
    projects        - Projects created by admins
    project_members - Many-to-many: users <-> projects
    tasks           - Tasks belonging to a project
"""

from datetime import datetime
import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ─────────────────────────────────────────────────────────────── constants ──

class TaskStatus:
    TODO        = "todo"
    IN_PROGRESS = "in_progress"
    DONE        = "done"
    ALL         = [TODO, IN_PROGRESS, DONE]


class TaskPriority:
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    ALL    = [LOW, MEDIUM, HIGH]


class UserRole:
    ADMIN  = "admin"
    MEMBER = "member"


class ProjectRole:
    ADMIN  = "admin"
    MEMBER = "member"


# ──────────────────────────────────────────────────────────────── models ────

class User(db.Model):
    """Registered user. Role is system-wide: admin or member."""

    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20),  nullable=False, default=UserRole.MEMBER)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    created_projects    = db.relationship("Project",       backref="creator",  lazy="dynamic",
                                          foreign_keys="Project.created_by")
    project_memberships = db.relationship("ProjectMember", backref="user",     lazy="dynamic")
    assigned_tasks      = db.relationship("Task",          backref="assignee", lazy="dynamic",
                                          foreign_keys="Task.assigned_to")
    created_tasks       = db.relationship("Task",          backref="creator",  lazy="dynamic",
                                          foreign_keys="Task.created_by")

    # ---------------------------------------------------------------- auth
    def set_password(self, password: str) -> None:
        """Hash *password* with bcrypt and store it."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Return True if *password* matches the stored hash."""
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))

    # ---------------------------------------------------------------- repr
    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "username":   self.username,
            "email":      self.email,
            "role":       self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.username!r}>"


class Project(db.Model):
    """A project that groups tasks together."""

    __tablename__ = "projects"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default="")
    created_by  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    members = db.relationship("ProjectMember", backref="project", lazy="dynamic",
                               cascade="all, delete-orphan")
    tasks   = db.relationship("Task",          backref="project", lazy="dynamic",
                               cascade="all, delete-orphan")

    def to_dict(self, include_members: bool = False) -> dict:
        data = {
            "id":          self.id,
            "name":        self.name,
            "description": self.description,
            "created_by":  self.created_by,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
            "updated_at":  self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_members:
            data["members"] = [m.to_dict() for m in self.members.all()]
        return data

    def __repr__(self) -> str:
        return f"<Project {self.name!r}>"


class ProjectMember(db.Model):
    """Association between a User and a Project, with a project-level role."""

    __tablename__ = "project_members"

    id         = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"),    nullable=False)
    role       = db.Column(db.String(20), nullable=False, default=ProjectRole.MEMBER)
    joined_at  = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "project_id": self.project_id,
            "user_id":    self.user_id,
            "username":   self.user.username if self.user else None,
            "role":       self.role,
            "joined_at":  self.joined_at.isoformat() if self.joined_at else None,
        }

    def __repr__(self) -> str:
        return f"<ProjectMember user={self.user_id} project={self.project_id}>"


class Task(db.Model):
    """A task belonging to a project."""

    __tablename__ = "tasks"

    id          = db.Column(db.Integer, primary_key=True)
    project_id  = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    status      = db.Column(db.String(20),  nullable=False, default=TaskStatus.TODO)
    priority    = db.Column(db.String(20),  nullable=False, default=TaskPriority.MEDIUM)
    deadline    = db.Column(db.DateTime, nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_overdue(self) -> bool:
        """True when deadline has passed and task is not done."""
        return bool(
            self.deadline
            and self.status != TaskStatus.DONE
            and self.deadline < datetime.utcnow()
        )

    def to_dict(self) -> dict:
        return {
            "id":               self.id,
            "project_id":       self.project_id,
            "title":            self.title,
            "description":      self.description,
            "status":           self.status,
            "priority":         self.priority,
            "deadline":         self.deadline.isoformat() if self.deadline else None,
            "assigned_to":      self.assigned_to,
            "assigned_username": self.assignee.username if self.assignee else None,
            "created_by":       self.created_by,
            "creator_username": self.creator.username if self.creator else None,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
            "updated_at":       self.updated_at.isoformat() if self.updated_at else None,
            "is_overdue":       self.is_overdue(),
        }

    def __repr__(self) -> str:
        return f"<Task {self.title!r}>"
