from __future__ import annotations

import re
from typing import Any


_ATTACK_SIGNALS = {'hakaret/küfür', 'kişiye yönelik saldırı', 'tehdit/şiddet'}
_SUBSTANTIVE_SIGNALS = {
    'soru',
    'sayısal/doğrulanabilir iddia',
    'kaynak/kanıt vurgusu',
    'koşullu/dengeli görüş',
    'görüş ayrılığı/itiraz',
    'destek/olumlu görüş',
    'konuya katkı eleştirisi',
    'bağlamı yeniden değerlendirme talebi',
}
_CONSTRUCTIVE_MARKERS = (
    'görüş', 'düşün', 'fikir', 'gerekçe', 'dayanak', 'kanıt', 'kaynak',
    'konu', 'tartış', 'açıkla', 'paylaş', 'katılmıyorum', 'katılıyorum',
    'değerlendir', 'soru', 'bilgi', 'veri', 'iddia', 'yaklaşım',
)


def _is_attack(signals: list[str]) -> bool:
    return bool(_ATTACK_SIGNALS.intersection(signals))


def _is_pure_attack(engine_module: Any, original: str, signals: list[str]) -> bool:
    if not _is_attack(signals):
        return False
    if _SUBSTANTIVE_SIGNALS.intersection(signals):
        return False
    try:
        if engine_module._ban_stance(original) != 'none':
            return False
    except Exception:
        pass
    return True


def _quality_issue(engine_module: Any, original: str, suggestion: str, signals: list[str]) -> str:
    text = (suggestion or '').strip()
    if not text:
        return 'boş çıktı'

    try:
        if engine_module._has_attack_residue(text):
            return 'saldırı kalıntısı'
    except Exception:
        pass

    low = engine_module._normalize(text) if hasattr(engine_module, '_normalize') else text.lower()

    # Saldırı kabuğu sökülürken geride kalan öznesiz/kırık cümleleri engeller.
    if re.search(r'^(?:birisin|birisiniz|birisi|biri|senden|sizden|senin|sizin|sana|seni)\b', low):
        return 'kırık başlangıç'
    if re.search(r'\b(?:birisin|birisiniz)\b', low):
        return 'kişisel hitap kalıntısı'
    if re.search(r'\b(?:senden|sizden)\s+daha\s+(?:iyi|kötü|zeki|akıllı|başarılı|mantıklı)\b', low):
        return 'kişisel karşılaştırma kalıntısı'
    if _is_attack(signals) and re.search(r'\b(?:senden|sizden|senin|sizin)\b', low):
        return 'ikinci kişi kalıntısı'

    # Salt saldırıda çıkan metin tartışılabilir bir görüş/gerekçe eksenine dönmeli.
    if _is_pure_attack(engine_module, original, signals):
        if not any(marker in low for marker in _CONSTRUCTIVE_MARKERS):
            return 'salt saldırıdan anlamsız iskelet kaldı'

    # Aşırı kısa ve bağlamsız artıklar kullanıcıya gösterilmez.
    words = re.findall(r'\b\w+\b', text, flags=re.UNICODE)
    if _is_attack(signals) and len(words) < 4 and not text.endswith('?'):
        return 'çok kısa saldırı artığı'

    try:
        valid, reason = engine_module._candidate_valid(original, text, signals)
        if not valid:
            return reason
    except Exception:
        pass

    return ''


def _safe_generic(original: str) -> str:
    low = original.lower()
    if any(x in low for x in ('fikir', 'düşünce', 'görüş', 'yorum')):
        return (
            'Bu görüşü yeterince ikna edici bulmuyorum. '
            'Eleştirimi kişiye değil, ileri sürülen düşüncenin gerekçelerine odaklamak istiyorum.'
        )
    return (
        'Bu görüşe katılmıyorum. '
        'Eleştirimi kişiye değil, ileri sürülen görüşün gerekçelerine odaklamak istiyorum.'
    )


def _fallback(engine_module: Any, original: str, context: str, signals: list[str]) -> str:
    # Önce mevcut güvenli motorun alan-özel yeniden yazımını tekrar dene.
    try:
        deterministic, _, _ = engine_module._deterministic_rewrite(original, context, signals)
        if not _quality_issue(engine_module, original, deterministic, signals):
            return deterministic
    except Exception:
        pass

    # Soru varsa saldırı kabuğunu atıp gerçek soruyu korumaya çalış.
    if 'soru' in signals:
        try:
            clean = engine_module._strip_attack_shell(original)
            clean = re.sub(r'^\s*(?:m[ıi]s[ıi]n|misin|musun|müsün)\b[ ,;:-]*', '', clean, flags=re.IGNORECASE)
            if len(clean.split()) >= 3 and not engine_module._has_attack_residue(clean):
                candidate = engine_module._question_sentence(clean)
                if not _quality_issue(engine_module, original, candidate, signals):
                    return candidate
        except Exception:
            pass

    # Sayısal iddia varsa sayı ve kanıt isteme eksenini koru.
    if 'sayısal/doğrulanabilir iddia' in signals:
        try:
            candidate = engine_module._numeric_claim_rewrite(original)
            if not _quality_issue(engine_module, original, candidate, signals):
                return candidate
        except Exception:
            pass

    # Kaynak talebini kaybetme.
    if 'kaynak/kanıt vurgusu' in signals:
        return 'Bu iddianın dayanağını değerlendirebilmek için kullandığın kaynak veya kanıtı paylaşabilir misin?'

    return _safe_generic(original)


