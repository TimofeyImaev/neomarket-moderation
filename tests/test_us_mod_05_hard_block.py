"""MOD-05: Hard block product via decline with hard_block reason."""
import uuid
import pytest
from unittest.mock import patch

from tests.conftest import (
    MODERATOR_ID, ANOTHER_MODERATOR_ID,
    HARD_REASON_ID, SOFT_REASON_ID,
    make_pending_card,
)
from src.models.moderation import ProductModeration
from src.services.events import handle_b2b_event
from src.schemas.moderation import B2BProductEventIn


def _decline(client, ticket_id, headers, reason_id, field_reports=None, comment="bad product"):
    return client.post(
        f"/api/v1/tickets/{ticket_id}/block",
        json={
            "blocking_reason_ids": [reason_id],
            "comment": comment,              # was moderator_comment — renamed per openapi.yaml:779
            "field_reports": field_reports or [],
        },
        headers=headers,
    )


@patch("src.services.decline.send_moderation_decision", return_value=True)
def test_hard_block_transitions_to_terminal_and_emits_event(mock_send, client, db, auth_headers, seeded_reasons):
    card = make_pending_card(db)
    card.status = "IN_REVIEW"  # must be IN_REVIEW before /block
    db.commit()

    r = _decline(client, card.id, auth_headers, HARD_REASON_ID)

    assert r.status_code == 200
    db.expire_all()
    updated = db.query(ProductModeration).filter_by(product_id=card.product_id).first()
    assert updated.status == "HARD_BLOCKED"
    mock_send.assert_called_once()


@patch("src.services.decline.send_moderation_decision", return_value=True)
def test_hard_block_event_carries_hard_block_true(mock_send, client, db, auth_headers, seeded_reasons):
    card = make_pending_card(db)
    card.status = "IN_REVIEW"
    db.commit()

    _decline(client, card.id, auth_headers, HARD_REASON_ID)

    _, payload = mock_send.call_args[0]
    assert payload["hard_block"] is True
    assert payload["event_type"] == "BLOCKED"


@patch("src.services.decline.send_moderation_decision", return_value=True)
def test_soft_block_event_carries_hard_block_false(mock_send, client, db, auth_headers, seeded_reasons):
    card = make_pending_card(db)
    card.status = "IN_REVIEW"
    db.commit()

    _decline(client, card.id, auth_headers, SOFT_REASON_ID)

    _, payload = mock_send.call_args[0]
    assert payload["hard_block"] is False


@patch("src.services.decline.send_moderation_decision", return_value=True)
def test_any_modify_on_hard_blocked_returns_403(mock_send, client, db, auth_headers, seeded_reasons):
    """Cannot decline a card that is already HARD_BLOCKED."""
    card = make_pending_card(db)
    card.status = "HARD_BLOCKED"
    db.commit()

    r = _decline(client, card.id, auth_headers, HARD_REASON_ID)

    assert r.status_code == 403
    mock_send.assert_not_called()


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_on_hard_blocked_returns_403(mock_send, client, db, auth_headers, seeded_reasons):
    """Cannot approve a card that is already HARD_BLOCKED — must return 403."""
    card = make_pending_card(db)
    card.status = "HARD_BLOCKED"
    db.commit()

    r = client.post(
        f"/api/v1/tickets/{card.id}/approve",
        json={"moderator_comment": None},
        headers=auth_headers,
    )

    assert r.status_code == 403
    mock_send.assert_not_called()


def test_edited_event_on_hard_blocked_is_ignored(db, seeded_reasons):
    """EDITED event for HARD_BLOCKED product is silently ignored."""
    card = make_pending_card(db)
    card.status = "HARD_BLOCKED"
    db.commit()

    data = B2BProductEventIn(
        product_id=card.product_id,
        seller_id=card.seller_id,
        event="EDITED",
        date="2026-01-01T00:00:00Z",
    )
    handle_b2b_event(db, data, product_json={"name": "updated"})

    db.expire_all()
    updated = db.query(ProductModeration).filter_by(product_id=card.product_id).first()
    assert updated.status == "HARD_BLOCKED"


def test_deleted_event_removes_hard_blocked(db, seeded_reasons):
    """DELETED event removes even HARD_BLOCKED card (product deleted by admin/system)."""
    card = make_pending_card(db)
    card.status = "HARD_BLOCKED"
    db.commit()

    data = B2BProductEventIn(
        product_id=card.product_id,
        seller_id=card.seller_id,
        event="DELETED",
        date="2026-01-01T00:00:00Z",
    )
    handle_b2b_event(db, data)

    db.expire_all()
    remaining = db.query(ProductModeration).filter_by(product_id=card.product_id).first()
    assert remaining is None


@patch("src.services.decline.send_moderation_decision", return_value=True)
def test_decline_others_card_returns_403(mock_send, client, db, auth_headers, other_auth_headers, seeded_reasons):
    card = make_pending_card(db, moderator_id=ANOTHER_MODERATOR_ID)

    r = _decline(client, card.id, auth_headers, SOFT_REASON_ID)

    assert r.status_code == 403
    mock_send.assert_not_called()
