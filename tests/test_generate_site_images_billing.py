from __future__ import annotations

import scripts.generate_site_images as gsi


class BillingError(Exception):
    def __init__(self, message: str = "billing limit", error_type: str = "billing_limit_user_error") -> None:
        super().__init__(message)
        self.body = {
            "error": {
                "code": "billing_hard_limit_reached",
                "type": error_type,
                "message": message,
            }
        }


def _slot(slot_id: str) -> gsi.SlotSpec:
    section, _ = slot_id.split(".", 1)
    return gsi.SlotSpec(
        slot_id=slot_id,
        section=section,
        entity={"type": "page", "id": None, "slug": slot_id},
        prompt=f"prompt {slot_id}",
        alt=f"alt {slot_id}",
        sizes=("md",),
    )


def test_billing_aborts_and_marks_pending(monkeypatch):
    saved: dict = {}

    monkeypatch.setattr(gsi, "_load_manifest", lambda: {"manifest_version": 2, "style_id": gsi.STYLE_ID, "generated_at": "", "slots": []})
    monkeypatch.setattr(gsi, "_save_manifest", lambda payload: saved.setdefault("payload", payload))
    monkeypatch.setattr(gsi, "_is_complete", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(gsi, "_save_variants", lambda *_args, **_kwargs: {"md": "/static/img/generated/mock.webp"})

    call_count = {"n": 0}

    def fail_on_first(*_args, **_kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise BillingError("límite de billing alcanzado")
        return b"png"

    monkeypatch.setattr(gsi, "_generate_mock_png", fail_on_first)

    result = gsi.generate(
        slots=[_slot("home.hero"), _slot("home.faq")],
        options=gsi.GenerationOptions(mock=True, force=False, optimize_existing=False, continue_on_error=False),
    )

    assert result.billing_detected is True
    assert result.pending_slots == ["home.faq"]
    assert result.counters["blocked_billing"] == 1

    slot_rows = {row["slot_id"]: row for row in saved["payload"]["slots"]}
    assert slot_rows["home.hero"]["status"] == "blocked_billing"
    assert slot_rows["home.hero"]["error_code"] == "billing_hard_limit_reached"
    assert "billing" in slot_rows["home.hero"]["error_message"].lower()


def test_billing_continue_uses_placeholders(monkeypatch):
    saved: dict = {}

    monkeypatch.setattr(gsi, "_load_manifest", lambda: {"manifest_version": 2, "style_id": gsi.STYLE_ID, "generated_at": "", "slots": []})
    monkeypatch.setattr(gsi, "_save_manifest", lambda payload: saved.setdefault("payload", payload))
    monkeypatch.setattr(gsi, "_is_complete", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(gsi, "_save_variants", lambda *_args, **_kwargs: {"md": "/static/img/generated/mock.webp"})

    call_count = {"n": 0}

    def first_fails_then_ok(*_args, **_kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise BillingError("hard limit reached", error_type="invalid_request_error")
        return b"png"

    monkeypatch.setattr(gsi, "_generate_mock_png", first_fails_then_ok)

    result = gsi.generate(
        slots=[_slot("home.hero"), _slot("home.faq"), _slot("home.testimonios-1")],
        options=gsi.GenerationOptions(mock=True, force=False, optimize_existing=False, continue_on_error=True),
    )

    assert result.billing_detected is True
    assert result.pending_slots == []
    assert result.counters["blocked_billing"] == 1
    assert result.counters["placeholder_due_to_billing"] == 2

    slot_rows = {row["slot_id"]: row for row in saved["payload"]["slots"]}
    assert slot_rows["home.faq"]["status"] == "placeholder_due_to_billing"
    assert slot_rows["home.testimonios-1"]["status"] == "placeholder_due_to_billing"
    assert slot_rows["home.faq"]["error_code"] == "billing_hard_limit_reached"
    assert slot_rows["home.faq"]["timestamp"]


def test_main_exits_with_code_2_on_billing(monkeypatch):
    monkeypatch.setattr(
        gsi,
        "parse_args",
        lambda: type(
            "Args",
            (),
            {
                "only": "all",
                "only_slot": None,
                "mock": True,
                "real": False,
                "force": False,
                "optimize_existing": False,
                "continue_on_error": False,
            },
        )(),
    )
    monkeypatch.setattr(gsi, "_resolve_mode", lambda _args: True)
    monkeypatch.setattr(gsi, "_all_slots", lambda: [_slot("home.hero")])
    monkeypatch.setattr(
        gsi,
        "generate",
        lambda **_kwargs: gsi.GenerationResult(
            counters={
                "generated": 0,
                "skipped": 0,
                "optimized": 0,
                "failed": 0,
                "blocked_billing": 1,
                "placeholder_due_to_billing": 0,
            },
            failures=[],
            pending_slots=[],
            billing_detected=True,
        ),
    )

    try:
        gsi.main()
        assert False, "main debía salir con SystemExit"
    except SystemExit as exc:
        assert exc.code == 2
