"""
Firebase Admin SDK initialisation and ID-token verification.

Set the FIREBASE_CREDENTIALS environment variable to the full JSON content
of your Firebase service-account key (Settings → Service accounts → Generate
new private key).  If the variable is absent the module is a no-op so the
rest of the app still starts up in local development.

All firebase_admin imports are deferred to runtime so the module is always
importable — even in CI environments where firebase-admin is not installed.
"""
import json
import os

_app = None


def _init():
    global _app
    if _app is not None:
        return
    cred_json = os.environ.get('FIREBASE_CREDENTIALS', '')
    if not cred_json:
        raise RuntimeError(
            'FIREBASE_CREDENTIALS env var is not set. '
            'Add your service-account JSON as a single-line env var on Render.'
        )
    import firebase_admin
    from firebase_admin import credentials
    cred = credentials.Certificate(json.loads(cred_json))
    _app = firebase_admin.initialize_app(cred)


def verify_id_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims dict."""
    _init()
    from firebase_admin import auth as _fb_auth
    return _fb_auth.verify_id_token(id_token)
