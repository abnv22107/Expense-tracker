from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('expenses/', views.expenses_view, name='expenses'),
    path('expenses/create/', views.expense_create_view, name='expense-create'),
    path('expenses/<int:pk>/update/', views.expense_update_view, name='expense-update'),
    path('expenses/<int:pk>/delete/', views.expense_delete_view, name='expense-delete'),
    path('income/create/', views.income_create_view, name='income-create'),
    path('income/<int:pk>/update/', views.income_update_view, name='income-update'),
    path('income/<int:pk>/delete/', views.income_delete_view, name='income-delete'),
    path('insights/', views.insights_view, name='insights'),
    path('insights/analyze-investment/', views.analyze_investment_view, name='analyze-investment'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password_view, name='change-password'),
    path('profile/notification-settings/', views.notification_settings_view, name='notification-settings'),
    path('reports/', views.reports_view, name='reports'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/register/', views.register_view, name='register'),
    path('mutual-fund-suggestions/', views.mutual_fund_suggestions_view, name='mutual-fund-suggestions'),
    path('api/ask_gpt/', views.ask_gpt_view, name='ask-gpt'),
    path('api/transactions/', views.transactions_api, name='transactions-api'),
    path('signup/', views.signup_view, name='signup'),
    path('delete_transaction/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('stocks/', views.stocks_view, name='stocks'),
    path('api/stock/<str:symbol>/', views.stock_data_api, name='stock-data'),
    path('api/trending-stocks/', views.trending_stocks_api, name='trending-stocks'),
] 