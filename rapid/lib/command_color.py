"""Ask subprocesses to emit their own ANSI color when stdout is not a TTY.

Pytest, tox, uv, and ruff honor ``FORCE_COLOR``. Pytest also honors ``PY_COLORS``.
``CLICOLOR_FORCE`` covers tools that follow the BSD convention. ``TERM`` is set
when it is missing or ``dumb`` so tools that key off ``TERM`` still colorize.

``NO_COLOR`` (https://no-color.org/) opts out. Values the job already set are kept.
"""

_COLOR_VARIABLES = (
    ('FORCE_COLOR', '1'),
    ('PY_COLORS', '1'),
    ('CLICOLOR_FORCE', '1'),
)


def color_disabled(env) -> bool:
    return 'NO_COLOR' in env or b'NO_COLOR' in env


def apply_command_colors(env: dict) -> None:
    """Set color variables on a process environment mapping, in place."""
    if color_disabled(env):
        return
    for key, value in _COLOR_VARIABLES:
        env.setdefault(key, value)
    if env.get('TERM', '') in ('', 'dumb'):
        env['TERM'] = 'xterm-256color'


def command_color_entries(job_env=None) -> list:
    """Container env entries that enable color, unless the job opted out."""
    job_env = job_env if isinstance(job_env, dict) else {}
    if color_disabled(job_env):
        return []
    entries = [
        {'name': key, 'value': value}
        for key, value in _COLOR_VARIABLES
        if key not in job_env
    ]
    if job_env.get('TERM', '') in ('', 'dumb'):
        entries.append({'name': 'TERM', 'value': 'xterm-256color'})
    return entries
