# Tracker

Django asset-tracking application for FTTB and OLT records.

## Configuration

The application reads secrets and deployment-specific values from environment variables. Do not commit real credentials or a production `DJANGO_SECRET_KEY` to Git.

Required:

- `DJANGO_SECRET_KEY`: a newly generated, random Django secret key.
- `TRACKER_DB_PASSWORD`: password for the PostgreSQL application account.

Common optional settings:

- `TRACKER_DB_NAME` (default: `tracker`)
- `TRACKER_DB_USER` (default: `tracker`)
- `TRACKER_DB_HOST` (default: `10.10.10.137`)
- `TRACKER_DB_PORT` (default: `5432`)
- `TRACKER_DB_CONN_MAX_AGE` (default: `60`)
- `DJANGO_DEBUG` (default: `False`; do not enable in production)
- `DJANGO_ALLOWED_HOSTS` (comma-separated host names; default includes `10.10.10.124,localhost,127.0.0.1`)
- `DJANGO_CSRF_TRUSTED_ORIGINS` (comma-separated full origins; default `http://10.10.10.124`)
- `DJANGO_TIME_ZONE` (default: `Asia/Manila`)
- `DJANGO_SECURE_COOKIES` (default: `False` for compatibility with the current HTTP URL; set to `1` after HTTPS is configured)
- `DJANGO_SECURE_SSL_REDIRECT` (default: `False`; enable only when HTTPS is correctly configured end-to-end)

Generate a new secret key in a trusted environment, for example:

```sh
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Provide the generated value and database password through your deployment secret store or protected environment file. Never paste secrets into source code, issue comments, or chat messages.

The default database host and URL prefix reflect the current deployment configuration; override them through environment variables when needed.

## Database migrations

The inventory migration history includes a follow-up migration that aligns the old initial schema with the current models. Apply migrations through your normal deployment process. If the legacy migration has already been applied, do not delete migration history or mark migrations as applied without checking the actual schema first.

## Record access

The web application filters assets using the user's group membership and custodian assignment; superusers and users in an Engineer-marked group can see all assets. These Django queryset rules do **not** provide PostgreSQL row-level security for a person connecting directly to PostgreSQL with SQL tools. Direct SQL access must be separately restricted through database roles and PostgreSQL policies/views, or denied to ordinary application users. Do not give end users the Django application's unrestricted database credentials.

## Tests

Run the Django test suite in an environment with the required settings and a test database configured:

```sh
python manage.py test inventory
```


## Asset attachments

The asset edit page supports adding and deleting multiple attachments per FTTB/OLT record; the read-only asset detail page lists attachments for download only. Attachment metadata is stored in PostgreSQL and file bytes are stored under `MEDIA_ROOT/asset_attachments/<asset-id>/`. Downloads go through an authenticated Django view that checks the user's asset visibility; files should **not** be exposed through a public static/media URL.

- Maximum 10 files per upload request.
- Maximum 20 MB per file (also configure Apache's request-body limit appropriately).
- Allowed extensions: PDF, common image formats, text/CSV, Office documents, ZIP, logs and configuration files.
- Users need the asset's change permission to upload/delete attachments.
- Back up `MEDIA_ROOT` separately from PostgreSQL.
- Ensure the Apache/Django service account can write to `MEDIA_ROOT`.
- Before deployment, review the migration history and run `python manage.py makemigrations --check --dry-run`, `python manage.py check`, and the test suite in the deployment environment.
