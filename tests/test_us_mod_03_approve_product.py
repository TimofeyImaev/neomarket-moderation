"""MOD-03: Approve product moderation card."""
import uuid
import pytest
from unittest.mock import patch

from tests.conftest import (
    MODERATOR_ID, ANOTHER_MODERATOR_ID, SOFT_REASON_ID,
    make_pending_card,
)
from src.models.moderation import ProductModeration


def _approve(client, ticket_id, headers, body=None):
    return client.post(
        f"/api/v1/tickets/{ticket_id}/approve",
        json=body or {},
        headers=headers,
    )


def _make_in_review_card(db, **kwargs):
    """Helper: create card already in IN_REVIEW status (required to approve)."""
    card = make_pending_card(db, **kwargs)
    card.status = "IN_REVIEW"
    db.commit()
    db.refresh(card)
    return card


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_transitions_to_moderated_and_emits_event(mock_send, client, db, auth_headers, seeded_reasons):
    card = _make_in_review_card(db)

    r = _approve(client, card.id, auth_headers)

    assert r.status_code == 200
    db.expire_all()
    updated = db.query(ProductModeration).filter_by(product_id=card.product_id).first()
    assert updated.status == "APPROVED"   # TicketStatus enum value per moderation/openapi.yaml:651-653
    assert updated.moderator_id == MODERATOR_ID
    mock_send.assert_called_once()
    _, payload = mock_send.call_args[0]
    assert payload["event_type"] == "MODERATED"   # B2B event type
    assert payload["product_id"] == card.product_id


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_others_card_returns_403(mock_send, client, db, auth_headers, other_auth_headers, seeded_reasons):
    card = _make_in_review_card(db, moderator_id=ANOTHER_MODERATOR_ID)

    r = _approve(client, card.id, auth_headers)

    assert r.status_code == 403
    mock_send.assert_not_called()


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_after_edited_returns_409(mock_send, client, db, auth_headers, seeded_reasons):
    """EDITED product with no SKUs cannot be approved."""
    card = _make_in_review_card(db, json_before={"name": "old"})
    card.json_after = {"name": "new", "skus": []}
    db.commit()

    r = _approve(client, card.id, auth_headers)

    assert r.status_code == 409
    mock_send.assert_not_called()


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_without_sku_returns_409(mock_send, client, db, auth_headers, seeded_reasons):
    """CREATED product without SKUs cannot be approved."""
    card = _make_in_review_card(db)
    card.json_after = {"name": "no skus", "skus": []}
    db.commit()

    r = _approve(client, card.id, auth_headers)

    assert r.status_code == 409
    mock_send.assert_not_called()


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_pending_card_returns_409(mock_send, client, db, auth_headers, seeded_reasons):
    """PENDING card cannot be approved directly — must be IN_REVIEW first."""
    card = make_pending_card(db)  # status = PENDING

    r = _approve(client, card.id, auth_headers)

    assert r.status_code == 409
    mock_send.assert_not_called()


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_nonexistent_product_returns_404(mock_send, client, auth_headers, seeded_reasons):
    r = _approve(client, str(uuid.uuid4()), auth_headers)
    assert r.status_code == 404


def test_approve_without_token_returns_401(client, db, seeded_reasons):
    card = make_pending_card(db)
    r = _approve(client, card.id, {})
    assert r.status_code == 401
