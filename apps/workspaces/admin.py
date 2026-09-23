from django.contrib import admin

from .models import Membership, Workspace


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    fields = ("user", "role", "invited_by", "accepted_at")
    autocomplete_fields = ("user", "invited_by")


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "timezone", "created_at")
    search_fields = ("name", "owner__email")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "workspace", "role", "accepted_at")
    list_filter = ("role",)
    search_fields = ("user__email", "workspace__name")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user", "workspace", "invited_by")