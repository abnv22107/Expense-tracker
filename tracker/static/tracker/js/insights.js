// AI Insights and Recommendations
document.addEventListener('DOMContentLoaded', function() {
    // Initialize expense analysis
    analyzeExpenses();
    
    // Initialize smart recommendations
    generateSmartRecommendations();
    
    // Set up investment analysis
    const analyzeInvestmentBtn = document.getElementById('analyzeInvestment');
    if (analyzeInvestmentBtn) {
        analyzeInvestmentBtn.addEventListener('click', analyzeInvestment);
    }

    // Fill recent trends if present
    const trendsDiv = document.getElementById('recentTrends');
    if (trendsDiv && window.getAISpendingTrends) {
        trendsDiv.textContent = window.getAISpendingTrends();
    }
});

// Conversational AI Suggestions
function getConversationalAISuggestions(expenses) {
    if (!expenses || expenses.length === 0) return [
        "No expenses found. Start adding expenses to get AI insights."
    ];
    const now = new Date();
    const categories = {};
    let totalSpent = 0;
    let lastMonthSpent = 0;
    let thisMonthSpent = 0;
    let months = {};
    let allAmounts = [];
    expenses.forEach(expense => {
        if (expense.transaction_type !== 'expense') return;
        const date = new Date(expense.date);
        const monthKey = `${date.getFullYear()}-${date.getMonth()}`;
        months[monthKey] = (months[monthKey] || 0) + parseFloat(expense.amount);
        categories[expense.category.name] = (categories[expense.category.name] || 0) + parseFloat(expense.amount);
        totalSpent += parseFloat(expense.amount);
        allAmounts.push(parseFloat(expense.amount));
        if (date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear()) {
            thisMonthSpent += parseFloat(expense.amount);
        }
        if (date.getMonth() === now.getMonth() - 1 && date.getFullYear() === now.getFullYear()) {
            lastMonthSpent += parseFloat(expense.amount);
        }
    });
    // Find highest spending category
    const highestCategory = Object.entries(categories).sort(([,a], [,b]) => b - a)[0];
    // Detect spike
    let spikeMsg = '';
    if (lastMonthSpent > 0 && thisMonthSpent > lastMonthSpent * 1.2) {
        spikeMsg = `Heads up! Your spending this month (₹${thisMonthSpent.toFixed(2)}) is over 20% higher than last month (₹${lastMonthSpent.toFixed(2)}). Consider reviewing large or unusual transactions.`;
    }
    // Category advice: consistent overspending
    let overspendMsg = '';
    if (highestCategory) {
        let overspendMonths = 0;
        Object.keys(months).forEach(monthKey => {
            // For each month, check if this category is >40% of that month's total
            let monthTotal = 0;
            let catTotal = 0;
            expenses.forEach(exp => {
                if (exp.transaction_type !== 'expense') return;
                const date = new Date(exp.date);
                const key = `${date.getFullYear()}-${date.getMonth()}`;
                if (key === monthKey) {
                    monthTotal += parseFloat(exp.amount);
                    if (exp.category.name === highestCategory[0]) catTotal += parseFloat(exp.amount);
                }
            });
            if (monthTotal > 0 && catTotal > monthTotal * 0.4) overspendMonths++;
        });
        if (overspendMonths >= 3) {
            overspendMsg = `You've been consistently spending a large portion on ${highestCategory[0]} for ${overspendMonths} months. Try reducing your ${highestCategory[0]} expenses by 10% next month!`;
        }
    }
    // Unusual transactions
    let unusualMsg = '';
    const avg = allAmounts.reduce((a,b) => a+b, 0) / allAmounts.length;
    const unusual = expenses.filter(e => e.transaction_type === 'expense' && parseFloat(e.amount) > avg * 2);
    if (unusual.length > 0) {
        unusualMsg = `I noticed ${unusual.length} unusually large transaction${unusual.length>1?'s':''} (over 2x your average expense). Review: ` + unusual.map(e => `${e.category.name} (₹${parseFloat(e.amount).toFixed(2)})`).join(', ') + '.';
    }
    // Simulated typical user comparison
    let typicalMsg = '';
    const typicalMonthly = 20000; // Simulated
    if (thisMonthSpent > typicalMonthly * 1.2) {
        typicalMsg = `Compared to a typical user (₹${typicalMonthly}/month), your spending this month is quite high. Consider setting a budget!`;
    } else if (thisMonthSpent < typicalMonthly * 0.8) {
        typicalMsg = `Great job! Your spending this month is lower than a typical user (₹${typicalMonthly}/month).`;
    }
    // Natural language summary
    const summary = `So far, you've spent ₹${totalSpent.toFixed(2)}. Your top category is ${highestCategory ? highestCategory[0] : 'N/A'} (₹${highestCategory ? highestCategory[1].toFixed(2) : '0'}).`;
    // Suggestions array
    const suggestions = [summary];
    if (spikeMsg) suggestions.push(spikeMsg);
    if (overspendMsg) suggestions.push(overspendMsg);
    if (unusualMsg) suggestions.push(unusualMsg);
    if (typicalMsg) suggestions.push(typicalMsg);
    suggestions.push("Tip: Review your monthly trends and set budgets for better control. I'm here to help with more insights!");
    return suggestions;
}

