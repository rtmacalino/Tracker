from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase

from .access import visible_assets
from .models import Asset, AssetAttachment, GroupProfile


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



class AssetAttachmentTests(VisibleAssetsTests):
    def test_superuser_can_upload_and_download_attachment(self):
        self.client.force_login(self.admin_user)
        upload = SimpleUploadedFile(
            "site-photo.jpg", b"test image bytes", content_type="image/jpeg"
        )
        response = self.client.post(
            reverse("inventory:asset_attachment_upload", args=[self.vendor_asset.pk]),
            {"files": [upload]},
        )
        self.assertRedirects(response, self.vendor_asset.get_absolute_url())
        attachment = AssetAttachment.objects.get(asset=self.vendor_asset)
        self.assertEqual(attachment.original_name, "site-photo.jpg")
        self.assertEqual(attachment.file_size, len(b"test image bytes"))

        response = self.client.get(
            reverse(
                "inventory:asset_attachment_download",
                args=[self.vendor_asset.pk, attachment.pk],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"test image bytes")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_disallowed_file_extension_is_rejected(self):
        self.client.force_login(self.admin_user)
        upload = SimpleUploadedFile("program.exe", b"not allowed")
        response = self.client.post(
            reverse("inventory:asset_attachment_upload", args=[self.vendor_asset.pk]),
            {"files": [upload]},
        )
        self.assertRedirects(response, self.vendor_asset.get_absolute_url())
        self.assertFalse(AssetAttachment.objects.filter(asset=self.vendor_asset).exists())

    def test_user_cannot_download_attachment_for_invisible_asset(self):
        attachment = AssetAttachment.objects.create(
            asset=self.other_asset,
            file=SimpleUploadedFile("report.pdf", b"private bytes"),
            original_name="report.pdf",
            file_size=len(b"private bytes"),
            uploaded_by=self.other_user,
        )
        self.client.force_login(self.vendor_user)
        response = self.client.get(
            reverse(
                "inventory:asset_attachment_download",
                args=[self.other_asset.pk, attachment.pk],
            )
        )
        self.assertEqual(response.status_code, 404)


    def test_view_record_only_displays_downloads_not_management_controls(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("inventory:asset_detail", args=[self.vendor_asset.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Attachments")
        self.assertNotContains(response, "Upload attachments")
        self.assertNotContains(response, "Delete attachment")

    def test_edit_record_displays_attachment_management_controls(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("inventory:asset_edit", args=[self.vendor_asset.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add files")
        self.assertContains(response, "Upload attachments")
        self.assertContains(response, "Delete attachment")

    def test_attachment_management_returns_to_edit_record_when_requested(self):
        self.client.force_login(self.admin_user)
        upload = SimpleUploadedFile("report.pdf", b"report bytes")
        response = self.client.post(
            reverse("inventory:asset_attachment_upload", args=[self.vendor_asset.pk]),
            {"files": [upload], "return_to": "edit"},
        )
        self.assertRedirects(
            response,
            reverse("inventory:asset_edit", args=[self.vendor_asset.pk]),
        )
