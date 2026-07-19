"""Module alias for the packaged backup archive implementation.

This compatibility path must resolve to the implementation module itself—not
copy its symbols—because operational tests and downstream callers patch safety
limits and filesystem primitives on the legacy module path.
"""

import sys

from ombrebrain.storage import backup_archive as _implementation

sys.modules[__name__] = _implementation
