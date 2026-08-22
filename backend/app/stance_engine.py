"""N-KÖPRÜ v0.3.2 - Hibrit Transformer görüş motoru.

Amaç:
- Bariz ve yüksek kesinlikli Türkçe sinyalleri hızlı yapısal kurallarla ayırmak.
- Belirsiz yorumları gerçek mDeBERTa-XNLI Transformer modeline göndermek.
- CPU üzerindeki gecikmeyi azaltmak.
- Zero-shot modelin "yasaklanmalı mı?" gibi soru başlıklarında oluşan yön yanlılığını azaltmak.

Bu yapı N-KÖPRÜ'nün raporda tanımlanan hibrit AI yaklaşımıyla uyumludur.
"""
from __future__ import annotations

import importlib.util
import os
import re
import time
from typing import Iterable

MODEL_NAME = os.getenv(
    "N_KOPRU_STANCE_MODEL",
    "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
)

BATCH_SIZE = int(os.getenv("N_KOPRU_AI_BATCH_SIZE", "4"))

_PIPELINE = None
_DEVICE = "cpu"
_LOAD_ERROR: str | None = None

LABEL_MAP = {
    "yapay zekâ kullanımını destekliyor veya tamamen yasaklanmasına karşı çıkıyor": "Destekleyen",
    "yapay zekâ kullanımını kısıtlamak ya da yasaklamak istiyor": "Karşı / Sınırlayıcı",
    "yapay zekânın belirli koşul, kural veya denetim altında kullanılmasını öneriyor": "Koşullu / Dengeli",
    "doğrudan taraf belirtmeden bilgi, gözlem veya değerlendirme sunuyor": "Soru / Tarafsız",
}
CANDIDATE_LABELS = list(LABEL_MAP.keys())

# Yapay zekâ dışındaki tartışmalarda aynı dört görüşü konu-bağımsız
# hipotezlerle sorarız; mevcut demo başlıkları ve adayları aynen korunur.
GENERIC_LABEL_MAP = {
    "başlıktaki uygulamayı destekliyor veya tamamen yasaklanmasına karşı çıkıyor": "Destekleyen",
    "başlıktaki uygulamayı kısıtlamak ya da yasaklamak istiyor": "Karşı / Sınırlayıcı",
    "uygulamanın belirli koşul, kural veya denetim altında sürmesini öneriyor": "Koşullu / Dengeli",
    "doğrudan taraf belirtmeden bilgi, gözlem veya değerlendirme sunuyor": "Soru / Tarafsız",
}


def candidate_labels_for_title(title: str) -> dict[str, str]:
    lowered = title.casefold()
    if any(signal in lowered for signal in ('yapay zek', 'üretken ai', 'generative ai')):
        return LABEL_MAP
    return GENERIC_LABEL_MAP

CONDITIONAL_SIGNALS = (
    "kontrollü", "koşullu", "şartıyla", "şart", "kural", "yönerge", "denetim",
    "etik kullanım", "şeffaflık", "açıkça belirtil", "kaynak göstermeden",
    "yasak yerine", "sınavlarda yasak", "kullanım amacı", "bağlama göre",
    "nasıl kullandığımız", "hangi kullanım", "ölçmeliyiz",
)

SUPPORT_SIGNALS = (
    "yasaklamak yanlış", "tamamen yasaklamak yanlış", "yasaklanmasına karşı",
    "engellemek gerçekçi değil", "tamamen engellemek gerçekçi değil",
    "interneti yasaklamaya", "doğru kullanılırsa", "faydalı", "yararlı",
    "okuryazarlığı", "nasıl kullanılacağını öğret", "serbest olmalı",
)

RESTRICT_SIGNALS = (
    "kesinlikle yasak", "yasaklanmalı", "ciddi problem", "ciddi sorun",
    "düşünmeyi bırakıyor", "zarar görüyor", "zarar veriyor",
    "ödevi yapay zekâya yaptır", "bütün ödevi", "tamamını yapay zekâ",
)

FACTUAL_PATTERNS = (
    r"%\s?\d+",
    r"\b\d+(?:[.,]\d+)?\s?(?:kişi|öğrenci|yıl|saat|gün)\b",
)

