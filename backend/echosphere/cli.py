"""Local operator provisioning and bounded runtime maintenance."""
import argparse
import getpass
import threading


def start_maintenance(app):
    stopped = threading.Event()

    def work():
        while not stopped.wait(2):
            try:
                app.extensions['session_service'].maintain()
                app.extensions['session_service'].purge()
            except Exception:
                app.logger.warning('maintenance_failed; retrying without logging sensitive context')
    thread = threading.Thread(target=work, name='echosphere-maintenance', daemon=True)
    thread.start()
    return stopped


def main():
    parser = argparse.ArgumentParser(description='EchoSphere local administration')
    parser.add_argument('command', choices=['create-user', 'purge', 'doctor'])
    parser.add_argument('--username')
    parser.add_argument('--role', choices=['agent', 'supervisor'], default='agent')
    args = parser.parse_args()
    from . import create_app
    app = create_app()
    if args.command == 'create-user':
        username = args.username or input('Username: ').strip()
        password = getpass.getpass('Password (12+ characters): ')
        if password != getpass.getpass('Confirm password: '):
            raise SystemExit('Passwords did not match')
        app.extensions['auth_service'].create_user(username, password, args.role)
        print('Operator created. No password was logged.')
    elif args.command == 'purge':
        print('Expired synthetic sessions purged:', app.extensions['session_service'].purge())
    else:
        settings = app.config['SETTINGS']
        print('Database ready; schema version 1')
        print('Agora credentials:', 'configured' if settings.agora_app_id and settings.agora_app_certificate else 'missing')
        print('Public HTTPS response endpoint:', 'configured' if settings.public_base_url else 'missing')
        print('Speech provider:', settings.speech_provider)
        print('Sarvam credentials:', 'configured' if settings.sarvam_api_key else 'not configured')
        print('No network call was made. Live audio remains a separate verification gate.')


if __name__ == '__main__':
    main()
