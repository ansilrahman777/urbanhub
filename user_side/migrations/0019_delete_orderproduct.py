# Generated by Django 4.2.4 on 2023-09-27 20:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0018_orderproduct_delete_orderproducts'),
    ]

    operations = [
        migrations.DeleteModel(
            name='OrderProduct',
        ),
    ]
