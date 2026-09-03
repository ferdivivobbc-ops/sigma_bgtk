import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore


def get_firestore_client():
    """Return a Firestore client using Firebase service-account credentials."""
    if not firebase_admin._apps:
        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if credentials_path:
            credential = credentials.Certificate(Path(credentials_path))
            firebase_admin.initialize_app(
                credential,
                {"projectId": os.getenv("FIREBASE_PROJECT_ID")} if os.getenv("FIREBASE_PROJECT_ID") else None,
            )
        else:
            firebase_admin.initialize_app(options={"projectId": os.getenv("FIREBASE_PROJECT_ID")} if os.getenv("FIREBASE_PROJECT_ID") else None)
    return firestore.client()
