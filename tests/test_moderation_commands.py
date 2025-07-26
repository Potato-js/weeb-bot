import ast
import os
import pytest

from .command_utils import get_function_def

FILEPATH = "src/cogs/moderation.py"
COMMANDS = [
    ("moderator_kick", "kick"),
    ("moderator_ban", "ban"),
    ("moderator_unban", "unban"),
    ("moderator_mute_or_timeout", "mute"),
    ("moderator_unmute_or_untimeout", "unmute"),
]

@pytest.mark.parametrize("func_name,command_name", COMMANDS)
def test_moderation_command_decorators(func_name: str, command_name: str):
    assert os.path.exists(FILEPATH), f"{FILEPATH} does not exist"
    with open(FILEPATH, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=FILEPATH)

    func = get_function_def(tree, func_name)
    assert func is not None, f"Function {func_name} not found in {FILEPATH}"

    found = False
    for dec in func.decorator_list:
        if isinstance(dec, ast.Call) and hasattr(dec.func, "attr"):
            if dec.func.attr in {"hybrid_command", "hybrid_group", "command"}:
                for kw in dec.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        if kw.value.value == command_name:
                            found = True
                            break
    assert found, f"{func_name} missing decorator name '{command_name}'"
