import os
import libsql_client
from flask import g


def get_db():
    """Get a libsql_client sync connection for the current request."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = libsql_client.create_client_sync(
            url=os.environ['TURSO_DATABASE_URL'],
            auth_token=os.environ['TURSO_AUTH_TOKEN']
        )
    return db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass
        g._database = None


def init_db():
    """Create the contacts table if it doesn't exist."""
    client = libsql_client.create_client_sync(
        url=os.environ['TURSO_DATABASE_URL'],
        auth_token=os.environ['TURSO_AUTH_TOKEN']
    )
    client.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            owner_name TEXT NOT NULL,
            label TEXT,
            name1 TEXT NOT NULL,
            phone1 TEXT NOT NULL,
            name2 TEXT,
            phone2 TEXT,
            name3 TEXT,
            phone3 TEXT,
            pin_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    client.close()