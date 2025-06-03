from unittest.mock import MagicMock, patch
import sys

sys.modules['psycopg'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

import pytest

from src.utils.economy import EconomyUtils


def normalize_whitespace(sql: str) -> str:
    return " ".join(sql.split())


def test_update_wallet():
    with patch("src.utils.economy.psycopg.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = [10]
        mock_connect.return_value = mock_conn

        EconomyUtils.update_wallet(user_id=1, amount=5)

        # Verify the SELECT and UPDATE queries were executed
        select_call = mock_cursor.execute.call_args_list[0]
        assert normalize_whitespace(select_call.args[0]) == normalize_whitespace(
            "SELECT wallet FROM bank WHERE user_id = %s"
        )

        update_call = mock_cursor.execute.call_args_list[1]
        assert normalize_whitespace(update_call.args[0]) == normalize_whitespace(
            "UPDATE bank SET wallet = %s WHERE user_id = %s"
        )
        assert update_call.args[1] == (15, 1)

        mock_cursor.close.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
