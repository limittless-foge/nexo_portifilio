from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_phonenumber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientprofile',
            name='deliverables_begin_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('DECLINED', 'Declined / Restricted')], default='PENDING', help_text='Status of the deliverables beginning step', max_length=20),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='kickoff_call_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('DECLINED', 'Declined / Restricted')], default='PENDING', help_text='Status of the kickoff call step', max_length=20),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='services_selected_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('DECLINED', 'Declined / Restricted')], default='PENDING', help_text='Status of the services selection step', max_length=20),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='team_assignment_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('DECLINED', 'Declined / Restricted')], default='PENDING', help_text='Status of the team assignment step', max_length=20),
        ),
    ]
