from echosphere import create_app
from echosphere.cli import start_maintenance

app = create_app()

if __name__ == "__main__":
    stopped = start_maintenance(app)
    try:
        app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False, threaded=True)
    finally:
        stopped.set()
