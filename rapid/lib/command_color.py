"""Ask subprocesses to emit their own ANSI color when stdout is not a TTY.

Pytest, tox, uv, and ruff honor ``FORCE_COLOR``. Pytest also honors
``PY_COLORS``. ``CLICOLOR_FORCE`` covers tools that follow the BSD convention.

A non-empty ``NO_COLOR`` (https://no-color.org/) opts out of every addition.
An empty value is unset. Values already present are kept.

``TERM`` is set when it is missing or ``dumb`` so tools that key off ``TERM``
still colorize. That is safe on a process environment, which already includes
the host values. Container overrides cannot see the image or the registered
task definition, so they replace an explicit ``TERM=dumb`` and leave a missing
``TERM`` missing.
"""


_COLOR_VARIABLES = (
    ('FORCE_COLOR', '1'),
    ('PY_COLORS', '1'),
    ('CLICOLOR_FORCE', '1'),
)


def _bytes_key(key: str) -> bytes:
    return key.encode('ascii', 'ignore')


def _present(env, key: str) -> bool:
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


def _as_text(value) -> str:
    if isinstance(value, bytes):
        return value.decode('utf-8', 'replace')
    if isinstance(value, str):
        return value
    return '{}'.format(value)


def _color_disabled(env) -> bool:
    if not _present(env, 'NO_COLOR'):
        return False
    return _as_text(_get(env, 'NO_COLOR')) != ''


def _set_default(env, key: str, value: str) -> None:
    if _present(env, key):
        return
    env[key] = value


def _is_dumb(value) -> bool:
    return value in ('dumb', b'dumb')


def _replace_dumb_term(env) -> bool:
    """Replace TERM=dumb, keeping a bytes key when that is the form present."""
    replaced = False
    if 'TERM' in env and _is_dumb(env['TERM']):
        env['TERM'] = 'xterm-256color'
        replaced = True
    if b'TERM' in env and _is_dumb(env[b'TERM']):
        env[b'TERM'] = b'xterm-256color'
        replaced = True
    return replaced


def apply_command_colors(env: dict, fill_missing_term: bool = True) -> None:
    """Set color variables on a process environment mapping, in place.

    Keys may be ``str`` or ``bytes``. A non-empty ``NO_COLOR`` opts out. An
    explicit ``TERM=dumb`` is replaced. A missing ``TERM`` is set only when
    ``fill_missing_term`` is true.
    """
    if not isinstance(env, dict) or _color_disabled(env):
        return
    for key, value in _COLOR_VARIABLES:
        _set_default(env, key, value)
    if _replace_dumb_term(env):
        return
    if not _present(env, 'TERM') and fill_missing_term:
        env['TERM'] = 'xterm-256color'


def apply_container_command_colors(env: dict) -> None:
    """Set color variables on a container override, in place.

    An explicit ``TERM=dumb`` is replaced. A missing ``TERM`` stays missing,
    because the override replaces the image and the registered task definition
    for every key it carries.
    """
    apply_command_colors(env, fill_missing_term=False)


def command_color_entries(job_env=None) -> list:
    """Container env entries that enable color, unless the job opted out.

    ``TERM`` is included only when the job set it and the value changes, so a
    job that omitted ``TERM`` does not replace the image's value. A non-empty
    ``NO_COLOR`` yields no entries, and the opt-out has to be in ``job_env``.
    """
    job_env = job_env if isinstance(job_env, dict) else {}
    flat = {}
    for key, value in job_env.items():
        if isinstance(key, bytes):
            key = key.decode('ascii', 'ignore')
        flat[key] = _as_text(value)
    before = dict(flat)
    apply_container_command_colors(flat)

    entries = []
    for key, _value in _COLOR_VARIABLES:
        if key not in flat:
            continue
        if key not in before or before[key] != flat[key]:
            entries.append({'name': key, 'value': flat[key]})
    if 'TERM' in flat and ('TERM' not in before or before['TERM'] != flat['TERM']):
        entries.append({'name': 'TERM', 'value': flat['TERM']})
    return entries
