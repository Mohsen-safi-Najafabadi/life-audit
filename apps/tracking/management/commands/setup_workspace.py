"""Create a workspace for a user and seed the default domains.

Usage:
    python manage.py setup_workspace --email you@example.com --name "My life"
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.tracking.defaults import seed_domains
from apps.workspaces.models import Membership, Workspace

User = get_user_model()


class Command(BaseCommand):
    help = "Create a workspace with the twelve default domains."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Owner's email address.")
        parser.add_argument("--name", default="My life", help="Workspace name.")

    @transaction.atomic
    def handle(self, *args, **options):
        email = options["email"].lower()
        name = options["name"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"No user with email {email}. Create one first.")

        workspace, created = Workspace.objects.get_or_create(
            name=name, owner=user, defaults={"timezone": "Europe/Berlin"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created workspace: {workspace.name}"))
        else:
            self.stdout.write(f"Workspace already exists: {workspace.name}")

        membership, created = Membership.objects.get_or_create(
            workspace=workspace,
            user=user,
            defaults={
                "role": Membership.Role.OWNER,
                "accepted_at": timezone.now(),
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Granted {user.email} the owner role"))

        new_domains = seed_domains(workspace)
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(new_domains)} domains "
                               f"({workspace.domains.count()} total)")
        )