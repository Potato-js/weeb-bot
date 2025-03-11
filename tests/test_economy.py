import psycopg

# import pytest
from src.utils.economy import EconomyUtils


class FakeCursor:
    def __init__(self, fetchone_result=None):
        self.commands = []
        self.closed = False
        self.fetchone_result = fetchone_result

    def execute(self, sql, params=None):
        self.commands.append((sql, params))

    def fetchone(self):
        return self.fetchone_result

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, fetchone_result=None):
        self.cursor_called = False
        self.committed = False
        self.closed = False
        self.cursor_obj = FakeCursor(fetchone_result=fetchone_result)

    def cursor(self):
        self.cursor_called = True
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def test_setup_database(monkeypatch):
    connections = []

    def fake_connect(**kwargs):
        conn = FakeConnection()
        connections.append(conn)
        return conn

    monkeypatch.setattr(psycopg, "connect", fake_connect)
    EconomyUtils.setup_database()

    # Validate a connection was created.
    assert len(connections) == 1, "A connection should have been created."
    conn = connections[0]

    # Verify that the connection's cursor was called, commit and close were called.
    assert conn.cursor_called, "Expected cursor() to be called on connection."
    assert conn.committed, "Expected commit() to be called on connection."
    assert conn.closed, "Expected close() to be called on connection."

    # Verify that the CREATE TABLE command was executed.
    expected_sql = "CREATE TABLE IF NOT EXISTS bank(user_id BIGINT PRIMARY KEY, wallet BIGINT, bank BIGINT, maxbank BIGINT)"
    cursor_commands = conn.cursor_obj.commands
    assert any(
        expected_sql in sql for sql, _ in cursor_commands
    ), "Expected SQL command not executed."
    # Verify the cursor was closed.
    assert conn.cursor_obj.closed, "Expected cursor to be closed."


def test_create_wallet(monkeypatch):
    connections = []

    def fake_connect(**kwargs):
        conn = FakeConnection()
        connections.append(conn)
        return conn

    monkeypatch.setattr(psycopg, "connect", fake_connect)
    test_user_id = 12345
    EconomyUtils.create_wallet(test_user_id)

    assert len(connections) == 1, "A connection should have been created."
    conn = connections[0]
    assert conn.cursor_called, "Expected cursor() to be called on connection."
    assert conn.committed, "Expected commit() to be called on connection."
    assert conn.closed, "Expected close() to be called on connection."
    expected_sql = "INSERT INTO bank VALUES(%s, %s, %s, %s)"
    cursor_commands = conn.cursor_obj.commands
    assert any(
        expected_sql in sql and params == (test_user_id, 0, 100, 25000)
        for sql, params in cursor_commands
    ), "Expected INSERT command not executed."
    assert conn.cursor_obj.closed, "Expected cursor to be closed."


def test_get_balance_new_user(monkeypatch):
    connections = []

    # Simulate that no record exists by returning None in fetchone.
    def fake_connect(**kwargs):
        conn = FakeConnection(fetchone_result=None)
        connections.append(conn)
        return conn

    monkeypatch.setattr(psycopg, "connect", fake_connect)
    test_user_id = 54321
    balance = EconomyUtils.get_balance(test_user_id)

    # When no record exists, create_wallet is called and default values are returned.
    assert balance == (0, 100, 25000)
    # Two connections expected: one for initial SELECT and one for create_wallet.
    assert len(connections) == 2


def test_get_balance_existing_user(monkeypatch):
    connections = []

    # Simulate an existing record with wallet=50, bank=150, maxbank=25000.
    def fake_connect(**kwargs):
        conn = FakeConnection(fetchone_result=(50, 150, 25000))
        connections.append(conn)
        return conn

    monkeypatch.setattr(psycopg, "connect", fake_connect)
    test_user_id = 98765
    balance = EconomyUtils.get_balance(test_user_id)

    assert balance == (50, 150, 25000)
    # Only one connection expected.
    assert len(connections) == 1


def test_update_wallet_existing_user(monkeypatch):
    connections = []

    # Simulate that the wallet exists with a current value of 200.
    class FakeConnectionUpdate(FakeConnection):
        def __init__(self):
            self.cursor_called = False
            self.committed = False
            self.closed = False
            self.cursor_obj = FakeCursor(fetchone_result=(200,))

    def fake_connect(**kwargs):
        conn = FakeConnectionUpdate()
        connections.append(conn)
        return conn

    monkeypatch.setattr(psycopg, "connect", fake_connect)
    test_user_id = 11111
    amount_to_add = 50
    EconomyUtils.update_wallet(test_user_id, amount_to_add)

    cursor_cmds = connections[0].cursor_obj.commands
    select_found = any(
        "SELECT wallet FROM bank WHERE user_id = %s" in sql for sql, _ in cursor_cmds
    )
    update_found = any(
        "UPDATE bank SET wallet = %s, WHERE user_id = %s" in sql
        for sql, _ in cursor_cmds
    )
    assert select_found, "SELECT command not executed in update_wallet."
    assert update_found, "UPDATE command not executed in update_wallet."
    assert connections[0].committed, "Expected commit() to be called on connection."
    assert connections[0].closed, "Expected close() to be called on connection."


def test_update_wallet_no_existing_user(monkeypatch):
    connections = []

    # Simulate that no wallet exists by returning None in fetchone.
    def fake_connect(**kwargs):
        conn = FakeConnection(fetchone_result=None)
        connections.append(conn)
        return conn

    monkeypatch.setattr(psycopg, "connect", fake_connect)
    test_user_id = 22222
    amount_to_add = 100
    result = EconomyUtils.update_wallet(test_user_id, amount_to_add)

    # When no wallet exists, update_wallet calls create_wallet and returns 0.
    assert result == 0
    # Two connections expected: one for SELECT and one for create_wallet.
    assert len(connections) == 2
