import sys
from types import SimpleNamespace

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

# Provide minimal stubs for the discord module so tests can run without the
# real dependency.
def _noop_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

class Cog:
    @staticmethod
    def listener(*args, **kwargs):
        return _noop_decorator

def hybrid_group(*args, **kwargs):
    def decorator(func):
        func.command = _noop_decorator
        return func
    return decorator

class Context:
    pass

class CommandError(Exception):
    pass

class MissingRequiredArgument(CommandError):
    def __init__(self, param=None):
        self.param = param

commands_stub = SimpleNamespace(
    Cog=Cog,
    listener=_noop_decorator,
    hybrid_group=hybrid_group,
    command=_noop_decorator,
    check=_noop_decorator,
    Context=Context,
    CommandError=CommandError,
    MissingRequiredArgument=MissingRequiredArgument,
)
color_stub = SimpleNamespace(random=lambda: None, blue=lambda: None)
sys.modules['discord'] = SimpleNamespace(Role=object, Color=color_stub, Embed=object)
sys.modules['discord.ext'] = SimpleNamespace(commands=commands_stub)
sys.modules['discord.ext.commands'] = commands_stub
sys.modules['psycopg'] = MagicMock()
sys.modules['dotenv'] = SimpleNamespace(load_dotenv=lambda: None)

from src.cogs.fakeperms import FakePerms


@pytest.fixture
def bot():
    return MagicMock()


@pytest.fixture
def fakeperms(bot):
    return FakePerms(bot)


def test_load_permission_flags(fakeperms):
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError
        fakeperms.permission_file = "non_existent_file.json"
        flags = fakeperms.load_permission_flags()
        assert flags == {}


def normalize_whitespace(sql):
    return " ".join(sql.split())


def test_setup_database(fakeperms):
    with patch("psycopg.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value

        print("Calling _setup_database()")
        fakeperms._setup_database()
        print("Called _setup_database()")

        print("mock_connect.call_args_list:", mock_connect.call_args_list)
        print("mock_conn.cursor.call_args_list:", mock_conn.cursor.call_args_list)
        print(
            "mock_cursor.execute.call_args_list:", mock_cursor.execute.call_args_list
        )  # Debug print to show the calls to execute
        assert mock_cursor.execute.called
        args, _ = mock_cursor.execute.call_args
        assert normalize_whitespace(args[0]) == normalize_whitespace(
            """
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id BIGINT PRIMARY KEY,
                permissions INTEGER NOT NULL
            )
        """
        )


def test_get_role_permissions(fakeperms):
    with patch("psycopg.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = [8]

        print("Calling get_role_permissions(123456)")
        perms = fakeperms.get_role_permissions(123456)
        print("Returned from get_role_permissions(123456) with perms:", perms)
        assert perms == 8

        mock_cursor.fetchone.return_value = None
        print("Calling get_role_permissions(123456) again")
        perms = fakeperms.get_role_permissions(234567)
        print("Returned from get_role_permissions(123456) again with perms:", perms)
        assert perms == 0


def test_set_role_permissions(fakeperms):
    with patch("psycopg.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value

        print("Calling set_role_permissions(123456, 8)")
        fakeperms.set_role_permissions(123456, 8)
        print("Called set_role_permissions(123456, 8)")

        print("mock_connect.call_args_list:", mock_connect.call_args_list)
        print("mock_conn.cursor.call_args_list:", mock_conn.cursor.call_args_list)
        print(
            "mock_cursor.execute.call_args_list:", mock_cursor.execute.call_args_list
        )  # Debug print to show the calls to execute
        assert mock_cursor.execute.called
        args, _ = mock_cursor.execute.call_args
        assert normalize_whitespace(args[0]) == normalize_whitespace(
            """
            INSERT INTO role_permissions (role_id, permissions) VALUES (%s, %s)
            ON CONFLICT (role_id) DO UPDATE SET permissions = EXCLUDED.permissions
        """
        )
        assert args[1] == (123456, 8)


@pytest.mark.asyncio
async def test_fp_grant_permission(fakeperms):
    mock_ctx = AsyncMock()
    mock_role = MagicMock()
    mock_role.id = 123456
    mock_role.mention = "@role"
    mock_ctx.send = AsyncMock()

    fakeperms.permission_flags = {"ADMIN": 0x8}
    fakeperms.get_role_permissions = MagicMock(return_value=0)
    fakeperms.set_role_permissions = MagicMock()

    await fakeperms.fp_grant_permission.callback(
        fakeperms, mock_ctx, mock_role, "admin"
    )
    fakeperms.set_role_permissions.assert_called_with(123456, 0x8)
    mock_ctx.send.assert_called()


@pytest.mark.asyncio
async def test_fp_revoke_permission(fakeperms):
    mock_ctx = AsyncMock()
    mock_role = MagicMock()
    mock_role.id = 123456
    mock_role.mention = "@role"
    mock_ctx.send = AsyncMock()

    fakeperms.permission_flags = {"ADMIN": 0x8}
    fakeperms.get_role_permissions = MagicMock(return_value=0x8)
    fakeperms.set_role_permissions = MagicMock()

    await fakeperms.fp_revoke_permission.callback(
        fakeperms, mock_ctx, role=mock_role, perm_name="admin"
    )
    fakeperms.set_role_permissions.assert_called_with(123456, 0)
    mock_ctx.send.assert_called()


@pytest.mark.asyncio
async def test_fp_list_permissions(fakeperms):
    mock_ctx = AsyncMock()
    mock_role = MagicMock()
    mock_role.id = 123456
    mock_role.name = "Test Role"
    mock_ctx.send = AsyncMock()

    fakeperms.permission_flags = {"ADMIN": 0x8}
    fakeperms.get_role_permissions = MagicMock(return_value=0x8)

    await fakeperms.fp_list_permissions.callback(fakeperms, mock_ctx, mock_role)
    mock_ctx.send.assert_called()
