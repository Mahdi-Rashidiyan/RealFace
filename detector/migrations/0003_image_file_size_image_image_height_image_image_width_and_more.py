# Generated by Django 5.1.2 on 2025-04-26 04:31

import detector.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('detector', '0002_alter_image_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='file_size',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='image',
            name='image_height',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='image',
            name='image_width',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='image',
            name='original_filename',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(help_text='Upload JPEG, PNG, or WebP images (max 10MB)', max_length=255, upload_to=detector.models.get_upload_path, validators=[detector.models.validate_image_file]),
        ),
    ]
