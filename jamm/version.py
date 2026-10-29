"""Package version source of truth.

Prefers the installed distribution version via importlib.metadata so runtime reflects
the published package. For a source/editable checkout that has not been installed, the
fallback reads ``[project].version`` straight out of pyproject.toml rather than
hardcoding a literal -- a hardcoded copy silently drifted two releases behind, and the
version is reported to the backend on every request via ``Jamm-SDK-Version``.
"""

import os
import re
from importlib.metadata import version as _pkg_version, PackageNotFoundError

_UNKNOWN = "0.0.0"


# Returned by _load_toml when a parser ran and rejected the file, as distinct from None
# ("no parser installed"). The two must not collapse: falling back to the regex after a
# parser has already declared the file malformed would report a version scraped out of a
# file TOML says is invalid.
_PARSE_FAILED = object()


def _load_toml(raw: bytes):
    """Parse TOML, returning the table, ``_PARSE_FAILED``, or None if no parser exists.

    tomllib is 3.11+; this package supports 3.9. tomli is the same parser backported,
    but it is not a runtime dependency -- this path only runs for an uninstalled source
    checkout, so the regex below is the fallback rather than a required install.
    """
    try:
        import tomllib
    except ModuleNotFoundError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ModuleNotFoundError:
            return None

    try:
        return tomllib.loads(raw.decode("utf-8"))
    except Exception:
        return _PARSE_FAILED


def _version_from_pyproject() -> str:
    """Read [project].version from the pyproject.toml next to this package."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pyproject.toml")

    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return _UNKNOWN

    parsed = _load_toml(raw)
    if parsed is _PARSE_FAILED:
        return _UNKNOWN
    if parsed is not None:
        version = parsed.get("project", {}).get("version")
        return version if isinstance(version, str) and version else _UNKNOWN

    # No TOML parser available (3.9/3.10 without tomli). Scan for the [project] table
    # and read its version key. Tolerates whitespace inside the table header, a trailing
    # comment after it, and whitespace around the `=`; only [project] counts, since
    # [tool.*] tables carry their own version keys.
    source = raw.decode("utf-8", errors="replace")
    in_project = False
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            # Trim before matching so a trailing comment is tolerated, and match the
            # inner padding as [ \t]* -- TOML allows tabs there too, and stripping only
            # spaces would miss "[\tproject\t]".
            header = stripped.split("#", 1)[0].strip()
            in_project = re.fullmatch(r"\[[ \t]*project[ \t]*\]", header) is not None
            continue
        if not in_project:
            continue
        found = re.match(r'version\s*=\s*["\']([^"\']+)["\']', stripped)
        if found:
            return found.group(1)

    return _UNKNOWN


try:
    VERSION = _pkg_version("jamm")
except PackageNotFoundError:
    VERSION = _version_from_pyproject()

__all__ = ["VERSION"]