PERSONAL_USE_SIGNALS = (
    "kullanıyorum", "yararlanıyorum", "destek alıyorum", "açıklama alıyorum",
)
BOUNDED_USE_SIGNALS = (
    "açıklama almak", "açıklama için", "ders çalış", "öğrenmek için",
    "konuyu anlamak", "yalnızca", "sadece", "kontrol ederek",
)
NEGATIVE_DELEGATION_PATTERN = re.compile(
    r"(?:ödev(?:im|lerim)?|proje(?:m)?|rapor(?:um)?|metn(?:im)?|cevab(?:ım)?)"
    r"[^.?!]{0,60}\b(?:yazdırmıyorum|yaptırmıyorum|hazırlatmıyorum|"
    r"çözdürmüyorum|ürettirmiyorum)\b"
)
POSITIVE_DELEGATION_PATTERN = re.compile(
    r"(?:ödev(?:im|lerim)?|proje(?:m)?|rapor(?:um)?|metn(?:im)?|cevab(?:ım)?)"
    r"[^.?!]{0,60}\b(?:yazdırıyorum|yaptırıyorum|hazırlatıyorum|"
    r"çözdürüyorum|ürettiriyorum)\b"
)
EVIDENCE_GAP_PATTERNS = (
    r"kaynak\s+(?:belirtilm|gösterilm|paylaşılm|sunulm|açıklanm)",
    r"(?:kaynak|veri|kanıt|araştırma|örneklem)\s+(?:olmadan|eksik|yok)",
    r"(?:kaynak|veri|kanıt|örneklem)[^.?!]{0,45}(?:gerek|paylaşılmalı|sunulmalı)",
)
EVIDENCE_CLAIM_SIGNALS = (
    "yüzde", "oran", "istatistik", "veri", "iddia", "örneklem",
    "araştırma", "kanıt", "sonuç", "ölçüm", "rakam", "sayısal",
)


def semantic_guardrail_label(text: str) -> tuple[str | None, str | None]:
    """Açık anlamı model yön yanlılığıyla çelişen yorumları önce sabitler."""
    lowered = text.lower().strip()
    personal_use = any(signal in lowered for signal in PERSONAL_USE_SIGNALS)
    bounded_use = any(signal in lowered for signal in BOUNDED_USE_SIGNALS)
    negative_delegation = NEGATIVE_DELEGATION_PATTERN.search(lowered)
    positive_delegation = POSITIVE_DELEGATION_PATTERN.search(lowered)

    if personal_use and not positive_delegation and (negative_delegation or bounded_use):
        return "Koşullu / Dengeli", "anlamsal tutarlılık: sınırlı kişisel kullanım"

    evidence_gap = any(re.search(pattern, lowered) for pattern in EVIDENCE_GAP_PATTERNS)
    evidence_claim = any(signal in lowered for signal in EVIDENCE_CLAIM_SIGNALS)
    if evidence_gap and evidence_claim:
        return "Soru / Tarafsız", "anlamsal tutarlılık: kaynak/veri eleştirisi"

    return None, None


def dependencies_installed() -> bool:
    return (
        importlib.util.find_spec("transformers") is not None
        and importlib.util.find_spec("torch") is not None
        and importlib.util.find_spec("sentencepiece") is not None
    )


def load_model():
    global _PIPELINE, _DEVICE, _LOAD_ERROR
    if _PIPELINE is not None:
        return _PIPELINE
    if not dependencies_installed():
        _LOAD_ERROR = "AI paketleri kurulu değil. requirements-ai.txt dosyasını kurun."
        return None

    try:
        import torch
        from transformers import pipeline

        use_cuda = bool(torch.cuda.is_available())
        _DEVICE = "cuda" if use_cuda else "cpu"
        device = 0 if use_cuda else -1

        if not use_cuda:
            try:
                torch.set_num_threads(min(8, max(1, os.cpu_count() or 4)))
            except Exception:
                pass

        _PIPELINE = pipeline(
            task="zero-shot-classification",
            model=MODEL_NAME,
            device=device,
        )
        _LOAD_ERROR = None
        return _PIPELINE
    except Exception as exc:
        _LOAD_ERROR = f"{type(exc).__name__}: {exc}"
        _PIPELINE = None
        return None


def status(load: bool = False) -> dict:
    if load:
        load_model()
    installed = dependencies_installed()
    loaded = _PIPELINE is not None

    if loaded:
        message = "Hibrit Transformer görüş motoru hazır."
        mode = "hybrid-transformer"
    elif installed:
        message = "AI paketleri kurulu; model henüz belleğe yüklenmedi."
        mode = "ai-ready"
    else:
        message = "AI paketleri kurulu değil; heuristik yedek motor kullanılacak."
        mode = "heuristic-fallback"

    return {
        "installed": installed,
        "loaded": loaded,
        "model": MODEL_NAME,
        "device": _DEVICE,
        "mode": mode,
        "message": message,
        "error": _LOAD_ERROR,
    }


