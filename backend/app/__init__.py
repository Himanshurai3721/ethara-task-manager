"""
Team Task Manager - Application Factory
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS

from app.models.models import db


def create_app(config_class=None):
    """
    Application factory pattern.

    Args:
        config_class: Optional config class override (useful for testing).

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__,
                static_folder=os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'),
                static_url_path='')

    # ------------------------------------------------------------------ config
    if config_class:
        app.config.from_object(config_class)
    else:
        from config import get_config
        app.config.from_object(get_config())

    # ------------------------------------------------------------------- CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # --------------------------------------------------------------- database
    db.init_app(app)

    # --------------------------------------------------------------- blueprints
    from app.routes.auth import auth_bp
    from app.routes.projects import projects_bp
    from app.routes.tasks import tasks_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(dashboard_bp)

    # ---------------------------------------------------------- static pages
    @app.route("/")
    def serve_index():
        return app.send_static_file("index.html")

    @app.route("/dashboard.html")
    def serve_dashboard():
        return app.send_static_file("dashboard.html")

    # ---------------------------------------------------------- health check
    @app.route("/api/health")
    def health_check():
        return jsonify({"status": "healthy", "message": "Team Task Manager API is running"}), 200

    # --------------------------------------------------------- error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    # --------------------------------------------------- create DB tables
    with app.app_context():
        db.create_all()

    return app
