"""N-KÖPRÜ backend package bootstrap.

Yanıt Koçu için son kalite ve içerik-koruma kapıları burada kurulur; böylece
mevcut API ve test importları değişmeden güvenli post-denetim devreye girer.
"""

from . import coach_engine as _coach_engine
from .coach_guard import install as _install_coach_guard
from .coach_target_guard import install as _install_target_guard
from .coach_invariant_guard import install as _install_invariant_guard

_install_coach_guard(_coach_engine)
_install_target_guard(_coach_engine)
_install_invariant_guard(_coach_engine)

del _install_coach_guard
del _install_target_guard
del _install_invariant_guard
