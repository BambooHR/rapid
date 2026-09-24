"""Ask subprocesses to emit their own ANSI color when stdout is not a TTY.

Pytest, tox, uv, and ruff honor ``FORCE_COLOR``. ``CLICOLOR_FORCE`` covers tools
that follow the BSD convention. ``PY_COLORS`` is left unset: pytest checks it
before ``NO_COLOR``, so setting it would defeat an opt-out baked into a container
image or task definition that this process cannot see. ``FORCE_COLOR`` is checked
after ``NO_COLOR``, so an image-level opt-out still wins.

``TERM`` is upgraded from missing or ``dumb`` only when the job did not set it.
A ``dumb`` value on the host is the non-TTY default. A ``dumb`` value the job set
is an opt-out and is kept. Container overrides do not set ``TERM``, because a
Kubernetes job appends its own environment afterward and an image ``TERM`` is not
visible here.

``NO_COLOR`` (https://no-color.org/) opts out. Values the job already set are kept.
"""

import re


_COLOR_VARIABLES = (
    ('FORCE_COLOR', '1'),
    ('CLICOLOR_FORCE', '1'),
)

_ANSI_ESCAPE = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a log line."""
    return _ANSI_ESCAPE.sub('', text)


def color_disabled(env) -> bool:
    if not isinstance(env, dict):
        return False
    return 'NO_COLOR' in env or b'NO_COLOR' in env


def _bytes_key(key: str) -> bytes:
    return key.encode('ascii', 'ignore')


def _has(env, key: str) -> bool:
    if not isinstance(env, dict):
        return False
    return key in env or _bytes_key(key) in env


def _get(env, key: str):
    if not isinstance(env, dict):
        return None
    if key in env:
        return env[key]
    bkey = _bytes_key(key)
    if bkey in env:
        return env[bkey]
    return None


def _set_default(env, key: str, value: str) -> None:
    if _has(env, key):
        return
    env[key] = value


def _set_term(env, value: str) -> None:
    """Write TERM, keeping a bytes key when that is the only form present."""
    if 'TERM' in env or b'TERM' not in env:
        env['TERM'] = value
    else:
        env[b'TERM'] = value.encode('ascii')


def apply_command_colors(env: dict, job_env=None) -> None:
    """Set color variables on a process environment mapping, in place.

    ``job_env`` is the environment the job configured, before host variables were
    merged. Keys may be ``str`` or ``bytes``. A value the job set is not replaced,
    including ``TERM=dumb``.
    """
    if color_disabled(env) or color_disabled(job_env):
        return
    for key, value in _COLOR_VARIABLES:
        if _has(job_env, key):
            continue
        _set_default(env, key, value)
    if _has(job_env, 'TERM'):
        return
    term = _get(env, 'TERM')
    if term in (None, '', 'dumb', b'', b'dumb'):
        _set_term(env, 'xterm-256color')


def command_color_entries(job_env=None) -> list:
    """Container env entries that enable color, unless the job opted out.

    ``TERM`` is not included. The job environment is applied separately and must
    keep a ``TERM`` it set, and an image-level ``TERM`` cannot be read from here.
    """
    job_env = job_env if isinstance(job_env, dict) else {}
    if color_disabled(job_env):
        return []
    return [
        {'name': key, 'value': value}
        for key, value in _COLOR_VARIABLES
        if not _has(job_env, key)
    ]
