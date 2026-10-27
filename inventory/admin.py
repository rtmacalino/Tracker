from django import forms
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group

from .access import visible_assets
from .models import (
    Asset,
    AssetType,
    AssetTypeStatus,
    FTTB,
    OLT,
    GroupProfile,
    all_status_options,
)


class GroupProfileForm(forms.ModelForm):
    is_vendor = forms.BooleanField(label="Vendor", required=False)
    is_engineer = forms.BooleanField(label="Engineer", required=False)

    class Meta:
        model = Group
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.profile
            except GroupProfile.DoesNotExist:
                profile = None
            if profile is not None:
                self.fields["is_vendor"].initial = profile.is_vendor
                self.fields["is_engineer"].initial = profile.is_engineer


class GroupProfileAdmin(BaseGroupAdmin):
    form = GroupProfileForm
    fieldsets = (
        (None, {"fields": ("name", "is_vendor", "is_engineer")}),
        ("Permissions", {"fields": ("permissions",)}),
    )
    list_display = ("name", "vendor_flag", "engineer_flag")
    list_select_related = ("profile",)

    @admin.display(boolean=True, description="Vendor")
    def vendor_flag(self, obj):
        try:
            return obj.profile.is_vendor
        except GroupProfile.DoesNotExist:
            return False

    @admin.display(boolean=True, description="Engineer")
    def engineer_flag(self, obj):
        try:
            return obj.profile.is_engineer
        except GroupProfile.DoesNotExist:
            return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        GroupProfile.objects.update_or_create(
            group=obj,
            defaults={
                "is_vendor": form.cleaned_data.get("is_vendor", False),
                "is_engineer": form.cleaned_data.get("is_engineer", False),
            },
        )


try:
    admin.site.unregister(Group)
except NotRegistered:
    pass
admin.site.register(Group, GroupProfileAdmin)


class AssetAdminForm(forms.ModelForm):
    status = forms.ChoiceField(label="Status")

    class Meta:
        model = Asset
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = all_status_options()

        vendor_ids = set(
            Group.objects.filter(profile__is_vendor=True).values_list("pk", flat=True)
        )
        if self.instance and self.instance.pk and self.instance.vendor_id:
            vendor_ids.add(self.instance.vendor_id)
        self.fields["vendor"].queryset = Group.objects.filter(pk__in=vendor_ids)


class AssetTypeStatusInline(admin.TabularInline):
    model = AssetTypeStatus
    extra = 1
    ordering = ("order", "key")


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    add_in_actions = True
    list_display = ("name", "description", "status_count")
    search_fields = ("name",)
    inlines = [AssetTypeStatusInline]

    @admin.display(description="Statuses")
    def status_count(self, obj):
        return obj.statuses.count()


class BaseAssetAdmin(admin.ModelAdmin):
    add_in_actions = True
    form = AssetAdminForm
    list_display = (
        "id",
        "name",
        "asset_type",
        "status",
        "vendor",
        "custodian",
        "updated_by",
        "updated_at",
    )
    list_filter = ("asset_type", "vendor")
    search_fields = ("name", "description", "custodian__username")
    list_select_related = ("asset_type", "vendor", "custodian", "updated_by")
    readonly_fields = ("created_by", "updated_by")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(
            pk__in=visible_assets(request.user).values("pk")
        ).select_related("asset_type", "vendor", "custodian", "updated_by")

    def get_exclude(self, request, obj=None):
        exclude = list(super().get_exclude(request, obj) or [])
        if getattr(self.model, "TYPE_NAME", None):
            exclude.append("asset_type")
        return exclude

    def save_model(self, request, obj, form, change):
        type_name = getattr(self.model, "TYPE_NAME", None)
        if type_name:
            obj.asset_type = AssetType.objects.get(name=type_name)
        if not obj.created_by_id:
            obj.created_by = request.user
        if change:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FTTB)
class FTTBAdmin(BaseAssetAdmin):
    pass


@admin.register(OLT)
class OLTAdmin(BaseAssetAdmin):
    pass
