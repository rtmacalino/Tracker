"""Single source of truth for the asset grid and its exports."""

from django.utils import timezone

ASSET_COLUMNS = [
    {"key": "id", "label": "ID"},
    {"key": "name", "label": "Name"},
    {"key": "type", "label": "Type"},
    {"key": "status", "label": "Status"},
    {"key": "vendor", "label": "Vendor"},
    {"key": "custodian", "label": "Custodian"},
    {"key": "description", "label": "Description"},
    {"key": "added", "label": "Added"},
    {"key": "updated", "label": "Updated"},
]

ASSET_COLUMN_KEYS = tuple(column["key"] for column in ASSET_COLUMNS)
ASSET_COLUMN_MAP = {column["key"]: column for column in ASSET_COLUMNS}

# Regular users start with the compact view. Admin/Engineers start with every
# allowed column. Users can override either default from the gear menu.
CORE_COLUMN_KEYS = ("id", "name", "type", "status", "vendor", "custodian")


def default_allowed_columns():
    """The complete catalog, used when no admin/Engineer choice exists yet."""
    return list(ASSET_COLUMN_KEYS)


def normalized_column_keys(keys):
    """Keep known keys, drop duplicates, and preserve the supplied order."""
    selected = []
    seen = set()
    for key in keys or []:
        if key in ASSET_COLUMN_MAP and key not in seen:
            selected.append(key)
            seen.add(key)
    return selected


def columns_for_keys(keys):
    """Return column dictionaries in the same order as ``keys``."""
    selected = []
    seen = set()
    for key in keys or []:
        if key in ASSET_COLUMN_MAP and key not in seen:
            selected.append(ASSET_COLUMN_MAP[key])
            seen.add(key)
    return selected


def allowed_column_keys():
    """The columns Admin/Engineers have made available to users."""
    from .models import GridColumnSettings

    row = GridColumnSettings.objects.filter(pk=1).first()
    keys = normalized_column_keys(row.allowed_columns if row else [])
    return keys or default_allowed_columns()


def allowed_columns():
    return columns_for_keys(allowed_column_keys())


def default_user_column_keys(user):
    """Default view for a user who has not customized their columns.

    Admin/Engineers default to every allowed column. Everyone else starts with
    the compact core set, falling back to all allowed columns when an admin has
    removed one of the core fields from the catalog.
    """
    allowed = allowed_column_keys()
    if user.is_superuser:
        return allowed

    from .access import is_engineer

    if is_engineer(user):
        return allowed

    core = [key for key in CORE_COLUMN_KEYS if key in allowed]
    return core or allowed


def user_column_order(user):
    """Ordered list of every allowed column for this user."""
    from .models import UserColumnPreference

    allowed = allowed_column_keys()
    if not user.is_authenticated:
        return allowed

    preference = UserColumnPreference.objects.filter(user=user).first()
    if preference is None or not preference.column_order:
        return allowed

    order = []
    seen = set()
    for key in normalized_column_keys(preference.column_order):
        if key in allowed and key not in seen:
            order.append(key)
            seen.add(key)
    # A newly allowed column (or a column added to the catalog later) is
    # appended instead of disappearing from the arrangement list.
    for key in allowed:
        if key not in seen:
            order.append(key)
            seen.add(key)
    return order


def user_column_keys(user):
    """Visible columns for a user, in their personal arrangement."""
    from .models import UserColumnPreference

    allowed = allowed_column_keys()
    order = user_column_order(user)
    preference = (
        UserColumnPreference.objects.filter(user=user).first()
        if user.is_authenticated
        else None
    )

    if preference is None or preference.visible_columns is None:
        visible = set(default_user_column_keys(user))
    else:
        visible = {
            key
            for key in normalized_column_keys(preference.visible_columns)
            if key in allowed
        }
        if not visible:
            visible = set(default_user_column_keys(user))

    return [key for key in order if key in visible]


def user_columns(user):
    return columns_for_keys(user_column_keys(user))


def export_column_keys(request):
    """Columns for an export, optionally supplied by the on-screen grid.

    The browser adds ``cols`` so an export always matches the grid even if a
    preference save is still in flight. The server only accepts allowed keys.
    """
    raw = request.GET.get("cols")
    if raw is None:
        return user_column_keys(request.user)

    allowed = set(allowed_column_keys())
    keys = [
        key for key in normalized_column_keys(raw.split(",")) if key in allowed
    ]
    return keys or user_column_keys(request.user)


def _format_timestamp(value):
    if not value:
        return ""
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")


def asset_column_value(asset, key):
    if key == "id":
        return asset.pk
    if key == "name":
        return asset.name
    if key == "type":
        return asset.asset_type.name if asset.asset_type_id else ""
    if key == "status":
        return asset.status_label
    if key == "vendor":
        return asset.vendor.name if asset.vendor_id else ""
    if key == "custodian":
        return asset.custodian.username if asset.custodian_id else ""
    if key == "description":
        return asset.description or ""
    if key == "added":
        return _format_timestamp(asset.created_at)
    if key == "updated":
        return _format_timestamp(asset.updated_at)
    return ""
