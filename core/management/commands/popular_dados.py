from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from core.models import (
    Insumo, Compra, ItemCompra, Produto, Receita, ItemReceita,
    Producao, Venda, ItemVenda
)


class Command(BaseCommand):
    help = 'Popula o banco com dados de exemplo para biscoitos APAE'

    def handle(self, *args, **kwargs):
        self.stdout.write('Limpando dados anteriores...')
        ItemVenda.objects.all().delete()
        Venda.objects.all().delete()
        Producao.objects.all().delete()
        ItemReceita.objects.all().delete()
        Receita.objects.all().delete()
        ItemCompra.objects.all().delete()
        Compra.objects.all().delete()
        Produto.objects.all().delete()
        Insumo.objects.all().delete()

        # ── INSUMOS ──────────────────────────────────────────────────────────
        self.stdout.write('Criando insumos...')
        farinha = Insumo.objects.create(nome_insumo='Farinha de Trigo', qtd_disponivel=0, und_medida='g')
        acucar = Insumo.objects.create(nome_insumo='Açúcar Refinado', qtd_disponivel=0, und_medida='g')
        manteiga = Insumo.objects.create(nome_insumo='Manteiga', qtd_disponivel=0, und_medida='g')
        ovos = Insumo.objects.create(nome_insumo='Ovos', qtd_disponivel=0, und_medida='un')
        leite = Insumo.objects.create(nome_insumo='Leite em Pó', qtd_disponivel=0, und_medida='g')
        chocolate = Insumo.objects.create(nome_insumo='Chocolate em Pó', qtd_disponivel=0, und_medida='g')
        canela = Insumo.objects.create(nome_insumo='Canela em Pó', qtd_disponivel=0, und_medida='g')
        fermento = Insumo.objects.create(nome_insumo='Fermento Químico', qtd_disponivel=0, und_medida='g')
        coco = Insumo.objects.create(nome_insumo='Coco Ralado', qtd_disponivel=0, und_medida='g')
        amendoim = Insumo.objects.create(nome_insumo='Amendoim Torrado', qtd_disponivel=0, und_medida='g')
        sal = Insumo.objects.create(nome_insumo='Sal', qtd_disponivel=0, und_medida='g')
        essencia = Insumo.objects.create(nome_insumo='Essência de Baunilha', qtd_disponivel=0, und_medida='ml')
        embalagem = Insumo.objects.create(nome_insumo='Embalagem Plástica 200g', qtd_disponivel=0, und_medida='un')

        # ── COMPRAS ───────────────────────────────────────────────────────────
        self.stdout.write('Criando compras...')
        hoje = date.today()

        c1 = Compra.objects.create(nota_fiscal='NF-2026-001', data_nf=hoje - timedelta(days=60))
        ItemCompra.objects.create(compra=c1, insumo=farinha,    qtd_item_compra=10, peso_cont=1000, und_medida='g', preco_unitario=Decimal('5.90'),  data_validade=hoje + timedelta(days=180))
        ItemCompra.objects.create(compra=c1, insumo=acucar,     qtd_item_compra=5,  peso_cont=1000, und_medida='g', preco_unitario=Decimal('4.50'),  data_validade=hoje + timedelta(days=365))
        ItemCompra.objects.create(compra=c1, insumo=manteiga,   qtd_item_compra=3,  peso_cont=500,  und_medida='g', preco_unitario=Decimal('9.80'),  data_validade=hoje + timedelta(days=60))
        ItemCompra.objects.create(compra=c1, insumo=ovos,       qtd_item_compra=60, peso_cont=1,    und_medida='un', preco_unitario=Decimal('0.85'), data_validade=hoje + timedelta(days=30))
        ItemCompra.objects.create(compra=c1, insumo=embalagem,  qtd_item_compra=200, peso_cont=1,   und_medida='un', preco_unitario=Decimal('0.40'))

        c2 = Compra.objects.create(nota_fiscal='NF-2026-002', data_nf=hoje - timedelta(days=30))
        ItemCompra.objects.create(compra=c2, insumo=chocolate,  qtd_item_compra=3,  peso_cont=500,  und_medida='g', preco_unitario=Decimal('12.00'), data_validade=hoje + timedelta(days=240))
        ItemCompra.objects.create(compra=c2, insumo=leite,      qtd_item_compra=4,  peso_cont=400,  und_medida='g', preco_unitario=Decimal('11.50'), data_validade=hoje + timedelta(days=300))
        ItemCompra.objects.create(compra=c2, insumo=fermento,   qtd_item_compra=5,  peso_cont=100,  und_medida='g', preco_unitario=Decimal('3.20'),  data_validade=hoje + timedelta(days=365))
        ItemCompra.objects.create(compra=c2, insumo=sal,        qtd_item_compra=2,  peso_cont=1000, und_medida='g', preco_unitario=Decimal('2.50'),  data_validade=hoje + timedelta(days=730))
        ItemCompra.objects.create(compra=c2, insumo=essencia,   qtd_item_compra=3,  peso_cont=30,   und_medida='ml', preco_unitario=Decimal('6.00'), data_validade=hoje + timedelta(days=365))

        c3 = Compra.objects.create(nota_fiscal='NF-2026-003', data_nf=hoje - timedelta(days=10))
        ItemCompra.objects.create(compra=c3, insumo=coco,       qtd_item_compra=4,  peso_cont=100,  und_medida='g', preco_unitario=Decimal('7.50'),  data_validade=hoje + timedelta(days=120))
        ItemCompra.objects.create(compra=c3, insumo=amendoim,   qtd_item_compra=3,  peso_cont=500,  und_medida='g', preco_unitario=Decimal('8.90'),  data_validade=hoje + timedelta(days=150))
        ItemCompra.objects.create(compra=c3, insumo=canela,     qtd_item_compra=2,  peso_cont=50,   und_medida='g', preco_unitario=Decimal('4.50'),  data_validade=hoje + timedelta(days=365))
        ItemCompra.objects.create(compra=c3, insumo=farinha,    qtd_item_compra=15, peso_cont=1000, und_medida='g', preco_unitario=Decimal('5.70'),  data_validade=hoje + timedelta(days=180))
        ItemCompra.objects.create(compra=c3, insumo=acucar,     qtd_item_compra=8,  peso_cont=1000, und_medida='g', preco_unitario=Decimal('4.30'),  data_validade=hoje + timedelta(days=365))

        # ── PRODUTOS ──────────────────────────────────────────────────────────
        self.stdout.write('Criando produtos...')
        p_choc = Produto.objects.create(nome_produto='Biscoito de Chocolate', qtd_disponivel=0, peso_cont=200, und_medida='g', preco_unitario=Decimal('12.00'))
        p_coco = Produto.objects.create(nome_produto='Biscoito de Coco',      qtd_disponivel=0, peso_cont=200, und_medida='g', preco_unitario=Decimal('10.00'))
        p_man  = Produto.objects.create(nome_produto='Biscoito de Amendoim',  qtd_disponivel=0, peso_cont=200, und_medida='g', preco_unitario=Decimal('11.00'))
        p_can  = Produto.objects.create(nome_produto='Biscoito de Canela',    qtd_disponivel=0, peso_cont=200, und_medida='g', preco_unitario=Decimal('10.00'))
        p_bau  = Produto.objects.create(nome_produto='Biscoito de Baunilha',  qtd_disponivel=0, peso_cont=200, und_medida='g', preco_unitario=Decimal('10.00'))

        # ── RECEITAS ──────────────────────────────────────────────────────────
        self.stdout.write('Criando receitas...')

        r_choc = Receita.objects.create(produto=p_choc, nome_receita='Biscoito de Chocolate')
        ItemReceita.objects.create(receita=r_choc, insumo=farinha,   qtd=250, medida_caseira='2 xícaras',   peso_cont=1000, und_medida='g')
        ItemReceita.objects.create(receita=r_choc, insumo=acucar,    qtd=100, medida_caseira='½ xícara',    peso_cont=1000, und_medida='g')
        ItemReceita.objects.create(receita=r_choc, insumo=chocolate, qtd=50,  medida_caseira='3 col. sopa', peso_cont=500,  und_medida='g')
        ItemReceita.objects.create(receita=r_choc, insumo=manteiga,  qtd=80,  medida_caseira='4 col. sopa', peso_cont=500,  und_medida='g')
        ItemReceita.objects.create(receita=r_choc, insumo=ovos,      qtd=2,   medida_caseira='2 unidades',  peso_cont=1,    und_medida='un')
        ItemReceita.objects.create(receita=r_choc, insumo=fermento,  qtd=5,   medida_caseira='1 col. chá',  peso_cont=100,  und_medida='g')
        ItemReceita.objects.create(receita=r_choc, insumo=sal,       qtd=2,   medida_caseira='1 pitada',    peso_cont=1000, und_medida='g')

        r_coco = Receita.objects.create(produto=p_coco, nome_receita='Biscoito de Coco')
        ItemReceita.objects.create(receita=r_coco, insumo=farinha,  qtd=250, medida_caseira='2 xícaras',   peso_cont=1000, und_medida='g')
        ItemReceita.objects.create(receita=r_coco, insumo=acucar,   qtd=80,  medida_caseira='⅓ xícara',    peso_cont=1000, und_medida='g')
        ItemReceita.objects.create(receita=r_coco, insumo=coco,     qtd=100, medida_caseira='1 xícara',    peso_cont=100,  und_medida='g')
        ItemReceita.objects.create(receita=r_coco, insumo=manteiga, qtd=80,  medida_caseira='4 col. sopa', peso_cont=500,  und_medida='g')
        ItemReceita.objects.create(receita=r_coco, insumo=ovos,     qtd=2,   medida_caseira='2 unidades',  peso_cont=1,    und_medida='un')
        ItemReceita.objects.create(receita=r_coco, insumo=leite,    qtd=40,  medida_caseira='2 col. sopa', peso_cont=400,  und_medida='g')
        ItemReceita.objects.create(receita=r_coco, insumo=fermento, qtd=5,   medida_caseira='1 col. chá',  peso_cont=100,  und_medida='g')

        r_man = Receita.objects.create(produto=p_man, nome_receita='Biscoito de Amendoim')
        ItemReceita.objects.create(receita=r_man, insumo=farinha,   qtd=200, medida_caseira='1½ xícara',   peso_cont=1000, und_medida='g')
        ItemReceita.objects.create(receita=r_man, insumo=acucar,    qtd=100, medida_caseira='½ xícara',    peso_cont=1000, und_medida='g')
        ItemReceita.objects.create(receita=r_man, insumo=amendoim,  qtd=150, medida_caseira='1 xícara',    peso_cont=500,  und_medida='g')
        ItemReceita.objects.create(receita=r_man, insumo=manteiga,  qtd=60,  medida_caseira='3 col. sopa', peso_cont=500,  und_medida='g')
        ItemReceita.objects.create(receita=r_man, insumo=ovos,      qtd=2,   medida_caseira='2 unidades',  peso_cont=1,    und_medida='un')
        ItemReceita.objects.create(receita=r_man, insumo=fermento,  qtd=5,   medida_caseira='1 col. chá',  peso_cont=100,  und_medida='g')
        ItemReceita.objects.create(receita=r_man, insumo=sal,       qtd=2,   medida_caseira='1 pitada',    peso_cont=1000, und_medida='g')

        r_can = Receita.objects.create(produto=p_can, nome_receita='Biscoito de Canela')
        ItemReceita.objects.create(receita=r_can, insumo=farinha,  qtd=250, medida_caseira='2 xícaras',   peso_cont=1000, und_medida='g')
        ItemReceita.objects.create(receita=r_can, insumo=acucar,   qtd=90,  medida_caseira='½ xícara',    peso_cont=1000, und_medida='g')
        ItemReceita.objects.create(receita=r_can, insumo=canela,   qtd=10,  medida_caseira='1 col. sopa', peso_cont=50,   und_medida='g')
        ItemReceita.objects.create(receita=r_can, insumo=manteiga, qtd=80,  medida_caseira='4 col. sopa', peso_cont=500,  und_medida='g')
        ItemReceita.objects.create(receita=r_can, insumo=ovos,     qtd=2,   medida_caseira='2 unidades',  peso_cont=1,    und_medida='un')
        ItemReceita.objects.create(receita=r_can, insumo=leite,    qtd=30,  medida_caseira='2 col. sopa', peso_cont=400,  und_medida='g')
        ItemReceita.objects.create(receita=r_can, insumo=fermento, qtd=5,   medida_caseira='1 col. chá',  peso_cont=100,  und_medida='g')

        r_bau = Receita.objects.create(produto=p_bau, nome_receita='Biscoito de Baunilha')
        ItemReceita.objects.create(receita=r_bau, insumo=farinha,  qtd=250, medida_caseira='2 xícaras',   peso_cont=1000, und_medida='g')
        ItemReceita.objects.create(receita=r_bau, insumo=acucar,   qtd=100, medida_caseira='½ xícara',    peso_cont=1000, und_medida='g')
        ItemReceita.objects.create(receita=r_bau, insumo=essencia, qtd=10,  medida_caseira='2 col. chá',  peso_cont=30,   und_medida='ml')
        ItemReceita.objects.create(receita=r_bau, insumo=manteiga, qtd=80,  medida_caseira='4 col. sopa', peso_cont=500,  und_medida='g')
        ItemReceita.objects.create(receita=r_bau, insumo=ovos,     qtd=2,   medida_caseira='2 unidades',  peso_cont=1,    und_medida='un')
        ItemReceita.objects.create(receita=r_bau, insumo=leite,    qtd=40,  medida_caseira='2 col. sopa', peso_cont=400,  und_medida='g')
        ItemReceita.objects.create(receita=r_bau, insumo=fermento, qtd=5,   medida_caseira='1 col. chá',  peso_cont=100,  und_medida='g')
        ItemReceita.objects.create(receita=r_bau, insumo=sal,      qtd=2,   medida_caseira='1 pitada',    peso_cont=1000, und_medida='g')

        # ── PRODUÇÕES ─────────────────────────────────────────────────────────
        self.stdout.write('Criando produções...')
        prod_data = [
            (r_choc, p_choc, hoje - timedelta(days=45), 3, 30),
            (r_coco, p_coco, hoje - timedelta(days=40), 2, 20),
            (r_man,  p_man,  hoje - timedelta(days=35), 2, 18),
            (r_can,  p_can,  hoje - timedelta(days=28), 3, 28),
            (r_bau,  p_bau,  hoje - timedelta(days=20), 2, 22),
            (r_choc, p_choc, hoje - timedelta(days=15), 4, 38),
            (r_coco, p_coco, hoje - timedelta(days=10), 3, 29),
            (r_man,  p_man,  hoje - timedelta(days=5),  2, None),
            (r_bau,  p_bau,  hoje - timedelta(days=2),  3, None),
        ]
        for receita, produto, data, qtd_rec, qtd_prod in prod_data:
            prod = Producao(
                receita=receita,
                qtd_da_receita=qtd_rec,
                data_inicio=timezone.make_aware(
                    timezone.datetime.combine(data, timezone.datetime.min.time())
                ),
            )
            if qtd_prod is not None:
                prod.qtd_produzida = qtd_prod
                produto.qtd_disponivel += qtd_prod
                produto.save()
            prod.save()

        # ── VENDAS ────────────────────────────────────────────────────────────
        self.stdout.write('Criando vendas...')
        vendas_data = [
            (hoje - timedelta(days=42), 'DINHEIRO', [(p_choc, 3), (p_coco, 2)]),
            (hoje - timedelta(days=38), 'PIX',      [(p_man, 4)]),
            (hoje - timedelta(days=35), 'DINHEIRO', [(p_choc, 2), (p_can, 3)]),
            (hoje - timedelta(days=30), 'PIX',      [(p_bau, 5), (p_coco, 2)]),
            (hoje - timedelta(days=25), 'DINHEIRO', [(p_choc, 6)]),
            (hoje - timedelta(days=20), 'PIX',      [(p_man, 3), (p_can, 2)]),
            (hoje - timedelta(days=18), 'DINHEIRO', [(p_bau, 4), (p_choc, 2)]),
            (hoje - timedelta(days=14), 'PIX',      [(p_coco, 5), (p_man, 2)]),
            (hoje - timedelta(days=10), 'DINHEIRO', [(p_can, 3), (p_bau, 3)]),
            (hoje - timedelta(days=7),  'PIX',      [(p_choc, 4), (p_coco, 3)]),
            (hoje - timedelta(days=5),  'DINHEIRO', [(p_man, 5)]),
            (hoje - timedelta(days=3),  'PIX',      [(p_bau, 6), (p_can, 2)]),
            (hoje - timedelta(days=1),  'DINHEIRO', [(p_choc, 3), (p_man, 2)]),
            (hoje,                      'PIX',      [(p_coco, 4), (p_bau, 2)]),
        ]
        for data_v, metodo, itens in vendas_data:
            venda = Venda.objects.create(
                data_venda=timezone.make_aware(
                    timezone.datetime.combine(data_v, timezone.datetime.min.time())
                ),
                metodo_pagamento=metodo,
            )
            for produto, qtd in itens:
                ItemVenda.objects.create(venda=venda, produto=produto, qtd=qtd)
                produto.qtd_disponivel = max(0, produto.qtd_disponivel - qtd)
                produto.save()

        self.stdout.write(self.style.SUCCESS('\nDados populados com sucesso!'))
        self.stdout.write(f'  {Insumo.objects.count()} insumos')
        self.stdout.write(f'  {Compra.objects.count()} compras  ({ItemCompra.objects.count()} itens)')
        self.stdout.write(f'  {Produto.objects.count()} produtos')
        self.stdout.write(f'  {Receita.objects.count()} receitas ({ItemReceita.objects.count()} ingredientes)')
        self.stdout.write(f'  {Producao.objects.count()} produções ({Producao.objects.filter(qtd_produzida__isnull=False).count()} finalizadas)')
        self.stdout.write(f'  {Venda.objects.count()} vendas   ({ItemVenda.objects.count()} itens)')