def _structural_label(text: str) -> tuple[str | None, str | None]:
    """Yalnızca yüksek kesinlikli sinyallerde hızlı karar verir."""
    t = text.lower().strip()

    if "?" in text:
        return "Soru / Tarafsız", "yapısal soru sinyali"

    guarded_label, guardrail_reason = semantic_guardrail_label(text)
    if guarded_label is not None:
        return guarded_label, guardrail_reason

    # Koşullu ifadeyi önce değerlendiriyoruz; "zarar" gibi sözcükler koşullu
    # cümle içinde geçse bile doğrudan yasakçı etikete kaymasın.
    if any(signal in t for signal in CONDITIONAL_SIGNALS):
        return "Koşullu / Dengeli", "yüksek kesinlikli koşul/kural sinyali"

    if any(signal in t for signal in SUPPORT_SIGNALS):
        return "Destekleyen", "yüksek kesinlikli destek sinyali"

    if any(signal in t for signal in RESTRICT_SIGNALS):
        return "Karşı / Sınırlayıcı", "yüksek kesinlikli kısıtlama sinyali"

    # Salt sayısal/gözlemsel cümlelerde belirgin tutum yoksa tarafsız say.
    if any(re.search(pattern, t) for pattern in FACTUAL_PATTERNS):
        return "Soru / Tarafsız", "yapısal olgusal ifade sinyali"

    return None, None


def classify_stances(title: str, comments: Iterable) -> tuple[list[dict], dict]:
    """Yüksek kesinlikli Türkçe kurallar + gerçek Transformer ile hibrit sınıflandırma."""
    classifier = load_model()
    if classifier is None:
        return [], status(load=False)

    comments = list(comments)
    started = time.perf_counter()

    ready: dict[int, dict] = {}
    label_map = candidate_labels_for_title(title)
    model_comments = []
    sequences = []

    for comment in comments:
        label, rule_engine = _structural_label(comment.text)
        if label is not None:
            ready[comment.id] = {
                "comment_id": comment.id,
                "text": comment.text,
                "label": label,
                "confidence": 0.0,  # model güveni değildir
                "engine": rule_engine,
            }
            continue

        model_comments.append(comment)
        sequences.append(f"Konu: {title}\nYorum: {comment.text}")

    transformer_count = 0

    try:
        if sequences:
            outputs = classifier(
                sequences,
                candidate_labels=list(label_map),
                hypothesis_template="Bu yorum {}.",
                multi_label=False,
                batch_size=BATCH_SIZE,
            )
            if isinstance(outputs, dict):
                outputs = [outputs]

            for comment, result in zip(model_comments, outputs):
                raw_label = result["labels"][0]
                score = float(result["scores"][0])
                ready[comment.id] = {
                    "comment_id": comment.id,
                    "text": comment.text,
                    "label": label_map.get(raw_label, "Soru / Tarafsız"),
                    "confidence": round(score, 4),
                    "engine": f"mDeBERTa-XNLI zero-shot • batch={BATCH_SIZE}",
                }
                transformer_count += 1

        details = [ready[c.id] for c in comments if c.id in ready]
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        rule_count = len(details) - transformer_count

        info = status(load=False)
        info["mode"] = "hybrid-transformer"
        info["message"] = (
            f"{len(details)} yorum hibrit AI ile sınıflandırıldı: "
            f"{rule_count} yüksek kesinlikli yapısal sinyal, "
            f"{transformer_count} gerçek Transformer çıkarımı."
        )
        info["batch_size"] = BATCH_SIZE
        info["elapsed_ms"] = elapsed_ms
        info["rule_count"] = rule_count
        info["transformer_count"] = transformer_count
        info["semantic_guardrail_count"] = sum(
            "anlamsal tutarlılık:" in item["engine"] for item in details
        )
        return details, info

    except Exception as exc:
        global _LOAD_ERROR
        _LOAD_ERROR = f"{type(exc).__name__}: {exc}"
        info = status(load=False)
        info["mode"] = "heuristic-fallback"
        info["message"] = "Transformer analizi sırasında hata oluştu; heuristik yedeğe geçildi."
        return [], info
