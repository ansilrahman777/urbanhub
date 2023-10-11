# Generated by Django 4.2.4 on 2023-10-10 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0027_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Order Placed', 'Order Placed'), ('Accepted', 'Accepted'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled'), ('Return Pending', 'Return Pending'), ('Returned', 'Returned'), ('Payment Failed', 'Payment Failed'), ('Order Failed', 'Order Failed')], default='Order Placed', max_length=20),
        ),
    ]
