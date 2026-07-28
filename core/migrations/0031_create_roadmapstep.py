from django.db import migrations, models

class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('core', '0030_alter_clientprofile_deliverables_begin_status_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoadmapStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('DECLINED', 'Declined')], default='PENDING', max_length=20)),
                ('order', models.PositiveIntegerField(default=1)),
                ('client', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='roadmap_steps', to='auth.user')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
