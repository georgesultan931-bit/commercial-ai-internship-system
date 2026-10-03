from django.core.management.base import BaseCommand

from institutions.models import InstitutionProfile
from students.models import StudentProfile


class Command(BaseCommand):
    help = (
        "Backfill StudentProfile.institution_profile from the legacy "
        "StudentProfile.institution text field using safe case-insensitive "
        "institution-name matching."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply changes. Without this flag, the command runs in dry-run mode.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]

        students = (
            StudentProfile.objects
            .filter(institution_profile__isnull=True)
            .exclude(institution__exact="")
            .select_related("user")
            .order_by("id")
        )

        total_candidates = students.count()

        linked = 0
        unmatched = 0
        ambiguous = 0
        skipped = 0

        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Student Institution Backfill"
            )
        )

        if apply_changes:
            self.stdout.write(
                self.style.WARNING(
                    "MODE: APPLY - matching records will be updated."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "MODE: DRY RUN - no database records will be changed."
                )
            )

        self.stdout.write(
            f"Candidates without institution_profile: {total_candidates}"
        )
        self.stdout.write("")

        for student in students:
            legacy_name = (student.institution or "").strip()

            if not legacy_name:
                skipped += 1
                continue

            matches = list(
                InstitutionProfile.objects.filter(
                    institution_name__iexact=legacy_name
                ).order_by("id")
            )

            if len(matches) == 1:
                institution = matches[0]

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[MATCH] Student #{student.id} "
                        f"({student.user.username}) -> "
                        f"{institution.institution_name}"
                    )
                )

                linked += 1

                if apply_changes:
                    student.institution_profile = institution
                    student.save(
                        update_fields=[
                            "institution_profile",
                            "institution",
                            "full_name",
                        ]
                    )

            elif len(matches) == 0:
                unmatched += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"[UNMATCHED] Student #{student.id} "
                        f"({student.user.username}) | "
                        f'legacy institution="{legacy_name}"'
                    )
                )

            else:
                ambiguous += 1

                institution_ids = ", ".join(
                    str(item.id)
                    for item in matches
                )

                self.stdout.write(
                    self.style.ERROR(
                        f"[AMBIGUOUS] Student #{student.id} "
                        f"({student.user.username}) | "
                        f'legacy institution="{legacy_name}" | '
                        f"InstitutionProfile IDs: {institution_ids}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Backfill Summary"
            )
        )
        self.stdout.write(
            f"Candidates: {total_candidates}"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Matched: {linked}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"Unmatched: {unmatched}"
            )
        )
        self.stdout.write(
            self.style.ERROR(
                f"Ambiguous: {ambiguous}"
            )
        )
        self.stdout.write(
            f"Skipped: {skipped}"
        )

        if apply_changes:
            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS(
                    "Backfill completed. Matched student records were updated."
                )
            )
        else:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "Dry run completed. Review the results, then run again "
                    "with --apply to save matched records."
                )
            )
