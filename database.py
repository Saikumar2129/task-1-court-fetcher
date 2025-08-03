import sqlite3
import json
from flask import g
from flask.cli import with_appcontext

DATABASE = 'queries.db'

def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called again.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Clear existing data and create new tables."""
    db = get_db()
    with open('schema.sql', 'r') as f:
        db.executescript(f.read())

def log_query(query_params, status, response_data, error_message=None):
    """Logs a query and its outcome to the database."""
    db = get_db()
    db.execute(
        'INSERT INTO query_log (query_params, status, response_data, error_message)'
        ' VALUES (?, ?, ?, ?)',
        (json.dumps(query_params), status, json.dumps(response_data), error_message)
    )
    db.commit()

def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
