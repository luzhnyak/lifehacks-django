# Django maintenance review — 2026-11-10

Scope: correct demonstrated bugs and deployment risks, preserve existing post
URLs and database contents. No deployment or production database changes.

1. Add regression tests for missing posts, category URLs, filtered pagination,
   stable ordering, slug edge cases, image handling and homepage query growth.
2. Remove duplicate models; share bounded slug generation; process new images
   before saving through Django storage rather than local filesystem signals.
3. Correct views and templates; prefetch only four posts per homepage category.
4. Read deployment secrets and flags from the environment, default to production
   safety, separate collected static files from uploads and source assets.
5. Update Django to the supported 5.2 LTS line, add the missing image migration,
   document setup and server migration steps, and add CI checks before deployment.

Verification: first reproduce regressions, then run the full Django test suite,
system checks, migration drift checks and production deployment checks. Use a
temporary test database and media directory; do not migrate the local database.

Review focus: existing slugs remain stable; long or punctuation-only names do
not produce invalid generated slugs; category filters survive all page links;
unchanged images are not re-encoded; production cannot start without a secret.
