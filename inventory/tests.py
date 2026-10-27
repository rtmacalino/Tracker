import tempfile
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Asset, AssetAttachment, AssetType


class AssetAttachmentWorkflowTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)
        override = override_settings(MEDIA_ROOT=self.temp_media.name)
        override.enable()
        self.addCleanup(override.disable)
        self.user = get_user_model().objects.create_superuser(username="attach-admin", email="admin@example.invalid", password="test-password")
        self.client.force_login(self.user)
        self.asset_type, _ = AssetType.objects.get_or_create(name="FTTB")
        self.asset = Asset.objects.create(name="Test record", asset_type=self.asset_type)

    def upload(self, name="report.pdf", content=b"sample file"):
        return self.client.post(reverse("inventory:asset_attachment_upload", args=[self.asset.pk]), {"files": [SimpleUploadedFile(name, content)]})

    def test_multiple_files_upload(self):
        response = self.client.post(reverse("inventory:asset_attachment_upload", args=[self.asset.pk]), {"files": [SimpleUploadedFile("one.pdf", b"1"), SimpleUploadedFile("two.txt", b"2")]})
        self.assertRedirects(response, reverse("inventory:asset_edit", args=[self.asset.pk]))
        self.assertEqual(AssetAttachment.objects.filter(asset=self.asset).count(), 2)

    def test_download_has_security_headers(self):
        self.upload()
        a = AssetAttachment.objects.get(asset=self.asset)
        response = self.client.get(reverse("inventory:asset_attachment_download", args=[self.asset.pk, a.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(b"".join(response.streaming_content), b"sample file")

    def test_disallowed_extension_is_rejected(self):
        self.upload("unsafe.html", b"<script></script>")
        self.assertFalse(AssetAttachment.objects.filter(asset=self.asset).exists())

    def test_delete_is_post_only_and_removes_file(self):
        self.upload()
        a = AssetAttachment.objects.get(asset=self.asset)
        path = Path(self.temp_media.name, a.file.name)
        self.assertEqual(self.client.get(reverse("inventory:asset_attachment_delete", args=[self.asset.pk, a.pk])).status_code, 405)
        response = self.client.post(reverse("inventory:asset_attachment_delete", args=[self.asset.pk, a.pk]))
        self.assertRedirects(response, reverse("inventory:asset_edit", args=[self.asset.pk]))
        self.assertFalse(AssetAttachment.objects.filter(pk=a.pk).exists())
        self.assertFalse(path.exists())

    def test_attachment_is_scoped_to_its_record(self):
        self.upload()
        a = AssetAttachment.objects.get(asset=self.asset)
        other = Asset.objects.create(name="Other record", asset_type=self.asset_type)
        response = self.client.get(reverse("inventory:asset_attachment_download", args=[other.pk, a.pk]))
        self.assertEqual(response.status_code, 404)

    def test_view_record_has_download_only(self):
        self.upload()
        response = self.client.get(reverse("inventory:asset_detail", args=[self.asset.pk]))
        self.assertContains(response, "Download")
        self.assertNotContains(response, "Upload attachments")
