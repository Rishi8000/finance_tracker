from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account-books/create/', views.create_account_book, name='create_account_book'),
    path('account-books/<int:book_id>/delete/', views.delete_account_book, name='delete_account_book'),
    path('account-books/<int:book_id>/', views.account_book_detail, name='account_book_detail'),
    path('account-books/<int:book_id>/add-transaction/', views.add_transaction, name='add_transaction'),
    path('account-books/transaction_history/', views.transaction_history, name='transaction_history'),
]