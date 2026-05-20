from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import (
    Insumo, Compra, ItemCompra, Produto,
    Receita, ItemReceita,
    Venda, ItemVenda, Perfil,
)


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name = 'Foto de perfil'


class UsuarioNormalAdmin(UserAdmin):
    inlines = [PerfilInline]
    def save_model(self, request, obj, form, change):
        if not change:  # só na criação
            obj.is_staff = False
            obj.is_superuser = False
        super().save_model(request, obj, form, change)


admin.site.unregister(User)
admin.site.register(User, UsuarioNormalAdmin)


class ItemCompraInline(admin.TabularInline):
    model = ItemCompra
    extra = 1


class ItemReceitaInline(admin.TabularInline):
    model = ItemReceita
    extra = 1


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 1


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nome_insumo', 'qtd_disponivel', 'und_medida')
    search_fields = ('nome_insumo',)


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('nota_fiscal', 'data_nf')
    inlines = [ItemCompraInline]


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome_produto', 'qtd_disponivel', 'preco_unitario', 'und_medida')
    search_fields = ('nome_produto',)


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('nome_receita', 'produto')
    inlines = [ItemReceitaInline]


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id_venda', 'data_venda', 'metodo_pagamento')
    inlines = [ItemVendaInline]


