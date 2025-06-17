document.addEventListener('DOMContentLoaded', () => {
    const expensesTableBody = document.getElementById('expensesTableBody');
    const searchInput = document.getElementById('searchInput');
    const clearSearch = document.getElementById('clearSearch');
    let transactions = [];

    async function fetchTransactions() {
        try {
            const response = await fetch('/tracker/api/transactions/');
            if (response.ok) {
                transactions = await response.json();
                renderTable();
            }
        } catch (error) {
            console.error('Error fetching transactions:', error);
            showToast('Error loading transactions', 'danger');
        }
    }

    function renderTable(filtered = null) {
        if (!expensesTableBody) return;
        
        expensesTableBody.innerHTML = '';
        const data = filtered || transactions;
        if (data.length === 0) {
            expensesTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No transactions found.</td></tr>';
            return;
        }
        data.forEach(tx => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(tx.date).toLocaleDateString()}</td>
                <td>${tx.description}</td>
                <td class="${tx.type === 'income' ? 'text-success' : 'text-danger'}">
                    ${tx.type === 'income' ? '+' : '-'}₹${Math.abs(tx.amount).toFixed(2)}
                </td>
                <td>${tx.type}</td>
                <td>${tx.category}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteExpense(${tx.id})"><i class="fas fa-trash"></i></button>
                </td>
            `;
            expensesTableBody.appendChild(row);
        });
    }

    window.deleteExpense = async function(id) {
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
                transactions = transactions.filter(tx => tx.id !== id);
                renderTable();
                showToast('Transaction deleted successfully', 'success');
            } else {
                throw new Error('Failed to delete transaction');
            }
        } catch (error) {
            console.error('Error deleting transaction:', error);
            showToast('Error deleting transaction', 'danger');
        }
    };

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const filtered = transactions.filter(tx =>
                tx.description.toLowerCase().includes(query) ||
                tx.category.toLowerCase().includes(query)
            );
            renderTable(filtered);
        });
    }

    if (clearSearch) {
        clearSearch.addEventListener('click', function() {
            searchInput.value = '';
            renderTable();
        });
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

    // Helper function to show toast notifications
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

    // Initial load
    fetchTransactions();
}); 