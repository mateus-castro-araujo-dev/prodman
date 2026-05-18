from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import *
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def insumos_list(request):
    insumos = Insumo.objects.all()
    return render(request, 'insumos.html', {'insumos': insumos})

@login_required
def compras_list(request):
    compras = Compra.objects.prefetch_related('itens', 'itens__insumo').all().order_by('-data_nf')
    despesas = Despesa.objects.all().order_by('-data')
    return render(request, 'compras.html', {'compras': compras, 'despesas': despesas})

@login_required
def despesa_adicionar(request):
    if request.method == 'POST':
        descricao = request.POST.get('descricao', '').strip()
        valor = request.POST.get('valor', '').strip()
        data = request.POST.get('data', '').strip()
        if descricao and valor:
            Despesa.objects.create(descricao=descricao, valor=valor, data=data or timezone.now().date())
            messages.success(request, 'Despesa registrada com sucesso!')
        else:
            messages.error(request, 'Preencha descrição e valor.')
    return redirect('compras_list')

@login_required
def receitas_list(request):
    receitas = Receita.objects.prefetch_related('ingredientes', 'ingredientes__insumo', 'produto').all()
    return render(request, 'receitas.html', {'receitas': receitas})

# --- PRODUÇÃO ---

@login_required
def producao_list(request):
    # Pendentes: qtd_produzida é None ou 0
    producoes_pendentes = Producao.objects.filter(qtd_produzida__isnull=True).order_by('-data_inicio')
    producoes_finalizadas = Producao.objects.filter(qtd_produzida__isnull=False).order_by('-data_inicio')
    return render(request, 'producao.html', {
        'pendentes': producoes_pendentes,
        'finalizadas': producoes_finalizadas
    })

@login_required
def producao_nova(request):
    if request.method == 'POST':
        receita_id = request.POST.get('receita_id')
        qtd_batches = int(request.POST.get('qtd_batches'))

        receita = get_object_or_404(Receita, pk=receita_id)
        
        # Verificar Estoque
        pode_produzir = True
        msg_erro = ""
        
        for ingrediente in receita.ingredientes.all():
            # Calcula o total de insumo necessário para os lotes
            qtd_necessaria = ingrediente.qtd * qtd_batches
            if ingrediente.insumo.qtd_disponivel < qtd_necessaria:
                pode_produzir = False
                msg_erro = f"Insumo insuficiente: {ingrediente.insumo.nome_insumo}"
                break
        
        if pode_produzir:
            # CRIA A PRODUÇÃO SALVANDO A QUANTIDADE DE LOTES
            Producao.objects.create(
                receita=receita, 
                qtd_produzida=None,
                qtd_da_receita=qtd_batches
            )
            messages.success(request, f"Produção de {qtd_batches} lote(s) iniciada com sucesso!")
            return redirect('producao_list')
        else:
            messages.error(request, msg_erro)

    receitas = Receita.objects.all()
    return render(request, 'producao_nova.html', {'receitas': receitas})

@login_required
@transaction.atomic
def producao_finalizar(request, id_producao):
    producao = get_object_or_404(Producao, pk=id_producao)
    
    if request.method == 'POST':
        qtd_final = int(request.POST.get('qtd_final'))
        
        # Atualiza a produção
        producao.qtd_produzida = qtd_final
        producao.save()
        
        # Dá baixa no estoque de insumos
        # Assumindo que qtd_final é proporcional à receita base.
        # Se a receita base gera 1 produto, multiplicamos ingredientes por qtd_final.
        for ingrediente in producao.receita.ingredientes.all():
            # qtd_deduzir = ingrediente.qtd * qtd_final
            qtd_deduzir = ingrediente.peso_cont * producao.qtd_da_receita
            insumo = ingrediente.insumo
            insumo.qtd_disponivel -= qtd_deduzir
            insumo.save()
            
        # 2. Adiciona ao estoque de produtos
        produto = producao.receita.produto
        produto.qtd_disponivel += qtd_final
        produto.save()
        
        messages.success(request, "Produção finalizada e estoques atualizados.")
        return redirect('producao_list')
        
    return render(request, 'producao_finalizar.html', {'producao': producao})

