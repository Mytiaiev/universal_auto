from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0029_carefficiency_remove_client_role_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vehicle',
            name='driver',
        ),
        migrations.AddField(
            model_name='driver',
            name='vehicle',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.vehicle', verbose_name='Автомобіль'),
        ),
    ]