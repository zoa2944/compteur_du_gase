from django.urls import path

from . import views

app_name = 'base'

urlpatterns = [
    path('', views.index, name='index'),
    path('gestion', views.gestion, name='gestion'),
    path('achats', views.pre_achats, name='pre_achats'),
    path('achats/<int:member_id>', views.achats, name='achats'),
    path('achats/<int:member_id>/<int:cat_id>', views.achats_cat, name='achats_cat'),
    path('end_achats/<int:member_id>', views.end_achats, name='end_achats'),
    path('produits', views.products, name='products'),
    path('produit/<int:product_id>', views.detail_product, name='detail_product'),
    path('produit', views.create_product, name='create_product'),
    path('membres', views.members, name='members'),
    path('membre/<int:member_id>', views.detail_member, name='detail_member'),
    path('appro', views.pre_appro, name='pre_appro'),
    path('appro/<int:provider_id>', views.appro, name='appro'),
    path('compte', views.pre_compte, name='pre_compte'),
    path('compte/<int:member_id>', views.compte, name='compte'),
    path('inventaire', views.inventory, name='inventory'),
    path('stats/<int:product_id>', views.stats, name='stats'),
]
