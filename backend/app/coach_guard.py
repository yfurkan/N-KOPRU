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


def _is_attack(signals: list[str]) -> bool:
    return bool(_ATTACK_SIGNALS.intersection(signals))


def _is_pure_attack(engine_module: Any, original: str, signals: list[str]) -> bool:
    """Gerçek tartışılabilir içerik sinyali taşımayan saldırıyı ayırır."""
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


def _malformed_issue(engine_module: Any, original: str, suggestion: str, signals: list[str]) -> str:
    """Yalnız saldırı girdilerindeki görünür biçimde bozuk son çıktıları yakalar.

    Temiz mesajlara bu kapı hiç uygulanmaz. Mevcut motorun saldırıdan sonra
    koruduğu gerçek içerik de (örn. "Bu öneri çok pahalı...") olduğu gibi kalır.
    """
    text = (suggestion or '').strip()
    if not text:
        return 'boş çıktı'
    if not _is_attack(signals):
        return ''

    low = engine_module._normalize(text) if hasattr(engine_module, '_normalize') else text.lower()

    # Önerinin kendisi hâlâ açık saldırı olarak sınıflanıyorsa dışarı verme.
    try:
        output_signals = list(engine_module.analyze_message(text))
        if _is_attack(output_signals):
            return 'saldırı kalıntısı'
    except Exception:
        pass

    # Ekran görüntüsündeki "Birisin senden daha iyi ..." sınıfı: saldırı
    # sökülürken özne/karşılaştırma kabuğu geride kalmış.
    if re.search(r'^(?:birisin|birisiniz|birisi|biri|senden|sizden|senin|sizin|sana|seni)\b', low):
        return 'kırık başlangıç'
    if re.search(r'\b(?:birisin|birisiniz)\b', low):
        return 'kişisel hitap kalıntısı'
    if re.search(r'\b(?:senden|sizden)\s+daha\s+(?:iyi|kötü|zeki|akıllı|başarılı|mantıklı|değerli)\b', low):
        return 'kişisel karşılaştırma kalıntısı'

    # Salt saldırı çıktısında ikinci kişi karşılaştırması kalmamalı. Buna
    # karşılık saldırıdan sonra kalan gerçek öneri/eleştiri cümlelerine dokunma.
    if _is_pure_attack(engine_module, original, signals):
        if re.search(r'\b(?:senden|sizden|senin|sizin)\b', low):
            return 'ikinci kişi kalıntısı'

    # Saldırı temizlenirken açık soru veya sayısal bilgi kaybolamaz.
    if 'soru' in signals and '?' not in text:
        return 'soru niyeti kayboldu'
    if 'sayısal/doğrulanabilir iddia' in signals:
        try:
            compact = text.replace(' ', '')
            for number in engine_module._numbers(original):
                if number.replace(' ', '') not in compact:
                    return 'sayısal bilgi kayboldu'
        except Exception:
            pass

    # Tek/iki kelimelik anlamsız artıkları engelle. Dört ve üzeri kelimelik
    # gerçek içerik, özel bozukluk kalıplarına takılmadıysa korunur.
    words = re.findall(r'\b\w+\b', text, flags=re.UNICODE)
    if len(words) < 4 and not text.endswith('?'):
        return 'çok kısa saldırı artığı'

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
    """Bozuk bir ilk çıktı için güvenli ve niyet-koruyan son yedek."""
    try:
        deterministic, _, _ = engine_module._deterministic_rewrite(original, context, signals)
        if not _malformed_issue(engine_module, original, deterministic, signals):
            return deterministic
    except Exception:
        pass

    if 'bağlamı yeniden değerlendirme talebi' in signals:
        return (
            'Yanıtın konuyu yeterince dikkate almadığını düşünüyorum. '
            'Konuyu baştan değerlendirerek yeniden yanıtlayabilir misin?'
        )

    if 'konuya katkı eleştirisi' in signals:
        return (
            'Yorumunun tartışmanın konusuna yeterince katkı sağlamadığını düşünüyorum. '
            'Konuyla ilgili görüşünü daha somut biçimde açıklayabilir misin?'
        )

    if 'kaynak/kanıt vurgusu' in signals:
        return 'Bu iddianın dayanağını değerlendirebilmek için kullandığın kaynak veya kanıtı paylaşabilir misin?'

    if 'soru' in signals:
        try:
            clean = engine_module._strip_attack_shell(original)
            clean = re.sub(r'^\s*(?:m[ıi]s[ıi]n|misin|musun|müsün)\b[ ,;:-]*', '', clean, flags=re.IGNORECASE)
            if len(clean.split()) >= 3:
                candidate = engine_module._question_sentence(clean)
                if not _malformed_issue(engine_module, original, candidate, signals):
                    return candidate
        except Exception:
            pass

    if 'sayısal/doğrulanabilir iddia' in signals:
        try:
            candidate = engine_module._numeric_claim_rewrite(original)
            if not _malformed_issue(engine_module, original, candidate, signals):
                return candidate
        except Exception:
            pass

    return _safe_generic(original)


def _ai_repair(engine_module: Any, original: str, bad_candidate: str, context: str, signals: list[str]) -> str:
    """Yalnız bozuk çıktıda, bellekte hazır yerel modeli ikinci hakem yapar.

    Model burada indirilmez/yüklenmez. Hazır değilse deterministik yedeğe
    dönülür. Yeni aday hem mevcut doğrulayıcıdan hem son kalite kapısından geçer.
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
        if not candidate or _malformed_issue(engine_module, original, candidate, signals):
            return ''

        valid, _ = engine_module._candidate_valid(original, candidate, signals)
        return candidate if valid else ''
    except Exception:
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

        # Ek katman yalnız ana motorun saldırı olarak sınıfladığı girdilerde
        # çalışır; temiz/nesnel mesajların davranışını değiştirmez.
        if not _is_attack(signals):
            return result

        suggestion = str(result.get('suggestion') or '').strip()
        issue = _malformed_issue(engine_module, original, suggestion, signals)
        if not issue:
            return result

        # Yalnız bozuk adayda, model zaten bellekte hazırsa ikinci yerel AI
        # hakemi denenir. Her çağrıya gereksiz 10-20 saniye eklenmez.
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
        if _malformed_issue(engine_module, original, safe, signals):
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
