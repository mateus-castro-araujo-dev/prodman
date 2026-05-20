import requests
import random
from io import BytesIO
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from core.models import (
    Insumo, Produto, Receita, ItemReceita,
    Compra, ItemCompra, Producao, Venda, ItemVenda, Despesa
)


IMAGENS = {
    'farinha':    'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400&q=80',
    'ovo':        'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400&q=80',
    'chocolate':  'https://images.unsplash.com/photo-1606312619070-d48b4c652a52?w=400&q=80',
    'manteiga':   'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400&q=80',
    'leite':      'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&q=80',
    'bisc_baunilha': 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=400&q=80',
    'bisc_choco':    'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=400&q=80',
    'rec_baunilha':  'https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=400&q=80',
    'rec_choco':     'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&q=80',
}


def baixar_imagem(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return ContentFile(r.content)
    except Exception as e:
        print(f'  [aviso] falha ao baixar imagem: {e}')
        return None


class Command(BaseCommand):
    help = 'Popula o banco com dados de exemplo'

    def handle(self, *args, **kwargs):
        self.stdout.write('=== Populando banco ===')

        # ── Insumos ──────────────────────────────────────────────────
        insumos_data = [
            ('Farinha de Trigo', 10000, 'g',   'farinha'),
            ('Ovo',               200,  'un',  'ovo'),
            ('Chocolate em Pó',  5000,  'g',   'chocolate'),
            ('Manteiga',         3000,  'g',   'manteiga'),
            ('Leite',            8000,  'ml',  'leite'),
        ]
        insumos = {}
        for nome, qtd, und, chave in insumos_data:
            obj, criado = Insumo.objects.get_or_create(nome_insumo=nome, defaults={
                'qtd_disponivel': qtd,
                'und_medida': und,
            })
            if criado:
                img = baixar_imagem(IMAGENS[chave])
                if img:
                    obj.imagem.save(f'{chave}.jpg', img, save=True)
                self.stdout.write(f'  Insumo criado: {nome}')
            insumos[chave] = obj

        # ── Produtos (biscoitos) ──────────────────────────────────────
        produtos_data = [
            ('Biscoito de Baunilha', 50, 200, 'un', 8.00, 'bisc_baunilha'),
            ('Biscoito de Chocolate', 50, 200, 'un', 9.00, 'bisc_choco'),
        ]
        produtos = {}
        for nome, qtd, peso, und, preco, chave in produtos_data:
            obj, criado = Produto.objects.get_or_create(nome_produto=nome, defaults={
                'qtd_disponivel': qtd,
                'peso_cont': peso,
                'und_medida': und,
                'preco_unitario': preco,
            })
            if criado:
                img = baixar_imagem(IMAGENS[chave])
                if img:
                    obj.imagem.save(f'{chave}.jpg', img, save=True)
                self.stdout.write(f'  Produto criado: {nome}')
            produtos[chave] = obj

        # ── Receitas ─────────────────────────────────────────────────
        receitas_data = [
            ('Receita Baunilha',   produtos['bisc_baunilha'], 'rec_baunilha'),
            ('Receita Chocolate',  produtos['bisc_choco'],    'rec_choco'),
        ]
        receitas = {}
        for nome, produto, chave in receitas_data:
            obj, criado = Receita.objects.get_or_create(nome_receita=nome, defaults={'produto': produto})
            if criado:
                img = baixar_imagem(IMAGENS[chave])
                if img:
                    obj.imagem.save(f'{chave}.jpg', img, save=True)
                self.stdout.write(f'  Receita criada: {nome}')
            receitas[chave] = obj

        # ── Ingredientes das receitas ─────────────────────────────────
        ingredientes_baunilha = [
            (insumos['farinha'],   500, 'xícaras', 500, 'g'),
            (insumos['ovo'],         2, 'unidades',   1, 'un'),
            (insumos['manteiga'],  200, 'gramas',   200, 'g'),
            (insumos['leite'],     250, 'ml',       250, 'ml'),
        ]
        ingredientes_choco = [
            (insumos['farinha'],   500, 'xícaras', 500, 'g'),
            (insumos['ovo'],         2, 'unidades',   1, 'un'),
            (insumos['manteiga'],  200, 'gramas',   200, 'g'),
            (insumos['leite'],     250, 'ml',       250, 'ml'),
            (insumos['chocolate'], 100, 'colheres', 100, 'g'),
        ]

        def add_ingredientes(receita, lista):
            if receita.ingredientes.exists():
                return
            for insumo, qtd, medida, peso, und in lista:
                ItemReceita.objects.create(
                    receita=receita, insumo=insumo,
                    qtd=qtd, medida_caseira=medida,
                    peso_cont=peso, und_medida=und,
                )

        add_ingredientes(receitas['rec_baunilha'], ingredientes_baunilha)
        add_ingredientes(receitas['rec_choco'], ingredientes_choco)
        self.stdout.write('  Ingredientes adicionados')

        # ── Produções ─────────────────────────────────────────────────
        for i, (chave, qtd_rec, qtd_prod) in enumerate([
            ('rec_baunilha', 3, 30),
            ('rec_baunilha', 5, 50),
            ('rec_choco',    4, 40),
            ('rec_choco',    2, 20),
        ]):
            Producao.objects.get_or_create(
                receita=receitas[chave],
                qtd_da_receita=qtd_rec,
                defaults={
                    'qtd_produzida': qtd_prod,
                    'data_inicio': timezone.now() - timedelta(days=i * 3),
                }
            )
        self.stdout.write('  Produções criadas')

        # ── Vendas ────────────────────────────────────────────────────
        vendas_data = [
            ('DINHEIRO', [('bisc_baunilha', 5), ('bisc_choco', 3)]),
            ('PIX',      [('bisc_choco', 10)]),
            ('DINHEIRO', [('bisc_baunilha', 8)]),
            ('PIX',      [('bisc_baunilha', 4), ('bisc_choco', 6)]),
        ]
        for i, (metodo, itens) in enumerate(vendas_data):
            venda = Venda.objects.create(
                metodo_pagamento=metodo,
                data_venda=timezone.now() - timedelta(days=i * 2),
            )
            for chave, qtd in itens:
                ItemVenda.objects.create(
                    venda=venda,
                    produto=produtos[chave],
                    qtd=qtd,
                )
        self.stdout.write('  Vendas criadas')

        # ── Despesas ──────────────────────────────────────────────────
        despesas = [
            ('Gás de cozinha',     85.00,  date.today() - timedelta(days=10)),
            ('Embalagens',         120.00, date.today() - timedelta(days=7)),
            ('Material de limpeza', 45.50, date.today() - timedelta(days=5)),
            ('Energia elétrica',   210.00, date.today() - timedelta(days=2)),
        ]
        for desc, valor, data in despesas:
            Despesa.objects.get_or_create(descricao=desc, defaults={'valor': valor, 'data': data})
        self.stdout.write('  Despesas criadas')

        self.stdout.write(self.style.SUCCESS('=== Banco populado com sucesso! ==='))
