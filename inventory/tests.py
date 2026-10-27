from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.test import TestCase

from .access import visible_assets
from .models import Asset, GroupProfile


class VisibleAssetsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.vendor_group = Group.objects.create(name="Vendor A")
        GroupProfile.objects.create(group=cls.vendor_group, is_vendor=True)
        cls.other_group = Group.objects.create(name="Vendor B")
        GroupProfile.objects.create(group=cls.other_group, is_vendor=True)

        cls.vendor_user = User.objects.create_user(
            username="vendor-user", password="test-password-123"
        )
        cls.vendor_user.groups.add(cls.vendor_group)
        cls.other_user = User.objects.create_user(
            username="other-user", password="test-password-123"
        )
        cls.engineer_group = Group.objects.create(name="Engineers")
        GroupProfile.objects.create(group=cls.engineer_group, is_engineer=True)
        cls.engineer_user = User.objects.create_user(
            username="engineer-user", password="test-password-123"
        )
        cls.engineer_user.groups.add(cls.engineer_group)
        cls.admin_user = User.objects.create_superuser(
            username="admin-user", email="admin@example.invalid", password="test-password-123"
        )

        cls.vendor_asset = Asset.objects.create(
            name="Vendor A asset", vendor=cls.vendor_group
        )
        cls.custodian_asset = Asset.objects.create(
            name="Custodian asset", custodian=cls.vendor_user
        )
        cls.other_asset = Asset.objects.create(
            name="Vendor B asset", vendor=cls.other_group
        )
        cls.unassigned_asset = Asset.objects.create(name="Unassigned asset")

    def test_anonymous_user_sees_no_assets(self):
        self.assertFalse(visible_assets(AnonymousUser()).exists())

    def test_user_sees_assets_for_their_group_and_their_own_custody(self):
        visible_ids = set(
            visible_assets(self.vendor_user).values_list("pk", flat=True)
        )
        self.assertEqual(
            visible_ids,
            {self.vendor_asset.pk, self.custodian_asset.pk},
        )

    def test_engineer_sees_all_assets(self):
        self.assertSetEqual(
            set(visible_assets(self.engineer_user).values_list("pk", flat=True)),
            {
                self.vendor_asset.pk,
                self.custodian_asset.pk,
                self.other_asset.pk,
                self.unassigned_asset.pk,
            },
        )

    def test_superuser_sees_all_assets(self):
        self.assertEqual(visible_assets(self.admin_user).count(), 4)
