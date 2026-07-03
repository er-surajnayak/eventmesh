"""Lifecycle state-machine tests (transition table, no DB)."""

import pytest

from app.modules.events.lifecycle import ALLOWED_TRANSITIONS
from app.modules.events.models import EventStatus


def test_archived_is_terminal():
    assert ALLOWED_TRANSITIONS[EventStatus.archived] == set()


def test_cancelled_only_archives():
    assert ALLOWED_TRANSITIONS[EventStatus.cancelled] == {EventStatus.archived}


def test_published_can_hide_cancel_archive():
    assert ALLOWED_TRANSITIONS[EventStatus.published] == {
        EventStatus.hidden,
        EventStatus.cancelled,
        EventStatus.archived,
    }


def test_pending_review_can_publish():
    assert EventStatus.published in ALLOWED_TRANSITIONS[EventStatus.pending_review]


def test_draft_cannot_publish_directly():
    # Publishing from draft must go through pending_review (submit_for_review).
    assert EventStatus.published not in ALLOWED_TRANSITIONS[EventStatus.draft]


def test_every_status_has_a_transition_entry():
    for st in EventStatus:
        assert st in ALLOWED_TRANSITIONS


@pytest.mark.parametrize("st", list(EventStatus))
def test_no_self_transitions(st):
    assert st not in ALLOWED_TRANSITIONS[st]