def _ai_repair(engine_module: Any, original: str, bad_candidate: str, context: str, signals: list[str]) -> str:
    """Yalnız şüpheli çıktıda, zaten bellekte yüklü yerel modeli ikinci hakem olarak dener.

    Model yüklenmez/indirilemez; hazır değilse anında deterministik yedeğe dönülür.
    """
    try:
        status = engine_module.status(load=False)
        if not status.get('loaded'):
            return ''
        model = getattr(engine_module, '_MODEL', None)
        tokenizer = getattr(engine_module, '_TOKENIZER', None)
        if model is None or tokenizer is None:
            return ''

        import torch

        system_prompt = (
            "Sen N-KÖPRÜ Yanıt Koçu için son kalite hakemisin. Sana özgün mesaj ve hatalı olabilecek bir öneri verilecek. "
            "Hakaret, kişisel aşağılama, tehdit ve kırık cümle bırakma. Özgün mesajdaki gerçek görüşü, soruyu, sayıları, "
            "kaynak talebini ve yönü koru; olmayan yeni fikir ekleme. Salt hakaret varsa yeni iddia uydurma, eleştiriyi görüş ve gerekçe eksenine taşı. "
            "En fazla iki doğal Türkçe cümle yaz. Yalnızca nihai öneriyi döndür."
        )
        user_prompt = (
            f'Konu: {context.strip() or "Belirtilmedi"}\n'
            f'Sinyaller: {", ".join(signals)}\n'
            f'Özgün mesaj: {original}\n'
            f'İlk öneri: {bad_candidate}'
        )
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors='pt',
        ).to(model.device)
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=min(64, int(getattr(engine_module, 'MAX_NEW_TOKENS', 48)) + 16),
                do_sample=False,
                repetition_penalty=1.12,
                no_repeat_ngram_size=3,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated = outputs[0][inputs['input_ids'].shape[-1]:]
        candidate = tokenizer.decode(generated, skip_special_tokens=True)
        if hasattr(engine_module, '_clean_generation'):
            candidate = engine_module._clean_generation(candidate)
        candidate = candidate.strip()
        if candidate and not _quality_issue(engine_module, original, candidate, signals):
            return candidate
    except Exception:
        return ''
    return ''


def install(engine_module: Any) -> None:
    """coach_engine.rewrite_with_ai üzerine idempotent son kalite kapısı kurar."""
    if getattr(engine_module, '_N_KOPRU_FINAL_GUARD_INSTALLED', False):
        return

    original_rewrite = engine_module.rewrite_with_ai

    def guarded_rewrite_with_ai(text: str, context: str = '', use_ai: bool = True) -> dict[str, Any]:
        result = dict(original_rewrite(text, context=context, use_ai=use_ai))
        original = text.strip()
        if not original:
            return result

        signals = list(result.get('signals') or engine_module.analyze_message(original))
        suggestion = str(result.get('suggestion') or '').strip()
        issue = _quality_issue(engine_module, original, suggestion, signals)
        if not issue:
            return result

        # Yalnız problemli adayda, hazırsa ikinci yerel AI hakemi devreye girer.
        repaired = _ai_repair(engine_module, original, suggestion, context, signals) if use_ai else ''
        if repaired:
            result['suggestion'] = repaired
            result['engine'] = 'quality-guard-ai'
            result['reason'] = (
                'Son kalite denetimi ilk öneride anlam/anlatım sorunu buldu; '
                'yerel AI hakemi öneriyi yeniden yazdı ve güvenlik kontrollerinden geçirdi.'
            )
            return result

        safe = _fallback(engine_module, original, context, signals)
        # Son bir kez kontrol; bu dahi başarısızsa sabit güvenli cümle kullanılır.
        if _quality_issue(engine_module, original, safe, signals):
            safe = _safe_generic(original)

        result['suggestion'] = safe
        result['engine'] = 'quality-guard-safe'
        result['reason'] = (
            f'Son kalite denetimi ilk öneriyi reddetti ({issue}); '
            'kırık veya kişiselleştirilmiş ifade kullanıcıya gösterilmeden güvenli yeniden yazım kullanıldı.'
        )
        return result

    engine_module.rewrite_with_ai = guarded_rewrite_with_ai
    engine_module._N_KOPRU_FINAL_GUARD_INSTALLED = True
