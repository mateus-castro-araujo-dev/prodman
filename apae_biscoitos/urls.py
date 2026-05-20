"""
URL configuration for apae_biscoitos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('django-admin/', admin.site.urls),

    path('', views.login_view),
    path('home/', views.home, name='home'),

    path('insumos/', views.insumos_list, name='insumos_list'),
    path('compras/', views.compras_list, name='compras_list'),
    path('despesas/adicionar/', views.despesa_adicionar, name='despesa_adicionar'),
    path('receitas/', views.receitas_list, name='receitas_list'),
    
    path('producao/', views.producao_list, name='producao_list'),
    path('producao/nova/', views.producao_nova, name='producao_nova'),
    path('producao/finalizar/<int:id_producao>/', views.producao_finalizar, name='producao_finalizar'),
    
    path('venda/', views.venda_view, name='venda_view'),
    path('relatorios/', views.relatorios, name='relatorios'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Painel Admin Customizado
    path('admin/', views.painel_home, name='painel_home'),
    path('admin/insumos/', views.painel_insumos, name='painel_insumos'),
    path('admin/compras/', views.painel_compras, name='painel_compras'),
    path('admin/receitas/', views.painel_receitas, name='painel_receitas'),
    path('admin/vendas/', views.painel_vendas, name='painel_vendas'),
    path('admin/despesas/', views.painel_despesas, name='painel_despesas'),
    path('admin/usuarios/', views.painel_usuarios, name='painel_usuarios'),
    path('admin/relatorios/', views.painel_relatorios, name='painel_relatorios'),
    path('admin/producao/', views.painel_producao, name='painel_producao'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)