# --- VENDA ---
@login_required
def venda_view(request):
    produtos = Produto.objects.filter(qtd_disponivel__gt=0)
    
    if request.method == 'POST':
        try:
            # 1. Carrega os dados do JSON
            dados = json.loads(request.body)
            carrinho = dados.get('carrinho', [])
            metodo = dados.get('metodo_pagamento', 'DINHEIRO') # Pega o método do JSON
            
            if not carrinho:
                return JsonResponse({'status': 'error', 'message': 'Carrinho vazio'}, status=400)

            # 2. Inicia uma transação atômica
            with transaction.atomic():
                # Cria a venda
                nova_venda = Venda.objects.create(
                    data_venda=timezone.now(),
                    metodo_pagamento=metodo # Salva no banco
                )   
                print(f"--- Iniciando Venda #{nova_venda.id_venda} ---")
                
                for item in carrinho:
                    # 3. Força a conversão para INTEIROS
                    prod_id = int(item['id'])
                    qtd_venda = int(item['qty'])
                    
                    # Busca o produto bloqueando para edição
                    produto_db = Produto.objects.select_for_update().get(pk=prod_id)
                    
                    print(f"Produto: {produto_db.nome_produto} | Estoque Atual: {produto_db.qtd_disponivel} | Vendendo: {qtd_venda}")
                    
                    if produto_db.qtd_disponivel >= qtd_venda:
                        # Deduz do estoque
                        produto_db.qtd_disponivel -= qtd_venda
                        produto_db.save() # Salva a alteração no banco
                        
                        # Cria o item da venda
                        ItemVenda.objects.create(
                            venda=nova_venda,
                            produto=produto_db,
                            qtd=qtd_venda
                        )
                        print(f"-> Sucesso. Novo estoque: {produto_db.qtd_disponivel}")
                    else:
                        # Se faltar estoque, cancela TUDO (Rollback)
                        raise Exception(f"Estoque insuficiente para {produto_db.nome_produto}")
            
            return JsonResponse({'status': 'success', 'message': 'Venda realizada!'})

        except Exception as e:
            print(f"ERRO NA VENDA: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return render(request, 'venda.html', {'produtos': produtos})

# --- RELATÓRIOS ---

@login_required
def relatorios(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    vendas_res = []
    producoes_res = []
    despesas_res = []
    total_faturamento = 0
    total_custo_vendas = 0
    total_despesas = 0
    total_perdas = 0

    if data_inicio and data_fim:
        vendas_res = Venda.objects.filter(
            data_venda__date__gte=data_inicio,
            data_venda__date__lte=data_fim
        )
        producoes_res = Producao.objects.filter(
            data_inicio__date__gte=data_inicio,
            data_inicio__date__lte=data_fim
        )
        despesas_res = Despesa.objects.filter(
            data__gte=data_inicio,
            data__lte=data_fim
        )

        for venda in vendas_res:
            total_faturamento += venda.total_venda()

            for item in venda.itens.all():
                receita = Receita.objects.filter(produto=item.produto).first()
                if receita:
                    custo_insumos = 0
                    for ing in receita.ingredientes.all():
                        ultimo_preco = ItemCompra.objects.filter(insumo=ing.insumo).order_by('-id_item_compra').first()
                        preco_unit = ultimo_preco.preco_unitario if ultimo_preco else 0
                        custo_insumos += (ing.peso_cont * preco_unit)
                    total_custo_vendas += (custo_insumos * item.qtd)

        total_despesas = sum(d.valor for d in despesas_res)

        hoje = timezone.now().date()
        itens_vencidos = ItemCompra.objects.filter(data_validade__lt=hoje)
        for item in itens_vencidos:
            total_perdas += (item.preco_unitario * item.qtd_item_compra)

    lucro_liquido = total_faturamento - total_custo_vendas - total_despesas - total_perdas

    return render(request, 'relatorios.html', {
        'vendas': vendas_res,
        'producoes': producoes_res,
        'despesas': despesas_res,
        'faturamento': total_faturamento,
        'custos': total_custo_vendas,
        'despesas_total': total_despesas,
        'perdas': total_perdas,
        'lucro': lucro_liquido,
    })

# --- LOGIN ---

def login_view(request):
    usuarios = User.objects.filter(is_staff=False, is_superuser=False)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            return render(request, "login.html", {
                "erro": "Usuário ou senha inválidos",
                "usuarios": usuarios
            })

    return render(request, "login.html", {"usuarios": usuarios})

@login_required
def home(request):
    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    return redirect('login')