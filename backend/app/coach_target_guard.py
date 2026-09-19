from __future__ import annotations

from typing import Any


# Hedefli karşılaştırma kalıpları ayrı bir yeniden-yazım motoru kurmaz.
# Var olan coach_guard katmanının kişi-hedefli tespit ve kabuk temizleme
# listelerine yalnızca eksik kalan Türkçe karşılaştırma biçimlerini ekler.
_INSULT = (
    r'(?:'
    r'mal(?!\s+(?:sahibi|varlığ\w*|varligi\w*|miktar\w*|stok\w*|teslim\w*|al[ıi]m\w*|sat[ıi]m\w*|beyan\w*))'
    r'|aptal\w*|salak\w*|gerizek[aâ]l[ıi]\w*|ahmak\w*|beyinsiz\w*|embesil\w*'
    r'|dangalak\w*|cahil\w*|ezik\w*|çaps[ıi]z\w*|caps[ıi]z\w*|vas[ıi]fs[ıi]z\w*'
    r')'
)

_TARGETED_COMPARISON_PATTERNS = (
    rf'\b(?:senin|sizin)\s+gibi\s+(?:bir\s+)?{_INSULT}\b',
    rf'\b(?:senin|sizin)\s+kadar\s+(?:bir\s+)?{_INSULT}\b',
    rf'\b(?:hayat[ıi]mda|ömrümde|omrumde)\s+(?:senin|sizin)\s+(?:gibi|kadar)\s+(?:bir\s+)?{_INSULT}\b',
)

_TARGETED_SHELL_PATTERNS = (
    rf'\b(?:hayat[ıi]mda|ömrümde|omrumde)\s+(?:senin|sizin)\s+(?:gibi|kadar)\s+(?:bir\s+)?{_INSULT}'
    rf'(?:\s+(?:birini|birisini|birisi|biri))?'
    rf'(?:\s+(?:görmedim|görmedik|görmemiştim|görmediniz|görüyorum|görüyoruz))?\b[\s,;:.-]*',
    rf'\b(?:senin|sizin)\s+(?:gibi|kadar)\s+(?:bir\s+)?{_INSULT}'
    rf'(?:\s+(?:birini|birisini|birisi|biri))?'
    rf'(?:\s+(?:görmedim|görmedik|görmemiştim|görmediniz|görüyorum|görüyoruz))?'
    rf'(?:\s+(?:hayat[ıi]mda|ömrümde|omrumde))?\b[\s,;:.-]*',
    rf'\b(?:senin|sizin)\s+(?:gibi|kadar)\s+(?:bir\s+)?{_INSULT}'
    rf'(?:\s+(?:birini|birisini|birisi|biri))?\s+ilk\s+kez\s+(?:görüyorum|görüyoruz)\b[\s,;:.-]*',
)


def _extend_once(existing: tuple[str, ...], additions: tuple[str, ...]) -> tuple[str, ...]:
    missing = tuple(pattern for pattern in additions if pattern not in existing)
    return existing + missing


def install(engine_module: Any) -> None:
    """Eksik hedefli karşılaştırma desenlerini mevcut kalite kapısına ekler."""
    if getattr(engine_module, '_N_KOPRU_TARGET_GUARD_INSTALLED', False):
        return

    from . import coach_guard

    coach_guard._REALWORLD_PERSONAL_PATTERNS = _extend_once(
        coach_guard._REALWORLD_PERSONAL_PATTERNS,
        _TARGETED_COMPARISON_PATTERNS,
    )
    coach_guard._REALWORLD_SHELL_PATTERNS = _extend_once(
        coach_guard._REALWORLD_SHELL_PATTERNS,
        _TARGETED_SHELL_PATTERNS,
    )
    engine_module._N_KOPRU_TARGET_GUARD_INSTALLED = True
