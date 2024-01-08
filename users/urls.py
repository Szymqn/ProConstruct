from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('user_details/', views.user_details, name='user_details'),
    path('change_password/', views.change_password, name='change_password'),
    path('check_orders/', views.check_orders, name='check_orders'),
]
