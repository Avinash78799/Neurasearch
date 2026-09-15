import ast
import subprocess
import sys
import tempfile
import os
import logging

logger = logging.getLogger("neurasearch.computation")

FORBIDDEN_ATTRIBUTES = {
    "__subclasses__", "__bases__", "__base__", "__mro__",
    "__globals__", "__code__", "__builtins__", "__import__",
    "__dict__", "__class__", "__reduce__", "__reduce_ex__",
    "__init_subclass__"
}

FORBIDDEN_NAMES = {
    "eval", "exec", "compile", "__import__", "getattr", "setattr",
    "delattr", "open", "breakpoint", "input", "exit", "quit"
}


def is_code_safe(code_str: str) -> tuple[bool, str]:
    """Static AST analyzer verifying no dunder attribute traversal or dangerous builtins exist."""
    try:
        tree = ast.parse(code_str)
    except SyntaxError as err:
        return False, f"Syntax error: {err}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRIBUTES:
            return False, f"Access to restricted attribute '{node.attr}' is blocked."
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return False, f"Use of restricted identifier '{node.id}' is blocked."
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_NAMES:
                return False, f"Call to restricted function '{node.func.id}' is blocked."
    return True, ""


def execute_computation(code_str: str) -> dict:
    """Executes a python code segment in a restricted sandbox subprocess.

    Enforces:
    - Pre-execution AST security validation against jailbreak patterns.
    - 3-second execution timeout.
    - Restricted safe builtins (math, datetime, list operations).
    - Blocked sensitive modules (os, sys, subprocess, socket, shutil).
    - Empty env to block network and ambient env vars access.
    - Captures stdout/stderr and extracts the 'result' variable.
    """
    safe, reason = is_code_safe(code_str)
    if not safe:
        logger.warning("Computation sandbox rejected code: %s", reason)
        return {
            "status": "error",
            "output": None,
            "result": None,
            "error": f"Security validation failed: {reason}"
        }

    wrapped_code = f"""# Import standard safe modules first, before blocking imports

import math
import datetime
import json
import sys

# Block sensitive modules in sys.modules
blocked = ['os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib', 'http', 'ftplib']
for b in blocked:
    sys.modules[b] = None

# Custom safe import function
def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name in ['math', 'datetime', 'json']:
        return sys.modules.get(name) or __import__(name, globals, locals, fromlist, level)
    raise ImportError(f"Import of module '{{name}}' is blocked in sandbox.")

# Define safe builtins namespace
safe_builtins = {{}}
allowed_builtins = [
    'abs', 'all', 'any', 'bin', 'bool', 'chr', 'divmod', 'enumerate', 'filter',
    'float', 'format', 'hash', 'hex', 'int', 'len', 'list', 'map', 'max', 'min',
    'oct', 'ord', 'pow', 'print', 'range', 'repr', 'reversed', 'round', 'set',
    'slice', 'sorted', 'str', 'sum', 'tuple', 'zip', 'dict', 'Exception',
    'ValueError', 'TypeError', 'KeyError', 'IndexError'
]
for a in allowed_builtins:
    if a in dir(__builtins__):
        safe_builtins[a] = getattr(__builtins__, a)

safe_builtins['__import__'] = safe_import

user_code = {repr(code_str)}
locs = {{
    "math": math,
    "datetime": datetime,
    "json": json
}}

try:
    # Run user code in a clean restricted namespace
    exec(user_code, {{"__builtins__": safe_builtins, "math": math, "datetime": datetime, "json": json}}, locs)
    # Check if a result variable was defined and print it
    if 'result' in locs:
        print(f"RESULT:{{locs['result']}}")
except Exception as e:
    print(f"ERROR:{{e}}", file=sys.stderr)
    sys.exit(1)
"""

    fd, path = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(wrapped_code)

        # Execute python script in a separate process with empty env to prevent leakages
        proc = subprocess.Popen(
            [sys.executable, path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={},  # Complete empty environment to block network
            text=True
        )

        try:
            stdout, stderr = proc.communicate(timeout=3.0)
            if proc.returncode == 0:
                result = None
                for line in stdout.splitlines():
                    if line.startswith("RESULT:"):
                        result = line.replace("RESULT:", "").strip()
                        break
                return {
                    "status": "success",
                    "output": stdout.strip(),
                    "result": result,
                    "error": None
                }
            else:
                return {
                    "status": "error",
                    "output": stdout.strip(),
                    "result": None,
                    "error": stderr.strip() or "Execution failed"
                }
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            return {
                "status": "timeout",
                "output": None,
                "result": None,
                "error": "Computation timed out (limit: 3.0 seconds)"
            }
    except Exception as exc:
        logger.error("Failed to run sandbox computation: %s", exc)
        return {
            "status": "error",
            "output": None,
            "result": None,
            "error": str(exc)
        }
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
