from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .models import Expense, Category, Income, UserProfile
from .forms import ExpenseForm, SignUpForm, IncomeForm, UserProfileForm
from django.contrib.auth import login as auth_login
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count
from collections import defaultdict
import json
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import openai
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
import cohere
import calendar
from dateutil.relativedelta import relativedelta
import requests
import yfinance as yf

# Initialize Cohere client
co = cohere.Client(settings.COHERE_API_KEY)

@login_required
def dashboard_view(request):
    # Get date range from request or default to current month
    today = timezone.now()
    current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # If it's the current month, use today as end date, otherwise use last day of the month
    if today.month == current_month_start.month:
        current_month_end = today
    else:
        # Get the last day of the current month
        next_month = current_month_start.replace(day=28) + timedelta(days=4)
        current_month_end = next_month - timedelta(days=next_month.day)
    
    # Get date range from request or use defaults
    date_from = request.GET.get('date_from', current_month_start.strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', current_month_end.strftime('%Y-%m-%d'))
    
    # Convert string dates to datetime objects
    date_from = datetime.strptime(date_from, '%Y-%m-%d')
    date_from = timezone.make_aware(date_from)
    date_to = datetime.strptime(date_to, '%Y-%m-%d')
    date_to = timezone.make_aware(date_to)
    
    print(f"Dashboard View - Date From: {date_from.strftime('%Y-%m-%d')}, Date To: {date_to.strftime('%Y-%m-%d')}")

    # Fetch expenses and income for the date range
    expenses = Expense.objects.filter(
        user=request.user,
        date__gte=date_from,
        date__lte=date_to
    ).select_related('category')  # Optimize query by selecting related category
    
    income = Income.objects.filter(
        user=request.user,
        date__gte=date_from,
        date__lte=date_to
    )
    
    print(f"Number of expenses fetched: {expenses.count()}")
    print(f"Number of incomes fetched: {income.count()}")
    
    # Calculate totals
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_income = income.aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate savings-related expenses (including mutual funds)
    savings_expenses = expenses.filter(
        category__name__in=['Savings', 'Mutual Funds']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate net savings (income - expenses excluding savings)
    net_savings = total_income - (total_expenses - savings_expenses)
    
    # Calculate savings rate
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
    
    print(f"Calculated Total Income: {total_income}")
    print(f"Calculated Total Expenses: {total_expenses}")
    print(f"Calculated Net Savings: {net_savings}")
    print(f"Calculated Savings Rate: {savings_rate}")
    
    # Prepare data for pie chart: total expenses per category
    category_totals = defaultdict(float)
    for expense in expenses:
        category_name = expense.category.name if expense.category else "Uncategorized"
        category_totals[category_name] += float(expense.amount)
    
    # Sort categories by amount for better visualization
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    
    pie_chart_data = {
        'labels': [cat[0] for cat in sorted_categories],
        'values': [float(cat[1]) for cat in sorted_categories],
    }
    
    # Prepare data for bar chart: monthly expenses for the selected period
    bar_chart_labels = []
    bar_chart_values = []
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Iterate through months within the selected date range
    current_date_iter = date_from.replace(day=1) # Start from the first day of the start month
    while current_date_iter <= date_to:
        year = current_date_iter.year
        month = current_date_iter.month
    
        # Get the first day of the target month
        start_of_month = timezone.make_aware(datetime(year, month, 1))
    
        # Get the last day of the target month
        _, num_days_in_month = calendar.monthrange(year, month)
        end_of_month = timezone.make_aware(datetime(year, month, num_days_in_month, 23, 59, 59, 999999))

        # Adjust end_of_month to be no later than date_to
        if end_of_month > date_to:
            end_of_month = date_to
    
        monthly_total = Expense.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
    
        bar_chart_labels.append(f"{month_names[month-1]} {year}")
        bar_chart_values.append(float(monthly_total))
    
        # Move to the next month
        current_date_iter += relativedelta(months=1)
    
    bar_chart_data = {
        'labels': bar_chart_labels,
        'values': bar_chart_values,
    }
    
    # Prepare transactions list for detailed report
    transactions = []
    for expense in expenses:
        transactions.append({
            'id': expense.id,
            'date': expense.date,
            'description': expense.description,
            'category': expense.category,
            'transaction_type': 'expense',
            'amount': float(expense.amount)
        })
    
    for inc in income:
        transactions.append({
            'id': inc.id,
            'date': inc.date,
            'description': inc.description,
            'category': {'name': inc.category} if inc.category else {'name': 'Uncategorized'},
            'transaction_type': 'income',
            'amount': float(inc.amount)
        })
    
    # Sort transactions by date
    transactions.sort(key=lambda x: x['date'], reverse=True)
    
    # Determine if the current view is for the 'Current Month'
    is_current_month_view = (
        date_from.date() == current_month_start.date() and
        date_to.date() == current_month_end.date()
    )

    context = {
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'current_month_start': current_month_start.strftime('%Y-%m-%d'),
        'current_month_end': current_month_end.strftime('%Y-%m-%d'),
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_savings': net_savings,
        'savings_rate': round(savings_rate, 1),
        'pie_chart_data': json.dumps(pie_chart_data),
        'bar_chart_data': json.dumps(bar_chart_data),
        'transactions': transactions,
        'income_form': IncomeForm(),
        'current_month': current_month_start.strftime('%B %Y'),
        'is_current_month_view': is_current_month_view,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def expenses_view(request):
    # Get date range from request or default to current month
    today = timezone.now()
    current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # If it's the current month, use today as end date, otherwise use last day of the month
    if today.month == current_month_start.month:
        current_month_end = today
    else:
        # Get the last day of the current month
        next_month = current_month_start.replace(day=28) + timedelta(days=4)
        current_month_end = next_month - timedelta(days=next_month.day)
    
    # Get date range from request or use defaults
    date_from = request.GET.get('date_from', current_month_start.strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', current_month_end.strftime('%Y-%m-%d'))
    
    # Convert string dates to datetime objects
    date_from = datetime.strptime(date_from, '%Y-%m-%d')
    date_from = timezone.make_aware(date_from)
    date_to = datetime.strptime(date_to, '%Y-%m-%d')
    date_to = timezone.make_aware(date_to)
    
    # Get expenses for the date range
    expenses = Expense.objects.filter(
        user=request.user,
        date__gte=date_from,
        date__lte=date_to
    ).select_related('category').order_by('-date', '-created_at')
    
    # Get all categories for the filter
    categories = Category.objects.filter(user=request.user).order_by('name')
    
    # Get selected category from request
    selected_category = request.GET.get('category')
    if selected_category:
        expenses = expenses.filter(category_id=selected_category)
    
    # Calculate statistics
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_transactions = expenses.count()
    average_expense = int(total_expenses / total_transactions) if total_transactions > 0 else 0
    
    # Calculate top category
    category_totals = defaultdict(float)
    for expense in expenses:
        category_name = expense.category.name if expense.category else "Uncategorized"
        category_totals[category_name] += float(expense.amount)
    
    top_category = max(category_totals.items(), key=lambda x: x[1])[0] if category_totals else "N/A"
    
    context = {
        'expenses': expenses,
        'categories': categories,
        'form': ExpenseForm(user=request.user),
        'selected_category': selected_category,
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'total_expenses': total_expenses,
        'average_expense': average_expense,
        'total_transactions': total_transactions,
        'top_category': top_category,
    }
    return render(request, 'tracker/expenses.html', context)

@login_required
def expense_create_view(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            # If no category is selected, create or get an "Uncategorized" category
            if not expense.category:
                uncategorized, created = Category.objects.get_or_create(
                    name="Uncategorized",
                    user=request.user
                )
                expense.category = uncategorized
            expense.save()
            return redirect('tracker:expenses')
    else:
        form = ExpenseForm(user=request.user)
    return render(request, 'tracker/expense_form.html', {'form': form})

@login_required
def expense_update_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('tracker:expenses')
    else:
        form = ExpenseForm(instance=expense, user=request.user)
    return render(request, 'tracker/expense_form.html', {'form': form, 'expense': expense})

@login_required
def expense_delete_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        return redirect('tracker:expenses')
    return render(request, 'tracker/expense_confirm_delete.html', {'expense': expense})

@login_required
def insights_view(request):
    # Get expense data for insights
    expenses = Expense.objects.filter(user=request.user)
    
    # Calculate total expenses
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate average expense
    avg_expense = total_expenses / expenses.count() if expenses.exists() else 0

    # Get expenses from the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_expenses = expenses.filter(date__gte=thirty_days_ago)

    # Get income from the last 30 days
    recent_income = Income.objects.filter(user=request.user, date__gte=thirty_days_ago)
    total_recent_income = recent_income.aggregate(total=Sum('amount'))['total'] or 0
    total_recent_expenses = recent_expenses.aggregate(total=Sum('amount'))['total'] or 0
    savings_potential = total_recent_income - total_recent_expenses

    # Analyze spending patterns
    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    
    for expense in recent_expenses:
        if expense.category:
            category_totals[expense.category.name] += float(expense.amount)
            category_counts[expense.category.name] += 1

    # Sort categories by total spending
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    # Use all categories instead of limiting to top 5
    top_categories = sorted_categories

    # Define category-specific tips
    category_tips = {
        'Food': [
            "Consider meal prepping to reduce food expenses.",
            "Look for deals and discounts at your local grocery store.",
            "Try to limit eating out to special occasions."
        ],
        'Transportation': [
            "Consider carpooling or public transportation to save on fuel.",
            "Regular vehicle maintenance can prevent costly repairs.",
            "Look into fuel-efficient driving habits."
        ],
        'Entertainment': [
            "Look for free or low-cost entertainment options.",
            "Consider sharing streaming service subscriptions with family.",
            "Set a monthly entertainment budget."
        ],
        'Shopping': [
            "Create a shopping list and stick to it.",
            "Wait for sales or use discount codes.",
            "Consider if you really need each purchase."
        ],
        'Bills': [
            "Review your subscriptions and cancel unused ones.",
            "Look for better deals on utilities and services.",
            "Consider bundling services for better rates."
        ],
        'Health': [
            "Use generic medications when possible.",
            "Take advantage of preventive care benefits.",
            "Consider a health savings account if eligible."
        ],
        'Education': [
            "Look for free online learning resources.",
            "Check for student discounts on software and services.",
            "Consider used textbooks or digital versions."
        ]
    }

    # Generate savings suggestions
    savings_suggestions = []
    
    # Add category-specific suggestions for all categories
    for category, amount in top_categories:
        if category in category_tips:
            # Calculate percentage of total spending
            percentage = (float(amount) / float(total_expenses)) * 100 if total_expenses > 0 else 0
            
            # Add a general observation
            savings_suggestions.append({
                'category': category,
                'amount': amount,
                'percentage': percentage,
                'tips': category_tips[category][:2]  # Get first 2 tips for this category
            })

    # Add general suggestions based on spending patterns
    if total_expenses > 0:
        # Check for frequent small purchases
        small_purchases = [exp for exp in recent_expenses if float(exp.amount) < 10]
        if len(small_purchases) > 10:
            small_total = sum(float(exp.amount) for exp in small_purchases)
            savings_suggestions.append({
                'category': 'Small Purchases',
                'amount': small_total,
                'percentage': (small_total / float(total_expenses)) * 100,
                'tips': [
                    "Track your small daily purchases - they add up quickly!",
                    "Consider setting a daily spending limit for small purchases."
                ]
            })

        # Add overall spending suggestion
        if total_expenses > 50000:  # Example threshold
            savings_suggestions.append({
                'category': 'Overall Spending',
                'amount': total_expenses,
                'percentage': 100,
                'tips': [
                    "Your monthly spending is above average. Consider creating a detailed budget.",
                    "Look for areas where you can reduce discretionary spending."
                ]
            })

    context = {
        'total_expenses': total_expenses,
        'avg_expense': avg_expense,
        'expense_count': expenses.count(),
        'savings_suggestions': savings_suggestions,
        'top_categories': top_categories,
        'savings_potential': savings_potential,
    }
    return render(request, 'tracker/insights.html', context)

@login_required
def analyze_investment_view(request):
    return render(request, 'tracker/insights.html')

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('tracker:profile')
    else:
        form = UserProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'tracker/profile.html', context)

@login_required
def change_password_view(request):
    return render(request, 'tracker/profile.html')

@login_required
def notification_settings_view(request):
    return render(request, 'tracker/profile.html')

@login_required
def reports_view(request):
    # Get recent expenses
    expenses = Expense.objects.filter(user=request.user).order_by('-date', '-created_at')[:5]
    
    # Get recent income
    income = Income.objects.filter(user=request.user).order_by('-date', '-created_at')[:5]
    
    # Calculate totals
    total_expenses = Expense.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or 0
    total_income = Income.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or 0
    balance = total_income - total_expenses
    
    context = {
        'expenses': expenses,
        'income': income,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'balance': balance,
        'form': ExpenseForm(user=request.user),
        'income_form': IncomeForm(),
    }
    return render(request, 'tracker/reports.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('tracker:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('tracker:login')

def register_view(request):
    if request.method == 'POST':
        # Handle registration logic here
        pass
    return render(request, 'tracker/register.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def income_create_view(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            return redirect('tracker:dashboard')
    else:
        form = IncomeForm()
    return render(request, 'tracker/income_form.html', {'form': form})

@login_required
def income_update_view(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            return redirect('tracker:dashboard')
    else:
        form = IncomeForm(instance=income)
    return render(request, 'tracker/income_form.html', {'form': form, 'income': income})

@login_required
def income_delete_view(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        income.delete()
        return redirect('tracker:dashboard')
    return render(request, 'tracker/income_confirm_delete.html', {'income': income})

@login_required
def mutual_fund_suggestions_view(request):
    try:
        profile = request.user.profile
    except Exception:
        profile = None

    suggestions = []
    if profile:
        # Example logic for mutual fund suggestions
        if profile.risk_tolerance == 'low':
            if profile.investment_goal == 'tax_saving':
                suggestions.extend([
                    {
                        'name': 'Axis Long Term Equity Fund',
                        'type': 'ELSS',
                        'risk': 'Low to Moderate',
                        'description': 'Good for tax saving and stable returns.'
                    },
                    {
                        'name': 'HDFC TaxSaver Fund',
                        'type': 'ELSS',
                        'risk': 'Low to Moderate',
                        'description': 'Consistent performer with tax benefits.'
                    },
                    {
                        'name': 'ICICI Prudential Long Term Equity Fund',
                        'type': 'ELSS',
                        'risk': 'Low to Moderate',
                        'description': 'Balanced approach to tax saving.'
                    },
                    {
                        'name': 'Mirae Asset Tax Saver Fund',
                        'type': 'ELSS',
                        'risk': 'Low to Moderate',
                        'description': 'Growth-oriented tax saving fund.'
                    },
                    {
                        'name': 'Nippon India Tax Saver Fund',
                        'type': 'ELSS',
                        'risk': 'Low to Moderate',
                        'description': 'Well-diversified tax saving option.'
                    }
                ])
            else:
                suggestions.extend([
                    {
                        'name': 'HDFC Hybrid Debt Fund',
                        'type': 'Hybrid',
                        'risk': 'Low',
                        'description': 'Suitable for conservative investors.'
                    },
                    {
                        'name': 'ICICI Prudential Conservative Hybrid Fund',
                        'type': 'Hybrid',
                        'risk': 'Low',
                        'description': 'Balanced debt-equity allocation.'
                    },
                    {
                        'name': 'SBI Conservative Hybrid Fund',
                        'type': 'Hybrid',
                        'risk': 'Low',
                        'description': 'Stable returns with low volatility.'
                    },
                    {
                        'name': 'Kotak Debt Hybrid Fund',
                        'type': 'Hybrid',
                        'risk': 'Low',
                        'description': 'Conservative hybrid fund with consistent performance.'
                    },
                    {
                        'name': 'Axis Conservative Hybrid Fund',
                        'type': 'Hybrid',
                        'risk': 'Low',
                        'description': 'Balanced approach for conservative investors.'
                    }
                ])
        elif profile.risk_tolerance == 'medium':
            if profile.investment_goal == 'wealth_creation':
                suggestions.extend([
                    {
                        'name': 'Mirae Asset Large Cap Fund',
                        'type': 'Equity Large Cap',
                        'risk': 'Moderate',
                        'description': 'Balanced risk and return for long-term growth.'
                    },
                    {
                        'name': 'Axis Bluechip Fund',
                        'type': 'Equity Large Cap',
                        'risk': 'Moderate',
                        'description': 'Focus on blue-chip companies.'
                    },
                    {
                        'name': 'HDFC Top 100 Fund',
                        'type': 'Equity Large Cap',
                        'risk': 'Moderate',
                        'description': 'Invests in top 100 companies by market cap.'
                    },
                    {
                        'name': 'ICICI Prudential Bluechip Fund',
                        'type': 'Equity Large Cap',
                        'risk': 'Moderate',
                        'description': 'Large cap focused fund with consistent returns.'
                    },
                    {
                        'name': 'SBI Bluechip Fund',
                        'type': 'Equity Large Cap',
                        'risk': 'Moderate',
                        'description': 'Well-established large cap fund.'
                    }
                ])
            else:
                suggestions.extend([
                    {
                        'name': 'ICICI Prudential Balanced Advantage Fund',
                        'type': 'Balanced',
                        'risk': 'Moderate',
                        'description': 'Dynamic allocation for moderate risk takers.'
                    },
                    {
                        'name': 'HDFC Balanced Advantage Fund',
                        'type': 'Balanced',
                        'risk': 'Moderate',
                        'description': 'Dynamic asset allocation strategy.'
                    },
                    {
                        'name': 'Axis Balanced Fund',
                        'type': 'Balanced',
                        'risk': 'Moderate',
                        'description': 'Balanced approach to equity and debt.'
                    },
                    {
                        'name': 'SBI Balanced Advantage Fund',
                        'type': 'Balanced',
                        'risk': 'Moderate',
                        'description': 'Flexible asset allocation fund.'
                    },
                    {
                        'name': 'Kotak Balanced Advantage Fund',
                        'type': 'Balanced',
                        'risk': 'Moderate',
                        'description': 'Dynamic asset allocation with risk management.'
                    }
                ])
        elif profile.risk_tolerance == 'high':
            if profile.investment_goal == 'wealth_creation':
                suggestions.extend([
                    {
                        'name': 'Axis Small Cap Fund',
                        'type': 'Equity Small Cap',
                        'risk': 'High',
                        'description': 'High growth potential for aggressive investors.'
                    },
                    {
                        'name': 'HDFC Small Cap Fund',
                        'type': 'Equity Small Cap',
                        'risk': 'High',
                        'description': 'Focus on small-cap opportunities.'
                    },
                    {
                        'name': 'ICICI Prudential Small Cap Fund',
                        'type': 'Equity Small Cap',
                        'risk': 'High',
                        'description': 'Aggressive small cap investment strategy.'
                    },
                    {
                        'name': 'SBI Small Cap Fund',
                        'type': 'Equity Small Cap',
                        'risk': 'High',
                        'description': 'High-risk, high-return small cap fund.'
                    },
                    {
                        'name': 'Kotak Small Cap Fund',
                        'type': 'Equity Small Cap',
                        'risk': 'High',
                        'description': 'Focused on small-cap growth opportunities.'
                    }
                ])
            else:
                suggestions.extend([
                    {
                        'name': 'SBI Equity Hybrid Fund',
                        'type': 'Hybrid',
                        'risk': 'High',
                        'description': 'Aggressive allocation for high risk takers.'
                    },
                    {
                        'name': 'HDFC Equity Hybrid Fund',
                        'type': 'Hybrid',
                        'risk': 'High',
                        'description': 'Aggressive hybrid fund with equity focus.'
                    },
                    {
                        'name': 'ICICI Prudential Equity Hybrid Fund',
                        'type': 'Hybrid',
                        'risk': 'High',
                        'description': 'High equity exposure hybrid fund.'
                    },
                    {
                        'name': 'Axis Equity Hybrid Fund',
                        'type': 'Hybrid',
                        'risk': 'High',
                        'description': 'Aggressive hybrid fund with dynamic allocation.'
                    },
                    {
                        'name': 'Kotak Equity Hybrid Fund',
                        'type': 'Hybrid',
                        'risk': 'High',
                        'description': 'High-risk hybrid fund with equity bias.'
                    }
                ])
    
    context = {
        'profile': profile,
        'suggestions': suggestions,
    }
    return render(request, 'tracker/mutual_fund_suggestions.html', context)

@csrf_exempt
@login_required
def ask_gpt_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            summary = data.get('summary', {})
            
            # Compose a prompt for Cohere
            prompt = f"User's question: {question}\nFinancial summary: Income ₹{summary.get('income', 0)}, Expenses ₹{summary.get('expenses', 0)}. Please provide a personalized, actionable financial suggestion."
            
            response = co.generate(
                model="command-r-plus",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            answer = response.generations[0].text.strip()
            return JsonResponse({"answer": answer})
        except Exception as e:
            return JsonResponse({"answer": "Sorry, there was an error processing your request."}, status=500)

@login_required
def transactions_api(request):
    expenses = Expense.objects.filter(user=request.user)
    income = Income.objects.filter(user=request.user)
    data = []
    for e in expenses:
        data.append({
            'transaction_type': 'expense',
            'amount': float(e.amount),
            'date': e.date.isoformat(),
            'category': {'name': e.category.name if e.category else ''},
            'description': e.description,
        })
    for i in income:
        data.append({
            'transaction_type': 'income',
            'amount': float(i.amount),
            'date': i.date.isoformat(),
            'category': {'name': i.category.name if hasattr(i.category, 'name') else (i.category if i.category else '')},
            'description': i.description if hasattr(i, 'description') else '',
        })
    return JsonResponse(data, safe=False)

@login_required
def delete_transaction(request, pk):
    if request.method == 'POST':
        try:
            # Only try to delete as an Income
            transaction = Income.objects.get(pk=pk, user=request.user)
            transaction.delete()
            return JsonResponse({'success': True})
        except Income.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Income entry not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@login_required
def stocks_view(request):
    return render(request, 'tracker/stocks.html')

@login_required
def stock_data_api(request, symbol):
    try:
        # Check if it's an Indian stock (ends with .NS or .BO)
        is_indian_stock = symbol.endswith('.NS') or symbol.endswith('.BO')
        
        # Get stock data using yfinance
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Get historical data for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        hist = stock.history(start=start_date, end=end_date)
        
        # Process the data
        price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        change = info.get('regularMarketChange', 0)
        change_percent = info.get('regularMarketChangePercent', 0)
        volume = info.get('regularMarketVolume', 0)
        market_cap = info.get('marketCap', 0)
        
        # Process historical data
        historical = []
        for date, row in hist.iterrows():
            historical.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': float(row['Close'])
            })

        # Prepare response data
        response_data = {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'price': price,
            'change': change,
            'changePercent': change_percent,
            'volume': volume,
            'marketCap': market_cap,
            'historical': historical,
            'isIndianStock': is_indian_stock
        }

        return JsonResponse({'success': True, 'data': response_data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def trending_stocks_api(request):
    try:
        # List of popular stocks to show as trending
        trending_symbols = [
            # US Stocks
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'WMT',
            # Indian Stocks
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
            'HINDUNILVR.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS', 'BAJFINANCE.NS'
        ]
        
        stocks = []
        for symbol in trending_symbols:
            try:
                # Get stock data using yfinance
                stock = yf.Ticker(symbol)
                info = stock.info
                
                # Process the data
                price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                change = info.get('regularMarketChange', 0)
                change_percent = info.get('regularMarketChangePercent', 0)
                volume = info.get('regularMarketVolume', 0)
                
                stocks.append({
                    'symbol': symbol,
                    'name': info.get('longName', symbol),
                    'price': price,
                    'change': change,
                    'changePercent': change_percent,
                    'volume': volume,
                    'isIndianStock': symbol.endswith('.NS') or symbol.endswith('.BO')
                })
            except Exception as e:
                print(f"Error fetching data for {symbol}: {str(e)}")
                continue

        return JsonResponse({'success': True, 'stocks': stocks})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
