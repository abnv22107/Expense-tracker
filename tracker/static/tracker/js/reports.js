document.addEventListener('DOMContentLoaded', () => {
    const categoryChart = document.getElementById('categoryChart');
    const trendChart = document.getElementById('trendChart');
    const dateFrom = document.getElementById('date_from');
    const dateTo = document.getElementById('date_to');

    // Initialize charts if elements exist
    if (categoryChart) {
        initializeCategoryChart();
    }
    if (trendChart) {
        initializeTrendChart();
    }

    // Set up date range change handlers
    if (dateFrom && dateTo) {
        dateFrom.addEventListener('change', updateCharts);
        dateTo.addEventListener('change', updateCharts);
    }
});

async function fetchTransactionData() {
    const dateFrom = document.getElementById('date_from').value;
    const dateTo = document.getElementById('date_to').value;
    
    try {
        const response = await fetch(`/tracker/api/transactions/?date_from=${dateFrom}&date_to=${dateTo}`);
        if (!response.ok) {
            throw new Error('Failed to fetch transactions');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching transactions:', error);
        showToast('Error loading transaction data', 'danger');
        return [];
    }
}

async function initializeCategoryChart() {
    const transactions = await fetchTransactionData();
    const categories = {};

    transactions.forEach(tx => {
        if (tx.transaction_type === 'expense') {
            categories[tx.category.name] = (categories[tx.category.name] || 0) + parseFloat(tx.amount);
        }
    });

    const ctx = document.getElementById('categoryChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(categories),
            datasets: [{
                label: 'Expenses by Category',
                data: Object.values(categories),
                backgroundColor: [
                    '#0d6efd', '#dc3545', '#ffc107', '#198754', '#6f42c1', '#fd7e14', '#20c997', '#0dcaf0'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                title: {
                    display: true,
                    text: 'Expenses by Category'
                }
            }
        }
    });
}

async function initializeTrendChart() {
    const transactions = await fetchTransactionData();
    const monthlyData = {};

    transactions.forEach(tx => {
        const date = new Date(tx.date);
        const monthYear = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        
        if (!monthlyData[monthYear]) {
            monthlyData[monthYear] = { income: 0, expense: 0 };
        }
        
        if (tx.transaction_type === 'income') {
            monthlyData[monthYear].income += parseFloat(tx.amount);
        } else {
            monthlyData[monthYear].expense += parseFloat(tx.amount);
        }
    });

    const months = Object.keys(monthlyData).sort();
    const incomeData = months.map(month => monthlyData[month].income);
    const expenseData = months.map(month => monthlyData[month].expense);

    const ctx = document.getElementById('trendChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: months,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    fill: true
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'Monthly Income vs Expenses'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + value;
                        }
                    }
                }
            }
        }
    });
}

async function updateCharts() {
    if (categoryChart) {
        initializeCategoryChart();
    }
    if (trendChart) {
        initializeTrendChart();
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