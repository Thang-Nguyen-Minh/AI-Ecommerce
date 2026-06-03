from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.IntegerField(unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('status', models.CharField(
                    choices=[('Pending', 'Pending'), ('Success', 'Success'), ('Failed', 'Failed')],
                    default='Pending', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'payment',
                'ordering': ['-created_at'],
            },
        ),
    ]
