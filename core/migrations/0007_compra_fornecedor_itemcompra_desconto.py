from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_despesa'),
    ]

    operations = [
        migrations.AddField(
            model_name='compra',
            name='fornecedor',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='itemcompra',
            name='desconto_percentual',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='itemcompra',
            name='desconto_valor',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
