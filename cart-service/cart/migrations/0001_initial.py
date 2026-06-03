from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('user_id', models.IntegerField(unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'cart_cart'},
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('product_id', models.IntegerField()),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('cart', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='cart.cart',
                )),
            ],
            options={'db_table': 'cart_item'},
        ),
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together={('cart', 'product_id')},
        ),
    ]
