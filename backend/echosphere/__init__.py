from flask import Flask

from .api.routes import api
from .config import Settings
from .errors import register_error_handlers
from .services.agora_gateway import AgoraGateway
from .services.sessions import SessionService
from .storage import Database


def create_app(
    settings: Settings | None = None,
    gateway: AgoraGateway | None = None,
) -> Flask:
    resolved = settings or Settings.from_environment()
    app = Flask(__name__)
    app.config.update(
        DEBUG=resolved.app_env == "development",
        JSON_SORT_KEYS=False,
        SETTINGS=resolved,
        SECRET_KEY=resolved.secret_key,
        MAX_CONTENT_LENGTH=65536,
    )

    database = Database(resolved.database_path)
    app.extensions['database'] = database
    app.extensions["session_service"] = SessionService(
        gateway=gateway or AgoraGateway(resolved),
        settings=resolved,
        database=database,
    )
    app.register_blueprint(api, url_prefix="/api")
    register_error_handlers(app)
    # Built assets are served from Flask for a same-origin demo deployment.
    from pathlib import Path
    from flask import send_from_directory
    dist = Path(__file__).resolve().parents[2] / 'frontend' / 'dist'

    @app.get('/')
    @app.get('/demo/call')
    @app.get('/console')
    def web_page():
        return send_from_directory(dist, 'index.html')

    @app.get('/assets/<path:filename>')
    def web_asset(filename):
        return send_from_directory(dist / 'assets', filename)

    @app.get('/health/live')
    def live_alias():
        return {'status': 'ok'}

    @app.get('/health/ready')
    def ready_alias():
        from .api.routes import health_ready
        return health_ready()
    return app
