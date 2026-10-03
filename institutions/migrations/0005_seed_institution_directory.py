from django.db import migrations


INSTITUTIONS = [('Africa Nazarene University', 'university', 'Kajiado'), ('Baringo National Polytechnic', 'polytechnic', 'Baringo'), ('Catholic University of Eastern Africa', 'university', 'Nairobi'), ('Chuka University', 'university', 'Tharaka Nithi'), ('Daystar University', 'university', 'Machakos'), ('Dedan Kimathi University of Technology', 'university', 'Nyeri'), ('Egerton University', 'university', 'Nakuru'), ('Eldoret National Polytechnic', 'polytechnic', 'Uasin Gishu'), ('Embu University', 'university', 'Embu'), ('Great Lakes University of Kisumu', 'university', 'Kisumu'), ('Jaramogi Oginga Odinga University of Science and Technology', 'university', 'Siaya'), ('Jomo Kenyatta University of Agriculture and Technology', 'university', 'Kiambu'), ('KCA University', 'university', 'Nairobi'), ('Kabarak University', 'university', 'Nakuru'), ('Kabete National Polytechnic', 'polytechnic', 'Nairobi'), ('Karatina University', 'university', 'Nyeri'), ('Kenya Coast National Polytechnic', 'polytechnic', 'Mombasa'), ('Kenyatta University', 'university', 'Nairobi'), ('Kibabii University', 'university', 'Bungoma'), ('Kirinyaga University', 'university', 'Kirinyaga'), ('Kisii National Polytechnic', 'polytechnic', 'Kisii'), ('Kisii University', 'university', 'Kisii'), ('Kisumu National Polytechnic', 'polytechnic', 'Kisumu'), ('Laikipia University', 'university', 'Laikipia'), ('Maasai Mara University', 'university', 'Narok'), ('Machakos University', 'university', 'Machakos'), ('Maseno University', 'university', 'Kisumu'), ('Masinde Muliro University of Science and Technology', 'university', 'Kakamega'), ('Meru National Polytechnic', 'polytechnic', 'Meru'), ('Meru University of Science and Technology', 'university', 'Meru'), ('Moi University', 'university', 'Uasin Gishu'), ('Mount Kenya University', 'university', 'Kiambu'), ('Multimedia University of Kenya', 'university', 'Nairobi'), ('North Eastern National Polytechnic', 'polytechnic', 'Garissa'), ('Pwani University', 'university', 'Kilifi'), ('Riara University', 'university', 'Nairobi'), ('Rift Valley National Polytechnic', 'polytechnic', 'Nakuru'), ('Rongo University', 'university', 'Migori'), ('Sigalagala National Polytechnic', 'polytechnic', 'Kakamega'), ('South Eastern Kenya University', 'university', 'Kitui'), ("St. Paul's University", 'university', 'Kiambu'), ('Strathmore University', 'university', 'Nairobi'), ('Technical University of Kenya', 'university', 'Nairobi'), ('Technical University of Mombasa', 'university', 'Mombasa'), ('United States International University Africa', 'university', 'Nairobi'), ('University of Eldoret', 'university', 'Uasin Gishu'), ('University of Embu', 'university', 'Embu'), ('University of Nairobi', 'university', 'Nairobi'), ('Zetech University', 'university', 'Kiambu')]


def seed_institutions(apps, schema_editor):
    InstitutionDirectory = apps.get_model(
        "institutions",
        "InstitutionDirectory",
    )

    for name, institution_type, county in INSTITUTIONS:
        InstitutionDirectory.objects.update_or_create(
            name=name,
            defaults={
                "institution_type": institution_type,
                "county": county,
                "is_active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("institutions", "0004_institution_directory"),
    ]

    operations = [
        migrations.RunPython(
            seed_institutions,
            migrations.RunPython.noop,
        ),
    ]
