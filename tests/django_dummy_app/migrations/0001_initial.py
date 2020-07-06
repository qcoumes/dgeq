# Generated by Django 3.0.8 on 2020-08-19 15:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Continent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('area', models.BigIntegerField()),
                ('population', models.BigIntegerField()),
            ],
            options={
                'verbose_name_plural': 'Countries',
            },
        ),
        migrations.CreateModel(
            name='River',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('discharge', models.IntegerField(null=True)),
                ('length', models.IntegerField()),
                ('countries', models.ManyToManyField(related_name='rivers', to='django_dummy_app.Country')),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('continent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regions', to='django_dummy_app.Continent')),
            ],
        ),
        migrations.CreateModel(
            name='Mountain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('height', models.IntegerField()),
                ('countries', models.ManyToManyField(related_name='mountains', to='django_dummy_app.Country')),
            ],
        ),
        migrations.CreateModel(
            name='Forest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('area', models.BigIntegerField()),
                ('countries', models.ManyToManyField(related_name='forests', to='django_dummy_app.Country')),
            ],
        ),
        migrations.CreateModel(
            name='Disaster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(max_length=255)),
                ('date', models.DateTimeField()),
                ('source', models.TextField()),
                ('comment', models.TextField()),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='disasters', to='django_dummy_app.Country')),
            ],
        ),
        migrations.AddField(
            model_name='country',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='countries', to='django_dummy_app.Region'),
        ),
    ]
