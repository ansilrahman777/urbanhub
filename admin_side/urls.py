from django.urls import path
from admin_side import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin_login',views.admin_login,name='admin_login'),
    path('admin_logout',views.admin_logout,name='admin_logout'),

    path('admin_index',views.admin_index,name='admin_index'),
    path('admin_category',views.admin_category,name='admin_category'),
    path('admin_products',views.admin_products,name='admin_products'),
    path('admin_orders',views.admin_orders,name='admin_orders'),
    path('admin_coupons',views.admin_coupons,name='admin_coupons'),
    
    path('admin_users',views.admin_users,name='admin_users'),
    path('admin_user_block_unblock/<int:id>',views.admin_user_block_unblock,name='admin_user_block_unblock'),

    path('admin_enable_disable_category/<int:id>',views.admin_enable_disable_category,name='admin_enable_disable_category'),
    path('admin_unlist_list_product/<int:product_id>',views.admin_unlist_list_product,name='admin_unlist_list_product'),


    path('admin_banners',views.admin_banners,name='admin_banners'),

    path('admin_add_category',views.admin_add_category,name='admin_add_category'),
    path('admin_add_product',views.admin_add_product,name='admin_add_product'),

    path('admin_edit_category/<int:id>/',views.admin_edit_category,name='admin_edit_category'),
    path('admin_edit_product/<int:product_id>/', views.admin_edit_product, name='admin_edit_product'),

    
    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)