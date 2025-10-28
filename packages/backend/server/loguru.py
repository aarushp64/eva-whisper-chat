"""
Minimal fallback logger to satisfy `from loguru import logger` imports
when the real `loguru` package is not installed in the environment.

This is intentionally tiny and only exposes the methods used in the
project (info, error, warning, debug). When the real `loguru` package
is installed, Python will import that instead of this stub (depending
on sys.path). Having this file makes the code importable in minimal
environments for tests and static checks.
"""
import logging

_std = logging.getLogger('eva_stub')
_std.setLevel(logging.INFO)
if not _std.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    _std.addHandler(ch)


class _LoggerProxy:
    def info(self, *args, **kwargs):
        _std.info(' '.join(map(str, args)))

    def error(self, *args, **kwargs):
        _std.error(' '.join(map(str, args)))

    def warning(self, *args, **kwargs):
        _std.warning(' '.join(map(str, args)))

    def debug(self, *args, **kwargs):
        _std.debug(' '.join(map(str, args)))


logger = _LoggerProxy()
