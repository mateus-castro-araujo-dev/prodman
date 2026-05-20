from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import *
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from functools import wraps


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
    if request.method == 'POST' and request.user.is_superuser:
        acao = request.POST.get('acao')
        if acao == 'add_produto':
            prod = Produto(
                nome_produto=request.POST.get('nome_produto', '').strip(),
                qtd_disponivel=int(request.POST.get('qtd_disponivel', 0)),
                peso_cont=int(request.POST.get('peso_cont', 0)),
                und_medida=request.POST.get('und_medida', 'g'),
                preco_unitario=float(request.POST.get('preco_unitario', 0)),
            )
            prod.save()
            if 'imagem' in request.FILES:
                prod.imagem = request.FILES['imagem']
                prod.save()
            messages.success(request, 'Biscoito cadastrado com sucesso!')
        elif acao == 'delete_produto':
            Produto.objects.filter(id_produto=request.POST.get('id')).delete()
            messages.success(request, 'Biscoito removido.')
        return redirect('receitas_list')

    receitas = Receita.objects.prefetch_related('ingredientes', 'ingredientes__insumo', 'produto').all()
    produtos = Produto.objects.all().order_by('nome_produto')
    return render(request, 'receitas.html', {'receitas': receitas, 'produtos': produtos})

# --- PRODUÇÃO ---

