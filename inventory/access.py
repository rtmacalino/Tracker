from django.db.models import Q

from .models import Asset


def is_engineer(user):
    """True when the user belongs to at least one Engineer-checked group."""
    if not user.is_authenticated:
        return False
    return user.groups.filter(profile__is_engineer=True).exists()


def can_manage_columns(user):
    """Admin/Engineers control the allowed column catalog."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or is_engineer(user)


def visible_assets(user):
    """Records a user is allowed to see.

    superuser                 -> everything
    Engineer group members    -> everything
    everyone else             -> assets owned by one of their groups OR where they are custodian.
    Assets with neither a group nor a custodian are admin-only.
    """
    if not user.is_authenticated:
        return Asset.objects.none()
    if user.is_superuser or is_engineer(user):
        return Asset.objects.all()
    return Asset.objects.filter(
        Q(vendor__in=user.groups.all()) | Q(custodian=user)
    ).distinct()
