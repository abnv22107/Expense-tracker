from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Expense, Category, Income, UserProfile

class ExpenseForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="Select a category",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    description = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = Expense
        fields = ['description', 'amount', 'date', 'category', 'notes']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Get categories and sort them by name
            categories = Category.objects.filter(user=user).order_by('name')
            self.fields['category'].queryset = categories

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['description', 'amount', 'date', 'category', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['risk_tolerance', 'investment_goal', 'investment_horizon_years']
        widgets = {
            'investment_horizon_years': forms.NumberInput(attrs={'min': 1, 'max': 50}),
        } 