# -*- coding: utf-8 -*-

from django.conf.urls import url

from creme.creme_core.conf.urls import Swappable, swap_manager

from creme import products
from .views import product, service  # portal


urlpatterns = [
    # url(r'^$', portal.portal, name='products__portal'),

    # url(r'^product/(?P<product_id>\d+)/add_images[/]?$', product.add_images,   name='products__add_images_to_product'),
    url(r'^product/(?P<product_id>\d+)/add_images[/]?$', product.ImagesAdding.as_view(), name='products__add_images_to_product'),
    # url(r'^service/(?P<service_id>\d+)/add_images[/]?$', service.add_images,   name='products__add_images_to_service'),
    url(r'^service/(?P<service_id>\d+)/add_images[/]?$', service.ImagesAdding.as_view(), name='products__add_images_to_service'),
    url(r'^images/remove/(?P<entity_id>\d+)[/]?$',       product.remove_image, name='products__remove_image'),

    url(r'^sub_category/(?P<category_id>\d+)/json[/]?$', product.get_subcategories, name='products__subcategories'),
]

# if not products.product_model_is_custom():
#     urlpatterns += [
#         url(r'^products[/]?$',                         product.listview,   name='products__list_products'),
#         url(r'^product/add[/]?$',                      product.add,        name='products__create_product'),
#         url(r'^product/edit/(?P<product_id>\d+)[/]?$', product.edit,       name='products__edit_product'),
#         url(r'^product/(?P<product_id>\d+)[/]?$',      product.detailview, name='products__view_product'),
#     ]
urlpatterns += swap_manager.add_group(
    products.product_model_is_custom,
    Swappable(url(r'^products[/]?$',                         product.listview,                  name='products__list_products')),
    Swappable(url(r'^product/add[/]?$',                      product.ProductCreation.as_view(), name='products__create_product')),
    Swappable(url(r'^product/edit/(?P<product_id>\d+)[/]?$', product.ProductEdition.as_view(),  name='products__edit_product'), check_args=Swappable.INT_ID),
    Swappable(url(r'^product/(?P<product_id>\d+)[/]?$',      product.ProductDetail.as_view(),   name='products__view_product'), check_args=Swappable.INT_ID),
    app_name='products',
).kept_patterns()

# if not products.service_model_is_custom():
#     urlpatterns += [
#         url(r'^services[/]?$',                         service.listview,   name='products__list_services'),
#         url(r'^service/add[/]?$',                      service.add,        name='products__create_service'),
#         url(r'^service/edit/(?P<service_id>\d+)[/]?$', service.edit,       name='products__edit_service'),
#         url(r'^service/(?P<service_id>\d+)[/]?$',      service.detailview, name='products__view_service'),
#     ]
urlpatterns += swap_manager.add_group(
    products.service_model_is_custom,
    Swappable(url(r'^services[/]?$',                         service.listview,                  name='products__list_services')),
    Swappable(url(r'^service/add[/]?$',                      service.ServiceCreation.as_view(), name='products__create_service')),
    Swappable(url(r'^service/edit/(?P<service_id>\d+)[/]?$', service.ServiceEdition.as_view(),  name='products__edit_service'), check_args=Swappable.INT_ID),
    Swappable(url(r'^service/(?P<service_id>\d+)[/]?$',      service.ServiceDetail.as_view(),   name='products__view_service'), check_args=Swappable.INT_ID),
    app_name='products',
).kept_patterns()