// For chatbot: summarize last 3 months trends
window.getAISpendingTrends = function() {
    // This function will be called by the page to fill the trends card
    // It fetches the last 3 months' spending
    // This is a synchronous version for demo; you may want to make it async if needed
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/tracker/api/transactions/', false);
    xhr.send(null);
    if (xhr.status !== 200) return 'No spending data available.';
    const expenses = JSON.parse(xhr.responseText);
    if (!expenses.length) return 'No spending data available.';
    const now = new Date();
    let months = [];
    for (let i = 2; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
        months.push({
            key: `${d.getFullYear()}-${d.getMonth()}`,
            label: d.toLocaleString('default', { month: 'short', year: 'numeric' }),
            total: 0
        });
    }
    expenses.forEach(exp => {
        if (exp.transaction_type !== 'expense') return;
        const date = new Date(exp.date);
        const key = `${date.getFullYear()}-${date.getMonth()}`;
        const m = months.find(m => m.key === key);
        if (m) m.total += parseFloat(exp.amount);
    });
    return 'Last 3 months spending: ' + months.map(m => `${m.label}: ₹${m.total.toFixed(2)}`).join(', ');
};

// Use new suggestions in analyzeExpenses
async function analyzeExpenses() {
    try {
        const response = await fetch('/tracker/api/transactions/');
        if (!response.ok) {
            throw new Error('Failed to fetch transactions');
        }
        const expenses = await response.json();
        const insights = getConversationalAISuggestions(expenses);
        document.getElementById('expenseAnalysis').innerHTML = `
            <div class="list-group">
                ${insights.map(insight => `
                    <div class="list-group-item">
                        <i class="fas fa-info-circle text-primary me-2"></i>
                        ${insight}
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Error analyzing expenses:', error);
        document.getElementById('expenseAnalysis').innerHTML = `
            <div class="alert alert-danger">
                Error analyzing expenses. Please try again later.
            </div>
        `;
    }
}

// Generate smart recommendations
async function generateSmartRecommendations() {
    try {
        const response = await fetch('/tracker/api/transactions/');
        if (!response.ok) {
            throw new Error('Failed to fetch transactions');
        }
        
        const expenses = await response.json();
        
        if (expenses.length === 0) {
            document.getElementById('smartRecommendations').innerHTML = `
                <div class="alert alert-info">
                    Add more expenses to get personalized recommendations.
                </div>
            `;
            return;
        }

        // Calculate monthly spending
        const monthlySpending = expenses.reduce((total, expense) => {
            if (expense.transaction_type === 'expense') {
                const date = new Date(expense.date);
                const now = new Date();
                if (date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear()) {
                    return total + parseFloat(expense.amount);
                }
            }
            return total;
        }, 0);

        // Generate recommendations based on spending patterns
        const recommendations = [
            {
                title: 'Budget Optimization',
                description: `Consider setting a monthly budget of ₹${(monthlySpending * 0.9).toFixed(2)} to save 10%`
            },
            {
                title: 'Expense Tracking',
                description: 'Try to log expenses daily for better tracking'
            },
            {
                title: 'Category Analysis',
                description: 'Review your spending categories monthly to identify saving opportunities'
            }
        ];

        // Display recommendations
        document.getElementById('smartRecommendations').innerHTML = `
            <div class="list-group">
                ${recommendations.map(rec => `
                    <div class="list-group-item">
                        <h6 class="mb-1">${rec.title}</h6>
                        <p class="mb-0">${rec.description}</p>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Error generating recommendations:', error);
        document.getElementById('smartRecommendations').innerHTML = `
            <div class="alert alert-danger">
                Error generating recommendations. Please try again later.
            </div>
        `;
    }
}

// Analyze investment opportunities
async function analyzeInvestment() {
    const amount = parseFloat(document.getElementById('investmentAmount').value);
    
    if (!amount || amount <= 0) {
        document.getElementById('investmentRecommendations').innerHTML = `
            <div class="alert alert-warning">
                Please enter a valid amount greater than 0.
            </div>
        `;
        return;
    }

    try {
        // Simulate AI-powered investment recommendations
        const recommendations = [
            {
                type: 'Stocks',
                description: 'Consider investing in index funds for long-term growth',
                allocation: '40%',
                amount: (amount * 0.4).toFixed(2)
            },
            {
                type: 'Bonds',
                description: 'Government bonds for stable returns',
                allocation: '30%',
                amount: (amount * 0.3).toFixed(2)
            },
            {
                type: 'Real Estate',
                description: 'REITs for real estate exposure',
                allocation: '20%',
                amount: (amount * 0.2).toFixed(2)
            },
            {
                type: 'Cash',
                description: 'Emergency fund and short-term needs',
                allocation: '10%',
                amount: (amount * 0.1).toFixed(2)
            }
        ];

        // Display recommendations
        document.getElementById('investmentRecommendations').innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Description</th>
                            <th>Allocation</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${recommendations.map(rec => `
                            <tr>
                                <td>${rec.type}</td>
                                <td>${rec.description}</td>
                                <td>${rec.allocation}</td>
                                <td>₹${rec.amount}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="alert alert-info mt-3">
                <i class="fas fa-info-circle"></i>
                These are AI-generated recommendations. Please consult with a financial advisor before making investment decisions.
            </div>
        `;
    } catch (error) {
        console.error('Error analyzing investment:', error);
        document.getElementById('investmentRecommendations').innerHTML = `
            <div class="alert alert-danger">
                Error generating investment recommendations. Please try again later.
            </div>
        `;
    }
} 