// Initialize variables
let transactions = [];
let totalBalance = 0;
let totalIncome = 0;
let totalExpenses = 0;

// DOM Elements
const transactionForm = document.getElementById('transactionForm');
const transactionList = document.getElementById('transactionList');
const totalBalanceElement = document.getElementById('totalBalance');
const totalIncomeElement = document.getElementById('totalIncome');
const totalExpensesElement = document.getElementById('totalExpenses');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    fetchTransactions();
});

if (transactionForm) {
    transactionForm.addEventListener('submit', (e) => {
        e.preventDefault();
        addTransaction();
    });
}

// Functions
async function fetchTransactions() {
    try {
        const response = await fetch('/tracker/api/transactions/');
        if (response.ok) {
            transactions = await response.json();
            updateUI();
        }
    } catch (error) {
        console.error('Error fetching transactions:', error);
        showToast('Error loading transactions', 'danger');
    }
}

async function addTransaction() {
    const formData = new FormData(transactionForm);
    const data = {
        description: formData.get('description'),
        amount: parseFloat(formData.get('amount')),
        type: formData.get('type'),
        category: formData.get('category'),
        date: new Date().toISOString()
    };

    try {
        const response = await fetch('/tracker/api/transactions/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const transaction = await response.json();
            transactions.push(transaction);
            updateUI();
            transactionForm.reset();
            showToast('Transaction added successfully', 'success');
        } else {
            throw new Error('Failed to add transaction');
        }
    } catch (error) {
        console.error('Error adding transaction:', error);
        showToast('Error adding transaction', 'danger');
    }
}

async function deleteTransaction(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }

    try {
        const response = await fetch(`/tracker/api/transactions/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            transactions = transactions.filter(transaction => transaction.id !== id);
            updateUI();
            showToast('Transaction deleted successfully', 'success');
        } else {
            throw new Error('Failed to delete transaction');
        }
    } catch (error) {
        console.error('Error deleting transaction:', error);
        showToast('Error deleting transaction', 'danger');
    }
}

function updateUI() {
    if (!transactionList) return;

    // Clear transaction list
    transactionList.innerHTML = '';

    // Reset totals
    totalBalance = 0;
    totalIncome = 0;
    totalExpenses = 0;

    // Calculate totals and display transactions
    transactions.forEach(transaction => {
        if (transaction.type === 'income') {
            totalIncome += transaction.amount;
        } else {
            totalExpenses += transaction.amount;
        }

        const row = document.createElement('tr');
        row.className = 'new-transaction';
        row.innerHTML = `
            <td>${transaction.description}</td>
            <td class="${transaction.type === 'income' ? 'text-success' : 'text-danger'}">
                ${transaction.type === 'income' ? '+' : '-'}₹${Math.abs(transaction.amount).toFixed(2)}
            </td>
            <td>${transaction.type}</td>
            <td>${transaction.category}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deleteTransaction(${transaction.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        transactionList.appendChild(row);
    });

    // Update summary cards if they exist
    if (totalBalanceElement) {
        totalBalance = totalIncome - totalExpenses;
        totalBalanceElement.textContent = `₹${totalBalance.toFixed(2)}`;
        totalIncomeElement.textContent = `₹${totalIncome.toFixed(2)}`;
        totalExpensesElement.textContent = `₹${totalExpenses.toFixed(2)}`;

        // Add color to balance
        if (totalBalance < 0) {
            totalBalanceElement.parentElement.classList.remove('bg-primary');
            totalBalanceElement.parentElement.classList.add('bg-danger');
        } else {
            totalBalanceElement.parentElement.classList.remove('bg-danger');
            totalBalanceElement.parentElement.classList.add('bg-primary');
        }
    }
}

function showToast(message, type = 'info') {
    const toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    toastContainer.innerHTML = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    document.body.appendChild(toastContainer);
    const toast = new bootstrap.Toast(toastContainer.querySelector('.toast'));
    toast.show();
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Category icons mapping
const categoryIcons = {
    food: 'fas fa-utensils',
    transport: 'fas fa-car',
    utilities: 'fas fa-bolt',
    entertainment: 'fas fa-film',
    other: 'fas fa-ellipsis-h'
}; 