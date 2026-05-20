from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Insumo(models.Model):
    id_insumo = models.AutoField(primary_key=True)
    nome_insumo = models.CharField(max_length=64)
    qtd_disponivel = models.IntegerField()
    und_medida = models.CharField(max_length=8)
    imagem = models.ImageField(upload_to='insumos/', null=True, blank=True)

    def __str__(self):
        return self.nome_insumo
    
    class Meta:
        db_table = 'insumo'

class Compra(models.Model):
    id_compra = models.AutoField(primary_key=True)
    nota_fiscal = models.CharField(max_length=48)
    fornecedor = models.CharField(max_length=128, blank=True, default='')
    data_nf = models.DateField()

    def total_compra(self):
        return sum(item.subtotal_com_desconto for item in self.itens.all())

    def total_bruto(self):
        return sum(item.subtotal_bruto for item in self.itens.all())

    def total_descontos(self):
        return sum(item.desconto_total for item in self.itens.all())

    class Meta:
        db_table = 'compra'

class Produto(models.Model):
    id_produto = models.AutoField(primary_key=True)
    nome_produto = models.CharField(max_length=64)
    qtd_disponivel = models.IntegerField()
    peso_cont = models.IntegerField()
    und_medida = models.CharField(max_length=20)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    imagem = models.ImageField(upload_to='produtos/', null=True, blank=True)

    def __str__(self):
        return self.nome_produto

    class Meta:
        db_table = 'produto'

class ItemCompra(models.Model):
    id_item_compra = models.AutoField(primary_key=True)
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, db_column='id_compra', related_name='itens')
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, db_column='id_insumo')
    qtd_item_compra = models.IntegerField()
    peso_cont = models.IntegerField()
    und_medida = models.CharField(max_length=8)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    desconto_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_validade = models.DateField(null=True, blank=True)

    @property
    def subtotal_bruto(self):
        return float(self.preco_unitario) * self.qtd_item_compra

    @property
    def desconto_total(self):
        bruto = self.subtotal_bruto
        d_perc = (bruto * float(self.desconto_percentual)) / 100
        return d_perc + float(self.desconto_valor)

    @property
    def subtotal_com_desconto(self):
        return max(self.subtotal_bruto - self.desconto_total, 0)

    @property
    def preco_unitario_final(self):
        if self.qtd_item_compra == 0:
            return 0
        return self.subtotal_com_desconto / self.qtd_item_compra

    class Meta:
        db_table = 'item_compra'

class Receita(models.Model):
    id_receita = models.AutoField(primary_key=True)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, db_column='id_produto')
    nome_receita = models.CharField(max_length=64)
    imagem = models.ImageField(upload_to='receitas/', null=True, blank=True)

    def __str__(self):
        return self.nome_receita

    class Meta:
        db_table = 'receita'

class ItemReceita(models.Model):
    id_item_receita = models.AutoField(primary_key=True)
    receita = models.ForeignKey(Receita, on_delete=models.CASCADE, db_column='id_receita', related_name='ingredientes')
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, db_column='id_insumo')
    qtd = models.IntegerField()
    medida_caseira = models.CharField(max_length=64)
    peso_cont = models.IntegerField()
    und_medida = models.CharField(max_length=8)

    class Meta:
        db_table = 'item_receita'

class Producao(models.Model):
    id_producao = models.AutoField(primary_key=True)
    receita = models.ForeignKey(Receita, on_delete=models.CASCADE, db_column='id_receita')
    # Qtd null indica produção pendente
    qtd_da_receita = models.IntegerField()
    qtd_produzida = models.IntegerField(null=True, blank=True) 
    data_inicio = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'producao'

class Venda(models.Model):
    METODOS_PAGAMENTO = [
        ('DINHEIRO', 'Dinheiro'),
        ('PIX', 'Pix'),
    ]
    id_venda = models.AutoField(primary_key=True)
    data_venda = models.DateTimeField(default=timezone.now)
    metodo_pagamento = models.CharField(
        max_length=10, 
        choices=METODOS_PAGAMENTO, 
        default='DINHEIRO'
    )

    def total_venda(self):
        # Calculado via itens
        total = sum(item.qtd * item.produto.preco_unitario for item in self.itens.all())
        return total

    class Meta:
        db_table = 'venda'

class ItemVenda(models.Model):
    id_item_venda = models.AutoField(primary_key=True)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, db_column='id_produto')
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, db_column='id_venda', related_name='itens')
    qtd = models.IntegerField()

    class Meta:
        db_table = 'item_venda'

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=ItemCompra)
def atualizar_estoque_compra(sender, instance, created, **kwargs):
    """
    Sempre que um item de compra é criado (created=True),
    adiciona a quantidade ao estoque do insumo.
    """
    if created:
        insumo = instance.insumo
        insumo.qtd_disponivel += instance.qtd_item_compra * instance.peso_cont
        insumo.save()

@receiver(post_delete, sender=ItemCompra)
def estornar_estoque_compra(sender, instance, **kwargs):
    """
    Se um item de compra for deletado, remove a quantidade do estoque.
    Isso é útil caso você tenha lançado errado e precise apagar.
    """
    insumo = instance.insumo
    insumo.qtd_disponivel -= instance.qtd_item_compra
    insumo.save()


class Despesa(models.Model):
    id_despesa = models.AutoField(primary_key=True)
    descricao = models.CharField(max_length=128)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField(default=timezone.now)

    def __str__(self):
        return self.descricao

    class Meta:
        db_table = 'despesa'

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='fotos/', null=True, blank=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def criar_perfil_automatico(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(user=instance)