@login_required
def producao_list(request):
    # Pendentes: qtd_produzida é None ou 0
    producoes_pendentes = Producao.objects.filter(qtd_produzida__isnull=True).order_by('-data_inicio')
    producoes_finalizadas = Producao.objects.filter(qtd_produzida__isnull=False).order_by('-data_inicio')
    return render(request, 'producao.html', {
        'pendentes': producoes_pendentes,
        'finalizadas': producoes_finalizadas,
        'from_admin': getattr(request, '_from_admin', False),
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
    hoje = timezone.now().date()
    data_inicio = request.GET.get('data_inicio') or hoje.replace(day=1).isoformat()
    data_fim = request.GET.get('data_fim') or hoje.isoformat()

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
                        if ultimo_preco and ultimo_preco.peso_cont:
                            preco_por_g = float(ultimo_preco.preco_unitario_final) / ultimo_preco.peso_cont
                            custo_insumos += preco_por_g * ing.qtd
                    total_custo_vendas += custo_insumos * item.qtd

        total_despesas = sum(d.valor for d in despesas_res)

        itens_vencidos = ItemCompra.objects.filter(data_validade__lt=hoje)
        for item in itens_vencidos:
            total_perdas += item.subtotal_com_desconto

    lucro_liquido = total_faturamento - total_custo_vendas - total_despesas - total_perdas

    # ── Dados para os gráficos ──
    from datetime import date as _date, timedelta
    from collections import defaultdict

    def build_chart(vendas, despesas, chave_fn, labels):
        fat   = defaultdict(float)
        custo = defaultdict(float)
        desp  = defaultdict(float)
        for venda in vendas:
            k = chave_fn(venda.data_venda.date())
            fat[k] += float(venda.total_venda())
            for item in venda.itens.all():
                receita = Receita.objects.filter(produto=item.produto).first()
                if receita:
                    ci = 0
                    for ing in receita.ingredientes.all():
                        up = ItemCompra.objects.filter(insumo=ing.insumo).order_by('-id_item_compra').first()
                        if up and up.peso_cont:
                            ci += (float(up.preco_unitario_final) / up.peso_cont) * ing.qtd
                    custo[k] += ci * item.qtd
        for d in despesas:
            desp[chave_fn(d.data)] += float(d.valor)
        lucro = {k: fat[k] - custo[k] - desp[k] for k in labels}
        return {
            'labels':      labels,
            'faturamento': [round(fat[k],   2) for k in labels],
            'custos':      [round(custo[k], 2) for k in labels],
            'despesas':    [round(desp[k],  2) for k in labels],
            'lucro':       [round(lucro[k], 2) for k in labels],
        }

    # Mensal: dias do mês atual
    mes_ini = hoje.replace(day=1)
    labels_mensal = [(mes_ini + timedelta(days=i)).strftime('%d/%m')
                     for i in range((hoje - mes_ini).days + 1)]
    chave_mensal = lambda d: d.strftime('%d/%m')
    vendas_mes = Venda.objects.filter(data_venda__date__gte=mes_ini, data_venda__date__lte=hoje)
    desp_mes   = Despesa.objects.filter(data__gte=mes_ini, data__lte=hoje)
    chart_mensal = build_chart(vendas_mes, desp_mes, chave_mensal, labels_mensal)

    # Anual: meses do ano atual
    ano_ini = hoje.replace(month=1, day=1)
    meses_nomes = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    labels_anual = [meses_nomes[m] for m in range(hoje.month)]
    chave_anual = lambda d: meses_nomes[d.month - 1]
    vendas_ano = Venda.objects.filter(data_venda__date__gte=ano_ini, data_venda__date__lte=hoje)
    desp_ano   = Despesa.objects.filter(data__gte=ano_ini, data__lte=hoje)
    chart_anual = build_chart(vendas_ano, desp_ano, chave_anual, labels_anual)

    chart_data = chart_mensal  # compatibilidade

    return render(request, 'relatorios.html', {
        'vendas': vendas_res,
        'producoes': producoes_res,
        'despesas': despesas_res,
        'faturamento': total_faturamento,
        'custos': total_custo_vendas,
        'despesas_total': total_despesas,
        'perdas': total_perdas,
        'lucro': lucro_liquido,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'chart_data':        json.dumps(chart_data),
        'chart_mensal':      json.dumps(chart_mensal),
        'chart_anual':       json.dumps(chart_anual),
        'from_admin': getattr(request, '_from_admin', False),
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
            if user.is_superuser:
                return redirect('painel_home')
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


# ════════════════════════════════════════════════
#  PAINEL ADMIN CUSTOMIZADO
# ════════════════════════════════════════════════

def painel_only(view_func):
    """Permite apenas superusers."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@painel_only
def painel_home(request):
    return render(request, 'painel/home.html', {'is_admin_painel': True})


@painel_only
def painel_relatorios(request):
    request._from_admin = True
    return relatorios(request)


@painel_only
def painel_producao(request):
    request._from_admin = True
    return producao_list(request)


@painel_only
def painel_insumos(request):
    edit_obj = None
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'delete':
            Insumo.objects.filter(id_insumo=request.POST.get('id')).delete()
            messages.success(request, 'Insumo removido.')
            return redirect('painel_insumos')
        elif acao in ('add', 'edit'):
            pk = request.POST.get('id')
            obj = Insumo.objects.get(id_insumo=pk) if pk else Insumo()
            obj.nome_insumo = request.POST.get('nome', '').strip()
            obj.qtd_disponivel = int(request.POST.get('qtd', 0))
            obj.und_medida = request.POST.get('und', 'g')
            obj.save()
            if 'imagem' in request.FILES:
                if obj.imagem:
                    obj.imagem.delete(save=False)
                obj.imagem = request.FILES['imagem']
                obj.save()
            messages.success(request, 'Insumo salvo com sucesso!')
            return redirect('painel_insumos')

    editar_id = request.GET.get('editar')
    if editar_id:
        edit_obj = Insumo.objects.filter(id_insumo=editar_id).first()

    return render(request, 'painel/insumos.html', {
        'insumos': Insumo.objects.all().order_by('nome_insumo'),
        'edit_obj': edit_obj,
        'form_title': '✏️ Editar Insumo' if edit_obj else '➕ Novo Insumo',
        'acao': 'edit' if edit_obj else 'add',
    })


@painel_only
def painel_compras(request):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'delete_despesa':
            Despesa.objects.filter(id_despesa=request.POST.get('id')).delete()
            messages.success(request, 'Despesa removida.')
            return redirect('painel_compras')
        elif acao == 'add_despesa':
            from datetime import date as _date
            Despesa.objects.create(
                descricao=request.POST.get('descricao', '').strip(),
                valor=float(request.POST.get('valor', 0)),
                data=request.POST.get('data') or _date.today(),
            )
            messages.success(request, 'Despesa registrada!')
            return redirect('painel_compras')
        elif acao == 'delete_compra':
            Compra.objects.filter(id_compra=request.POST.get('id')).delete()
            messages.success(request, 'Compra removida.')
        elif acao == 'add_compra':
            from datetime import date
            compra = Compra.objects.create(
                nota_fiscal=request.POST.get('nota_fiscal'),
                fornecedor=request.POST.get('fornecedor', '').strip(),
                data_nf=request.POST.get('data_nf') or date.today(),
            )
            insumos_ids = request.POST.getlist('insumo[]')
            qtds = request.POST.getlist('qtd_item[]')
            pesos = request.POST.getlist('peso_cont[]')
            unds = request.POST.getlist('und_item[]')
            precos = request.POST.getlist('preco[]')
            descontos_perc = request.POST.getlist('desc_perc[]')
            descontos_val = request.POST.getlist('desc_val[]')
            validades = request.POST.getlist('validade[]')
            for i, iid in enumerate(insumos_ids):
                if iid:
                    ItemCompra.objects.create(
                        compra=compra,
                        insumo_id=iid,
                        qtd_item_compra=int(qtds[i] or 0),
                        peso_cont=int(pesos[i] or 0),
                        und_medida=unds[i] if i < len(unds) else 'g',
                        preco_unitario=float(precos[i] or 0),
                        desconto_percentual=float(descontos_perc[i] or 0) if i < len(descontos_perc) else 0,
                        desconto_valor=float(descontos_val[i] or 0) if i < len(descontos_val) else 0,
                        data_validade=validades[i] if i < len(validades) and validades[i] else None,
                    )
            messages.success(request, 'Compra registrada!')
        return redirect('painel_compras')

    return render(request, 'painel/compras.html', {
        'compras': Compra.objects.prefetch_related('itens__insumo').order_by('-data_nf')[:10],
        'insumos': Insumo.objects.order_by('nome_insumo'),
        'despesas': Despesa.objects.order_by('-data')[:10],
    })


@painel_only
def painel_receitas(request):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'delete_produto':
            Produto.objects.filter(id_produto=request.POST.get('id')).delete()
            messages.success(request, 'Biscoito removido.')
            return redirect('painel_receitas')
        elif acao in ('add_produto', 'edit_produto'):
            pk = request.POST.get('id')
            prod = Produto.objects.get(id_produto=pk) if pk else Produto()
            prod.nome_produto = request.POST.get('nome_produto', '').strip()
            prod.qtd_disponivel = int(request.POST.get('qtd_disponivel', 0))
            prod.peso_cont = int(request.POST.get('peso_cont', 0))
            prod.und_medida = request.POST.get('und_medida', 'g')
            prod.preco_unitario = float(request.POST.get('preco_unitario', 0))
            prod.save()
            if 'imagem' in request.FILES:
                if prod.imagem:
                    prod.imagem.delete(save=False)
                prod.imagem = request.FILES['imagem']
                prod.save()
            messages.success(request, 'Biscoito salvo!')
            return redirect('painel_receitas')
        elif acao == 'delete_receita':
            Receita.objects.filter(id_receita=request.POST.get('id')).delete()
            messages.success(request, 'Receita removida.')
            return redirect('painel_receitas')
        elif acao in ('add_receita', 'edit_receita'):
            pk = request.POST.get('id')
            if pk:
                receita = Receita.objects.get(id_receita=pk)
                receita.ingredientes.all().delete()
            else:
                receita = Receita()
            receita.nome_receita = request.POST.get('nome_receita')
            receita.produto_id = request.POST.get('produto')
            receita.save()
            if 'imagem' in request.FILES:
                if receita.imagem:
                    receita.imagem.delete(save=False)
                receita.imagem = request.FILES['imagem']
                receita.save()
            insumos_ids = request.POST.getlist('ing_insumo[]')
            qtds = request.POST.getlist('ing_qtd[]')
            medidas = request.POST.getlist('ing_medida[]')
            pesos = request.POST.getlist('ing_peso[]')
            unds = request.POST.getlist('ing_und[]')
            for i, iid in enumerate(insumos_ids):
                if iid:
                    ItemReceita.objects.create(
                        receita=receita,
                        insumo_id=iid,
                        qtd=int(qtds[i] or 0),
                        medida_caseira=medidas[i] if i < len(medidas) else '',
                        peso_cont=int(pesos[i] or 0),
                        und_medida=unds[i] if i < len(unds) else 'g',
                    )
            messages.success(request, 'Receita salva!')
        return redirect('painel_receitas')

    edit_produto = None
    edit_receita = None
    if request.GET.get('editar_produto'):
        edit_produto = Produto.objects.filter(id_produto=request.GET.get('editar_produto')).first()
    if request.GET.get('editar_receita'):
        edit_receita = Receita.objects.prefetch_related('ingredientes__insumo').filter(id_receita=request.GET.get('editar_receita')).first()

    return render(request, 'painel/receitas.html', {
        'receitas': Receita.objects.prefetch_related('ingredientes__insumo').order_by('nome_receita'),
        'insumos': Insumo.objects.order_by('nome_insumo'),
        'produtos': Produto.objects.order_by('nome_produto'),
        'edit_produto': edit_produto,
        'edit_receita': edit_receita,
    })


@painel_only
def painel_vendas(request):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'delete_venda':
            Venda.objects.filter(id_venda=request.POST.get('id')).delete()
            messages.success(request, 'Venda removida.')
        elif acao == 'add_venda':
            carrinho_json = request.POST.get('carrinho_json', '{}')
            carrinho = json.loads(carrinho_json)
            venda = Venda.objects.create(
                metodo_pagamento=request.POST.get('metodo', 'DINHEIRO'),
            )
            for pid, item in carrinho.items():
                ItemVenda.objects.create(venda=venda, produto_id=int(pid), qtd=int(item['qtd']))
            messages.success(request, 'Venda registrada!')
        return redirect('painel_vendas')

    return render(request, 'painel/vendas.html', {
        'vendas': Venda.objects.prefetch_related('itens__produto').order_by('-data_venda'),
        'produtos': Produto.objects.filter(qtd_disponivel__gt=0).order_by('nome_produto'),
    })


@painel_only
def painel_despesas(request):
    edit_obj = None
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'delete_despesa':
            Despesa.objects.filter(id_despesa=request.POST.get('id')).delete()
            messages.success(request, 'Despesa removida.')
            return redirect('painel_despesas')
        elif acao in ('add_despesa', 'edit_despesa'):
            from datetime import date
            pk = request.POST.get('id')
            obj = Despesa.objects.get(id_despesa=pk) if pk else Despesa()
            obj.descricao = request.POST.get('descricao', '').strip()
            obj.valor = float(request.POST.get('valor', 0))
            data_str = request.POST.get('data')
            obj.data = data_str if data_str else date.today()
            obj.save()
            messages.success(request, 'Despesa salva!')
            return redirect('painel_despesas')

    editar_id = request.GET.get('editar')
    if editar_id:
        edit_obj = Despesa.objects.filter(id_despesa=editar_id).first()

    return render(request, 'painel/despesas.html', {
        'despesas': Despesa.objects.order_by('-data'),
        'edit_obj': edit_obj,
    })


@painel_only
def painel_usuarios(request):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'delete_user':
            uid = request.POST.get('id')
            User.objects.filter(id=uid, is_superuser=False).delete()
            messages.success(request, 'Usuário removido.')
        elif acao == 'add_user':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            confirm = request.POST.get('confirm', '')
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Nome de usuário já existe.')
            elif len(password) < 4:
                messages.error(request, 'Senha deve ter ao menos 4 caracteres.')
            elif password != confirm:
                messages.error(request, 'As senhas não coincidem.')
            else:
                novo = User.objects.create_user(username=username, password=password, is_staff=False, is_superuser=False)
                if 'foto' in request.FILES:
                    novo.perfil.foto = request.FILES['foto']
                    novo.perfil.save()
                messages.success(request, f'Usuário "{username}" criado!')
        elif acao == 'edit_user':
            uid = request.POST.get('id')
            user = User.objects.filter(id=uid, is_superuser=False).first()
            if not user:
                messages.error(request, 'Usuário não encontrado.')
            else:
                novo_username = request.POST.get('username', '').strip()
                password = request.POST.get('password', '')
                confirm = request.POST.get('confirm', '')
                if novo_username != user.username and User.objects.filter(username=novo_username).exists():
                    messages.error(request, 'Esse nome de usuário já existe.')
                elif password and password != confirm:
                    messages.error(request, 'As senhas não coincidem.')
                elif password and len(password) < 4:
                    messages.error(request, 'Senha deve ter ao menos 4 caracteres.')
                else:
                    user.username = novo_username
                    if password:
                        user.set_password(password)
                    user.save()
                    if 'foto' in request.FILES:
                        if user.perfil.foto:
                            user.perfil.foto.delete(save=False)
                        user.perfil.foto = request.FILES['foto']
                        user.perfil.save()
                    messages.success(request, 'Usuário atualizado!')
        return redirect('painel_usuarios')

    return render(request, 'painel/usuarios.html', {
        'usuarios': User.objects.select_related('perfil').order_by('username'),
    })
