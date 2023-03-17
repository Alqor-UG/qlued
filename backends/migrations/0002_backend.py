# Generated by Django 3.2.1 on 2022-01-10 10:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backends", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Backend",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, unique=True)),
                ("version", models.CharField(max_length=20)),
                (
                    "cold_atom_type",
                    models.CharField(
                        choices=[
                            ("fermion", "fermion"),
                            ("spin", "spin"),
                            ("boson", "boson"),
                        ],
                        max_length=15,
                    ),
                ),
                ("gates", models.JSONField(null=True)),
                ("max_experiments", models.IntegerField(default=1000)),
                ("max_shots", models.IntegerField(default=100000000)),
                ("simulator", models.BooleanField(default=True)),
                ("supported_instructions", models.JSONField(null=True)),
                (
                    "wire_order",
                    models.CharField(
                        choices=[
                            ("interleaved", "interleaved"),
                            ("sequential", "sequential"),
                        ],
                        max_length=15,
                    ),
                ),
                ("num_species", models.PositiveIntegerField(default=1)),
            ],
        ),
    ]
