"""PostgreSQL application database. One pooled connection per request."""
import hashlib
import logging
import re
from contextlib import contextmanager

from flask import g, has_request_context
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.pool import NullPool

from config import Config

logger = logging.getLogger(__name__)

# Tests still assign a unique path here. Each path becomes its own Postgres schema
# so cases do not share rows. The default uses the public schema.
DB_NAME = "finance.db"

_engine: Engine | None = None
_SAFE_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class DatabaseError(Exception):
    """The application database rejected or could not finish a statement."""


class IntegrityConflict(DatabaseError):
    """A unique or foreign-key constraint failed."""


class _Row(dict):
    """Mapping row so existing ``row['column']`` and ``dict(row)`` calls keep working."""


class _Result:
    def __init__(self, rows, lastrowid=None):
        self._rows = rows
        self.lastrowid = lastrowid

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def __iter__(self):
        return iter(self._rows)


class AppConnection:
    """Small wrapper around one pooled SQLAlchemy connection."""

    def __init__(self, sa_conn):
        self._conn = sa_conn
        self._tx = sa_conn.begin()

    def execute(self, sql, params=()):
        if isinstance(params, dict):
            bind = params
            statement = text(sql)
        else:
            if params is None:
                params = ()
            elif not isinstance(params, (list, tuple)):
                params = (params,)
            statement, bind = _qmarks(sql, params)
        try:
            result = self._conn.execute(statement, bind)
        except IntegrityError as exc:
            raise IntegrityConflict(str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            raise DatabaseError(str(exc.orig or exc)) from exc
        rows = []
        lastrowid = None
        if result.returns_rows:
            keys = list(result.keys())
            for record in result:
                row = _Row(zip(keys, record))
                rows.append(row)
            if rows and str(sql).lstrip().upper().startswith("INSERT") and "id" in rows[0]:
                lastrowid = rows[0]["id"]
        return _Result(rows, lastrowid)

    def commit(self):
        self._tx.commit()
        self._tx = self._conn.begin()

    def rollback(self):
        if self._tx.is_active:
            self._tx.rollback()
        self._tx = self._conn.begin()

    def close(self):
        try:
            if self._tx.is_active:
                self._tx.rollback()
        finally:
            self._conn.close()


def schema_name() -> str:
    if DB_NAME in ("finance.db", "public"):
        return "public"
    digest = hashlib.sha1(str(DB_NAME).encode()).hexdigest()[:16]
    return f"t_{digest}"


def _qmarks(sql: str, params: tuple | list):
    parts = sql.split("?")
    if len(parts) - 1 != len(params):
        raise DatabaseError("SQL placeholder count does not match the parameters")
    bind = {}
    out = parts[0]
    for index, part in enumerate(parts[1:]):
        key = f"p{index}"
        out += f":{key}" + part
        bind[key] = params[index]
    return text(out), bind


def _ident(name: str) -> str:
    if not _SAFE_IDENT.match(name):
        raise ValueError(f"Unsafe database identifier: {name}")
    return name


def ensure_database(url: str) -> None:
    """Create the application database when this server does not have it yet."""
    from sqlalchemy.engine.url import make_url

    parsed = make_url(url)
    name = parsed.database
    if not name:
        raise ValueError("APP_DATABASE_URL is missing a database name")
    _ident(name)
    maintenance = create_engine(
        parsed.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    try:
        with maintenance.connect() as conn:
            found = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": name},
            ).scalar()
            if not found:
                conn.execute(text(f'CREATE DATABASE "{name}"'))
                logger.info("Created PostgreSQL database %s", name)
    finally:
        maintenance.dispose()


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = Config.APP_DATABASE_URL or ""
        if not url:
            raise EnvironmentError("APP_DATABASE_URL is required")
        ensure_database(url)
        engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=10,
            future=True,
        )

        @event_checkout(engine)
        def _set_search_path(dbapi_conn, _record, _proxy):
            schema = _ident(schema_name())
            cursor = dbapi_conn.cursor()
            cursor.execute(f"SET search_path TO {schema}")
            cursor.close()

        _engine = engine
    return _engine


def event_checkout(engine: Engine):
    from sqlalchemy import event

    def decorate(fn):
        event.listens_for(engine, "checkout")(fn)
        return fn

    return decorate


def ensure_schema() -> None:
    schema = _ident(schema_name())
    if schema == "public":
        return
    with get_engine().connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()


def open_connection() -> AppConnection:
    ensure_schema()
    return AppConnection(get_engine().connect())


def get_connection() -> AppConnection:
    """Short-lived connection for startup and tests. Request handlers use connection()."""
    return open_connection()


@contextmanager
def connection():
    """
    One connection for the whole request, returned to the pool in teardown.
    Outside a request, open a connection and close it when the block ends.
    """
    if has_request_context():
        conn = getattr(g, "db_conn", None)
        if conn is None:
            conn = open_connection()
            g.db_conn = conn
        try:
            yield conn
        except DatabaseError:
            conn.rollback()
            raise
        return

    conn = open_connection()
    try:
        yield conn
    except DatabaseError:
        conn.rollback()
        raise
    finally:
        conn.close()


def close_request_connection(exc=None):
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()


def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
