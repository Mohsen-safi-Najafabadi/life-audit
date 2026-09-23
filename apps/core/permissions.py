"""Server-side authorisation helpers.

Every rule in the application is enforced here, on the server. The UI may
also hide buttons a user cannot use, but that is cosmetic only: no
permission decision is ever made in the browser.
"""

from functools import wraps

from django.http import Http404
from django.shortcuts import get_object_or_404

from apps.workspaces.models import Membership, Workspace


def get_workspace_or_404(user, workspace_id):
    """
    Fetch a workspace the user is actually a member of.

    Raises Http404 when the workspace does not exist OR when the user has no
    accepted membership in it. Returning 404 rather than 403 is deliberate:
    a 403 would confirm that the workspace exists, letting an attacker probe
    for valid identifiers.
    """
    return get_object_or_404(
        Workspace,
        id=workspace_id,
        memberships__user=user,
        memberships__accepted_at__isnull=False,
    )


def user_workspaces(user):
    """Every workspace this user may see. The basis of all scoped queries."""
    if not user or not user.is_authenticated:
        return Workspace.objects.none()
    return Workspace.objects.filter(
        memberships__user=user, memberships__accepted_at__isnull=False
    ).distinct()


def has_role(user, workspace, *roles):
    """True when the user holds any of the given roles in the workspace."""
    if not user or not user.is_authenticated:
        return False
    return Membership.objects.filter(
        workspace=workspace,
        user=user,
        role__in=roles,
        accepted_at__isnull=False,
    ).exists()


def can_view(user, workspace):
    return has_role(
        user, workspace, Membership.Role.OWNER, Membership.Role.EDITOR,
        Membership.Role.VIEWER,
    )


def can_edit(user, workspace):
    return has_role(user, workspace, Membership.Role.OWNER, Membership.Role.EDITOR)


def can_administer(user, workspace):
    return has_role(user, workspace, Membership.Role.OWNER)


def require_role(*roles):
    """
    Decorator for views that take a workspace_id argument.

    Usage:

        @require_role(Membership.Role.OWNER, Membership.Role.EDITOR)
        def create_assessment(request, workspace_id):
            ...

    The view receives request.workspace, already verified.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            workspace_id = kwargs.get("workspace_id")
            if workspace_id is None:
                raise Http404

            workspace = get_workspace_or_404(request.user, workspace_id)

            if not has_role(request.user, workspace, *roles):
                raise Http404

            request.workspace = workspace
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator