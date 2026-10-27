from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q

from .access import is_engineer
from .models import (
    Asset,
    AssetType,
    TYPE_MODELS,
    default_status_for,
    status_options_for,
)

COMMON_FIELDS = (
    "name",
    "asset_type",
    "status",
    "vendor",
    "custodian",
    "description",
)


class AssetForm(forms.ModelForm):
    status = forms.ChoiceField(label="Status")

    class Meta:
        model = Asset
        fields = [
            "name",
            "asset_type",
            "status",
            "vendor",
            "custodian",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["asset_type"].queryset = AssetType.objects.filter(
            name__in=TYPE_MODELS
        )
        self.fields["asset_type"].required = True
        if self.instance is not None and self.instance.pk:
            self.fields["asset_type"].disabled = True

        is_eng = bool(
            user is not None and not user.is_superuser and is_engineer(user)
        )
        current_vendor_id = (
            self.instance.vendor_id
            if self.instance is not None and self.instance.pk
            else None
        )

        vendor_ids = set(
            Group.objects.filter(profile__is_vendor=True).values_list("pk", flat=True)
        )
        if current_vendor_id:
            vendor_ids.add(current_vendor_id)
        if user is not None and not user.is_superuser and not is_eng:
            vendor_ids = set(
                user.groups.filter(profile__is_vendor=True).values_list("pk", flat=True)
            )
            if current_vendor_id:
                vendor_ids.add(current_vendor_id)
        self.fields["vendor"].queryset = Group.objects.filter(pk__in=vendor_ids)

        if user is not None and not user.is_superuser:
            custodian_qs = (
                get_user_model()
                .objects.filter(Q(groups__in=user.groups.all()) | Q(pk=user.pk))
                .distinct()
            )
            if is_eng:
                custodian_qs = get_user_model().objects.all()
            elif (
                self.instance is not None
                and self.instance.pk
                and self.instance.custodian_id
            ):
                custodian_qs = get_user_model().objects.filter(
                    Q(pk=self.instance.custodian_id)
                    | Q(pk__in=custodian_qs.values("pk"))
                )
            self.fields["custodian"].queryset = custodian_qs

        self.type_obj = self._resolve_type()
        self.fields["status"].choices = status_options_for(self.type_obj)
        if not self.is_bound:
            allowed = {key for key, _ in self.fields["status"].choices}
            current = self.initial.get("status")
            if current is None and self.instance is not None and self.instance.pk:
                current = self.instance.status
            if not current or current not in allowed:
                self.fields["status"].initial = default_status_for(self.type_obj)

    def _resolve_type(self):
        if self.is_bound:
            raw = self.data.get("asset_type")
        else:
            raw = self.initial.get("asset_type")
            if raw is None and self.instance is not None:
                raw = self.instance.asset_type_id
        if not raw:
            return None
        return AssetType.objects.filter(pk=raw).first()

    def save(self, commit=True):
        if self.instance is not None and self.instance.pk:
            asset = super().save(commit=False)
            if commit:
                asset.save()
                self.save_m2m()
            return asset

        data = self.cleaned_data
        model = TYPE_MODELS.get(data["asset_type"].name)
        if model is None:
            return super().save(commit=commit)

        child = model()
        for name in COMMON_FIELDS:
            setattr(child, name, data[name])
        if commit:
            child.save()
            self.save_m2m()
        return child