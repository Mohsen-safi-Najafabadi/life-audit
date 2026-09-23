"""The twelve default domains, taken from the printed Life Audit sheet.

Seeded into each new workspace. They are ordinary rows afterwards: rename,
reorder, retire or add as you like without touching this file.

Cadence assignments are a starting point, not a rule. Areas that genuinely
move day to day are daily; areas that move over months are not, because
rating them nightly would add noise rather than information.
"""

from .models import Cadence, Domain

DEFAULT_DOMAINS = [
    {
        "name_fa": "انرژی و بدن",
        "name_de": "Energie & Körper",
        "name_en": "Energy & body",
        "category": Domain.Category.BODY,
        "cadence": Cadence.DAILY,
        "icon": "dumbbell",
        "sort_order": 1,
    },
    {
        "name_fa": "خواب",
        "name_de": "Schlaf",
        "name_en": "Sleep",
        "category": Domain.Category.BODY,
        "cadence": Cadence.DAILY,
        "icon": "bed",
        "sort_order": 2,
    },
    {
        "name_fa": "وضعیت روانی و حال روحی",
        "name_de": "Psychisches Befinden & Stimmung",
        "name_en": "Mental state & mood",
        "category": Domain.Category.MIND,
        "cadence": Cadence.DAILY,
        "icon": "smile",
        "sort_order": 3,
    },
    {
        "name_fa": "اعتماد به نفس",
        "name_de": "Selbstvertrauen",
        "name_en": "Self-confidence",
        "category": Domain.Category.MIND,
        "cadence": Cadence.MONTHLY,
        "icon": "user",
        "sort_order": 4,
    },
    {
        "name_fa": "کار",
        "name_de": "Arbeit",
        "name_en": "Work",
        "category": Domain.Category.MATERIAL,
        "cadence": Cadence.QUARTERLY,
        "icon": "briefcase",
        "sort_order": 5,
    },
    {
        "name_fa": "وضعیت مالی",
        "name_de": "Finanzen",
        "name_en": "Finances",
        "category": Domain.Category.MATERIAL,
        "cadence": Cadence.MONTHLY,
        "icon": "coins",
        "sort_order": 6,
    },
    {
        "name_fa": "اقامت",
        "name_de": "Aufenthaltsstatus",
        "name_en": "Residency status",
        "category": Domain.Category.MATERIAL,
        "cadence": Cadence.QUARTERLY,
        "icon": "file-text",
        "sort_order": 7,
    },
    {
        "name_fa": "تحصیل",
        "name_de": "Ausbildung",
        "name_en": "Education",
        "category": Domain.Category.MATERIAL,
        "cadence": Cadence.QUARTERLY,
        "icon": "graduation-cap",
        "sort_order": 8,
    },
    {
        "name_fa": "روابط",
        "name_de": "Beziehungen",
        "name_en": "Relationships",
        "category": Domain.Category.SOCIAL,
        "cadence": Cadence.MONTHLY,
        "icon": "users",
        "sort_order": 9,
    },
    {
        "name_fa": "دوستان و حمایت اجتماعی",
        "name_de": "Freunde & soziale Unterstützung",
        "name_en": "Friends & social support",
        "category": Domain.Category.SOCIAL,
        "cadence": Cadence.MONTHLY,
        "icon": "users-round",
        "sort_order": 10,
    },
    {
        "name_fa": "نظم روزانه",
        "name_de": "Tagesstruktur",
        "name_en": "Daily routine",
        "category": Domain.Category.BODY,
        "cadence": Cadence.DAILY,
        "icon": "calendar",
        "sort_order": 11,
    },
    {
        "name_fa": "امید به آینده",
        "name_de": "Zuversicht",
        "name_en": "Hope for the future",
        "category": Domain.Category.MIND,
        "cadence": Cadence.MONTHLY,
        "icon": "sun",
        "sort_order": 12,
    },
]


def seed_domains(workspace):
    """Create any missing default domains in this workspace.

    Safe to re-run: existing domains are left untouched, so a renamed or
    retired domain is never silently restored.
    """
    created = []
    for spec in DEFAULT_DOMAINS:
        domain, was_created = Domain.objects.get_or_create(
            workspace=workspace,
            name_fa=spec["name_fa"],
            defaults=spec,
        )
        if was_created:
            created.append(domain)
    return created