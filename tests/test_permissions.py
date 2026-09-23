"""
Authorisation tests.

These verify the central security promise of the application: data belongs
to a workspace, and access requires an accepted membership in that
workspace. Knowing a URL or an identifier grants nothing.
"""

import pytest
from django.contrib.auth import get_user_model
from django.http import Http404
from django.utils import timezone

from apps.core.permissions import (
    can_administer,
    can_edit,
    can_view,
    get_workspace_or_404,
    user_workspaces,
)
from apps.workspaces.models import Membership, Workspace

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(email="alice@example.com", password="test-pass-1234")


@pytest.fixture
def bob(db):
    return User.objects.create_user(email="bob@example.com", password="test-pass-1234")


@pytest.fixture
def carol(db):
    """A third user with no membership anywhere."""
    return User.objects.create_user(email="carol@example.com", password="test-pass-1234")


@pytest.fixture
def alice_workspace(alice):
    workspace = Workspace.objects.create(name="Alice's life", owner=alice)
    Membership.objects.create(
        workspace=workspace,
        user=alice,
        role=Membership.Role.OWNER,
        accepted_at=timezone.now(),
    )
    return workspace


@pytest.fixture
def bob_workspace(bob):
    workspace = Workspace.objects.create(name="Bob's life", owner=bob)
    Membership.objects.create(
        workspace=workspace,
        user=bob,
        role=Membership.Role.OWNER,
        accepted_at=timezone.now(),
    )
    return workspace


class TestWorkspaceIsolation:
    def test_owner_can_reach_own_workspace(self, alice, alice_workspace):
        assert get_workspace_or_404(alice, alice_workspace.id) == alice_workspace

    def test_stranger_cannot_reach_another_workspace(self, bob, alice_workspace):
        """Bob knows the UUID but has no membership: the server denies him."""
        with pytest.raises(Http404):
            get_workspace_or_404(bob, alice_workspace.id)

    def test_user_with_no_memberships_sees_nothing(self, carol, alice_workspace, bob_workspace):
        assert user_workspaces(carol).count() == 0

    def test_user_sees_only_their_own_workspaces(self, alice, alice_workspace, bob_workspace):
        visible = user_workspaces(alice)
        assert list(visible) == [alice_workspace]
        assert bob_workspace not in visible


class TestRoles:
    def test_owner_has_every_permission(self, alice, alice_workspace):
        assert can_view(alice, alice_workspace)
        assert can_edit(alice, alice_workspace)
        assert can_administer(alice, alice_workspace)

    def test_editor_can_edit_but_not_administer(self, alice_workspace, bob):
        Membership.objects.create(
            workspace=alice_workspace,
            user=bob,
            role=Membership.Role.EDITOR,
            accepted_at=timezone.now(),
        )
        assert can_view(bob, alice_workspace)
        assert can_edit(bob, alice_workspace)
        assert not can_administer(bob, alice_workspace)

    def test_viewer_can_only_view(self, alice_workspace, bob):
        Membership.objects.create(
            workspace=alice_workspace,
            user=bob,
            role=Membership.Role.VIEWER,
            accepted_at=timezone.now(),
        )
        assert can_view(bob, alice_workspace)
        assert not can_edit(bob, alice_workspace)
        assert not can_administer(bob, alice_workspace)


class TestPendingInvitations:
    def test_unaccepted_membership_grants_nothing(self, alice_workspace, bob):
        """An invitation that was never accepted is not access."""
        Membership.objects.create(
            workspace=alice_workspace,
            user=bob,
            role=Membership.Role.EDITOR,
            accepted_at=None,
        )
        assert not can_view(bob, alice_workspace)
        assert not can_edit(bob, alice_workspace)
        with pytest.raises(Http404):
            get_workspace_or_404(bob, alice_workspace.id)


class TestConstraints:
    def test_one_role_per_user_per_workspace(self, alice_workspace, bob):
        """The database rejects a duplicate membership, not just the form."""
        from django.db import IntegrityError

        Membership.objects.create(
            workspace=alice_workspace, user=bob, role=Membership.Role.VIEWER
        )
        with pytest.raises(IntegrityError):
            Membership.objects.create(
                workspace=alice_workspace, user=bob, role=Membership.Role.EDITOR
            )