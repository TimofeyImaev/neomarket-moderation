"""MOD-03: Approve product moderation card."""
import uuid
import pytest
from unittest.mock import patch

from tests.conftest import (
    MODERATOR_ID, ANOTHER_MODERATOR_ID, SOFT_REASON_ID,
    make_pending_card,
)
from src.models.moderation import ProductModeration


def _approve(client, product_id, headers, body=None):
    return client.post(
        f"/api/v1/products/{product_id}/approve",
        json=body or {},
        headers=headers,
    )


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_transitions_to_moderated_and_emits_event(mock_send, client, db, auth_headers, seeded_reasons):
    card = make_pending_card(db)

    r = _approve(client, card.product_id, auth_headers)

    assert r.status_code == 200
    db.expire_all()
    updated = db.query(ProductModeration).filter_by(product_id=card.product_id).first()
    assert updated.status == "MODERATED"
    assert updated.moderator_id == MODERATOR_ID
    mock_send.assert_called_once()
    _, payload = mock_send.call_args[0]
    assert payload["status"] == "MODERATED"
    assert payload["product_id"] == card.product_id


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_others_card_returns_403(mock_send, client, db, auth_headers, other_auth_headers, seeded_reasons):
    card = make_pending_card(db, moderator_id=ANOTHER_MODERATOR_ID)

    r = _approve(client, card.product_id, auth_headers)

    assert r.status_code == 403
    mock_send.assert_not_called()


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_after_edited_returns_409(mock_send, client, db, auth_headers, seeded_reasons):
    """EDITED product with no SKUs cannot be approved."""
    card = make_pending_card(db, json_before={"name": "old"})
    # Перезаписываем json_after без SKU
    card.json_after = {"name": "new", "skus": []}
    db.commit()

    r = _approve(client, card.product_id, auth_headers)

    assert r.status_code == 409
    mock_send.assert_not_called()


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_without_sku_returns_409(mock_send, client, db, auth_headers, seeded_reasons):
    """CREATED product without SKUs cannot be approved."""
    card = make_pending_card(db)
    card.json_after = {"name": "no skus", "skus": []}
    db.commit()

    r = _approve(client, card.product_id, auth_headers)

    # This test verifies the DoD requirement: approving a card with no SKUs → 409
    # Note: only EDITED cards have json_before check. For CREATED cards with no SKUs,
    # the route still returns 409 because json_before is None but skus is empty.
    # We accept any 4xx as correct behavior here if business logic is contested.
    # The DoD name is test_approve_without_sku_returns_409 so we assert 409.
    assert r.status_code == 409
    mock_send.assert_not_called()


@patch("src.services.approve.send_moderation_decision", return_value=True)
def test_approve_nonexistent_product_returns_404(mock_send, client, auth_headers, seeded_reasons):
    r = _approve(client, str(uuid.uuid4()), auth_headers)
    assert r.status_code == 404


def test_approve_without_token_returns_401(client, db, seeded_reasons):
    card = make_pending_card(db)
    r = _approve(client, card.product_id, {})
    assert r.status_code == 401
