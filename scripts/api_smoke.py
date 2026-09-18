"""N-KÖPRÜ v1.5.0 için geçici SQLite üzerinde 35 maddelik API kabul kontrolü.

Bu script gerçek kullanıcı veya dış servis kullanmaz. Her çalıştırmada geçici
bir veritabanı açar, temel uçları sabit demo verisiyle dener ve sonunda siler.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

DB_PATH = Path(tempfile.gettempdir()) / f"nkopru_v150_api_smoke_{os.getpid()}.db"
os.environ["N_KOPRU_DB_PATH"] = str(DB_PATH)

from fastapi.testclient import TestClient  # noqa: E402

from app.database import reset_database_for_tests  # noqa: E402
from app.main import app  # noqa: E402
from app.pilot import SCENARIOS  # noqa: E402


def remove_test_database() -> None:
    for suffix in ("", "-wal", "-shm"):
        (Path(str(DB_PATH) + suffix)).unlink(missing_ok=True)


def main() -> int:
    remove_test_database()
    reset_database_for_tests()
    client = TestClient(app)
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, passed: bool, detail: str = "") -> None:
        checks.append((name, passed, detail))

    try:
        health = client.get("/health")
        check("health", health.status_code == 200 and health.json()["version"] == "1.5.0")

        readiness = client.get("/api/system/readiness")
        readiness_body = readiness.json()
        check(
            "readiness",
            readiness.status_code == 200
            and readiness_body["presentation_ready"] is True
            and readiness_body["required_ready_count"] == 5,
        )

        demo = client.get("/api/posts/demo")
        demo_body = demo.json()
        demo_id = int(demo_body["id"])
        check("demo post", demo.status_code == 200 and len(demo_body["comments"]) >= 20)

        post = client.get(f"/api/posts/{demo_id}")
        check("post by id", post.status_code == 200 and post.json()["id"] == demo_id)

        analysis = client.get(f"/api/analyze/{demo_id}?use_ai=false")
        analysis_body = analysis.json()
        check(
            "demo analysis",
            analysis.status_code == 200
            and bool(analysis_body.get("short_summary"))
            and bool(analysis_body.get("viewpoints"))
            and bool(analysis_body.get("bridge", {}).get("bridge_question")),
        )

        ai_status = client.get("/api/ai/status")
        check("stance status", ai_status.status_code == 200 and "mode" in ai_status.json())

        coach_status = client.get("/api/coach/status")
        check("coach status", coach_status.status_code == 200 and "mode" in coach_status.json())

        rewrite = client.post(
            "/api/rewrite",
            json={
                "text": "Sen hiçbir şey bilmiyorsun; kaynağın bile yok.",
                "context": "Yapay zekâ eğitimde kullanılmalı mı?",
                "use_ai": False,
            },
        )
        rewrite_body = rewrite.json()
        check(
            "coach rewrite",
            rewrite.status_code == 200
            and bool(rewrite_body.get("suggestion"))
            and "kaynak" in rewrite_body["suggestion"].casefold(),
        )

        explore = client.get("/api/explore")
        topics = explore.json().get("topics", []) if explore.status_code == 200 else []
        check("explore list", explore.status_code == 200 and bool(topics))

        topic_id = int(topics[0]["id"]) if topics else -1
        explore_item = client.get(f"/api/explore/{topic_id}")
        check("explore item", explore_item.status_code == 200 and explore_item.json()["id"] == topic_id)

        custom = client.post(
            "/api/analyze-discussion",
            json={
                "title": "Kontrollü yerel tartışma",
                "comments": [
                    "Bu uygulama kontrollü koşullarda yararlı olabilir.",
                    "Güvenlik ve maliyet bilgisi açıklanırsa değerlendirebiliriz.",
                    "Bu karar için kaynak ve karşılaştırmalı veri gerekli.",
                ],
                "use_ai": False,
            },
        )
        custom_body = custom.json()
        custom_id = int(custom_body.get("post", {}).get("id", -1))
        check("custom analysis", custom.status_code == 200 and custom_id > 0)

        append = client.post(
            f"/api/posts/{custom_id}/comments",
            json={"text": "Uygulama koşulları ayrıca açıklanmalı.", "use_ai": False},
        )
        check("append comment", append.status_code == 200 and bool(append.json().get("comment")))

        history = client.get("/api/history")
        history_body = history.json()
        history_id = int(history_body["analyses"][0]["id"]) if history_body.get("analyses") else -1
        history_detail = client.get(f"/api/history/{history_id}")
        check(
            "history list and detail",
            history.status_code == 200
            and bool(history_body.get("analyses"))
            and history_detail.status_code == 200,
        )

        notifications = client.get("/api/notifications")
        notification_body = notifications.json()
        notification_id = (
            int(notification_body["notifications"][0]["id"])
            if notification_body.get("notifications")
            else -1
        )
        check("notification list", notifications.status_code == 200 and "unread_count" in notification_body)

        filtered = client.get("/api/notifications?status=unread")
        if notification_id > 0:
            read = client.post(f"/api/notifications/{notification_id}/read")
            unread = client.post(f"/api/notifications/{notification_id}/unread")
            actions_ok = read.status_code == 200 and unread.status_code == 200
        else:
            actions_ok = filtered.status_code == 200
        check("notification filter and actions", filtered.status_code == 200 and actions_ok)

        read_all = client.post("/api/notifications/read-all")
        deleted = client.delete("/api/notifications/read")
        check("notification maintenance", read_all.status_code == 200 and deleted.status_code == 200)

        conversations = client.get("/api/messages")
        check("message list", conversations.status_code == 200 and bool(conversations.json().get("conversations")))

        detail = client.get("/api/messages/1")
        send = client.post("/api/messages/1", json={"text": "Yerel demo notunu ekipçe inceleyelim."})
        check("message detail and send", detail.status_code == 200 and send.status_code == 200)

        bridge = analysis_body.get("bridge", {})
        share = client.post(
            "/api/messages/bridge/share",
            json={
                "conversation_id": 2,
                "post_id": demo_id,
                "title": demo_body["text"],
                "summary": analysis_body["short_summary"],
                "common_acceptance": bridge.get("common_acceptance", ""),
                "main_divergence": bridge.get("main_divergence", ""),
                "missing_information": bridge.get("missing_information", ""),
                "bridge_question": bridge.get("bridge_question", "Bir sonraki kanıt nedir?"),
            },
        )
        check("share bridge", share.status_code == 200 and share.json().get("attachment") is not None)

        bookmarks = client.get("/api/bookmarks")
        check("bookmark list", bookmarks.status_code == 200)

        bookmark = client.post(
            "/api/bookmarks",
            json={
                "kind": "discussion",
                "post_id": demo_id,
                "title": demo_body["text"],
                "text": "Jüri demosu için kaydedilmiş yerel tartışma.",
                "tab_index": 0,
            },
        )
        bookmark_id = int(bookmark.json().get("bookmark", {}).get("id", -1))
        check("bookmark create", bookmark.status_code == 200 and bookmark_id > 0)

        bookmark_detail = client.get(f"/api/bookmarks/{bookmark_id}")
        check("bookmark detail", bookmark_detail.status_code == 200)

        bookmark_delete = client.delete(f"/api/bookmarks/{bookmark_id}")
        check("bookmark delete", bookmark_delete.status_code == 200)

        lists = client.get("/api/lists")
        check("list collection", lists.status_code == 200 and bool(lists.json().get("lists")))

        created_list = client.post(
            "/api/lists",
            json={"name": "Yerel jüri notları", "description": "Kontrollü demo kayıtları."},
        )
        list_id = int(created_list.json().get("list", {}).get("id", -1))
        check("list create", created_list.status_code == 200 and list_id > 0)

        list_detail = client.get(f"/api/lists/{list_id}")
        check("list detail", list_detail.status_code == 200 and list_detail.json()["list"]["id"] == list_id)

        entry = client.post(
            f"/api/lists/{list_id}/items",
            json={
                "kind": "discussion",
                "post_id": demo_id,
                "title": demo_body["text"],
                "text": "Jüri demosu tartışması.",
                "tab_index": 0,
            },
        )
        entry_id = int(entry.json().get("item", {}).get("id", -1))
        check("list entry create", entry.status_code == 200 and entry_id > 0)

        entry_delete = client.delete(f"/api/lists/{list_id}/items/{entry_id}")
        check("list entry delete", entry_delete.status_code == 200)

        list_delete = client.delete(f"/api/lists/{list_id}")
        check("list delete", list_delete.status_code == 200)

        profile = client.get("/api/profile")
        check("profile read", profile.status_code == 200 and bool(profile.json().get("user")))

        profile_update = client.put(
            "/api/profile",
            json={
                "display_name": "Yerel Demo",
                "handle": "@yerel_demo",
                "bio": "N-KÖPRÜ v1.5.0 kontrollü çalışma profili",
            },
        )
        check("profile update", profile_update.status_code == 200 and profile_update.json()["user"]["handle"] == "@yerel_demo")

        overview = client.get("/api/pilot")
        overview_body = overview.json()
        check(
            "controlled demo overview",
            overview.status_code == 200
            and overview_body["completed_session_count"] == 0
            and "gerçek kullanıcı" in overview_body["conclusion"].casefold(),
        )

        session_response = client.post("/api/pilot/sessions", json={"consent": True, "practice": True})
        session = session_response.json()
        phase = session.get("current_phase") or {}
        first = client.post(
            f"/api/pilot/sessions/{session.get('session_id', -1)}/phases",
            json={
                "phase_index": phase.get("phase_index", 0),
                "selected_answer": SCENARIOS[phase.get("scenario_key", "night-transport")]["correct_answer"],
                "duration_ms": 5000,
                "clarity_rating": 4,
                "confidence_rating": 4,
            },
        )
        next_phase = first.json().get("session", {}).get("current_phase") if first.status_code == 200 else None
        second = client.post(
            f"/api/pilot/sessions/{session.get('session_id', -1)}/phases",
            json={
                "phase_index": (next_phase or {}).get("phase_index", 1),
                "selected_answer": SCENARIOS[(next_phase or {}).get("scenario_key", "park-hours")]["correct_answer"],
                "duration_ms": 5000,
                "clarity_rating": 4,
                "confidence_rating": 4,
            },
        )
        session_get = client.get(f"/api/pilot/sessions/{session.get('session_id', -1)}")
        csv_response = client.get("/api/pilot/results.csv")
        check(
            "controlled demo two phases",
            session_response.status_code == 200
            and first.status_code == 200
            and second.status_code == 200
            and session_get.status_code == 200
            and session_get.json()["completed"] is True
            and csv_response.status_code == 200
            and csv_response.text.count("\n") == 1,
        )

        real_mode = client.post("/api/pilot/sessions", json={"consent": True, "practice": False})
        cors = client.options(
            "/health",
            headers={"Origin": "https://example.invalid", "Access-Control-Request-Method": "GET"},
        )
        check(
            "real mode closed and external origin rejected",
            real_mode.status_code == 400
            and "gerçek kullanıcı" in real_mode.json()["detail"].casefold()
            and "access-control-allow-origin" not in {key.casefold(): value for key, value in cors.headers.items()},
        )
        local_cors = client.options(
            "/health",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
        )
        check(
            "local origin accepted",
            local_cors.status_code == 200
            and local_cors.headers.get("access-control-allow-origin") == "http://localhost:3000",
        )
    finally:
        client.close()
        remove_test_database()

    failures = [(name, detail) for name, passed, detail in checks if not passed]
    for index, (name, passed, detail) in enumerate(checks, start=1):
        status = "PASS" if passed else "FAIL"
        suffix = f" — {detail}" if detail else ""
        print(f"{index:02d} {status} {name}{suffix}")
    print(f"\nAPI smoke: {len(checks) - len(failures)}/{len(checks)}")
    return 1 if failures or len(checks) != 35 else 0


if __name__ == "__main__":
    raise SystemExit(main())
