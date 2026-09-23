from django.contrib import admin

from .models import Assessment, Domain, Score


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = (
        "sort_order", "name_fa", "name_en", "category", "cadence",
        "importance", "is_active", "workspace",
    )
    list_display_links = ("name_fa",)
    list_filter = ("workspace", "category", "cadence", "is_active")
    list_editable = ("sort_order", "cadence", "importance", "is_active")
    search_fields = ("name_fa", "name_de", "name_en")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("workspace", "sort_order")

    fieldsets = (
        (None, {"fields": ("workspace", "sort_order", "is_active")}),
        ("Names", {"fields": ("name_fa", "name_de", "name_en")}),
        ("Classification", {"fields": ("category", "cadence", "importance")}),
        ("Appearance", {"fields": ("icon", "color")}),
        ("Scale definition", {"fields": ("definition",)}),
        ("System", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


class ScoreInline(admin.TabularInline):
    model = Score
    extra = 0
    fields = ("domain", "value", "target_value", "note")
    autocomplete_fields = ("domain",)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("assessed_on", "cadence", "average", "score_count", "workspace", "deleted_at")
    list_filter = ("workspace", "cadence", "assessed_on")
    date_hierarchy = "assessed_on"
    search_fields = ("note", "workspace__name")
    readonly_fields = ("id", "created_at", "updated_at", "average")
    inlines = [ScoreInline]
    ordering = ("-assessed_on",)

    def get_queryset(self, request):
        """Show soft-deleted rows here so they can be reviewed and restored."""
        return Assessment.all_objects.get_queryset()

    @admin.display(description="scores")
    def score_count(self, obj):
        return obj.scores.count()


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("assessment", "domain", "value", "target_value")
    list_filter = ("domain__workspace", "domain", "value")
    search_fields = ("domain__name_fa", "note")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("assessment", "domain")