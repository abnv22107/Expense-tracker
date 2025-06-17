// Floating AI Chatbot Widget
(function() {
    // Create chatbot button
    const btn = document.createElement('button');
    btn.id = 'ai-chatbot-btn';
    btn.innerHTML = '<i class="fas fa-robot"></i> AI Chat';
    btn.style.position = 'fixed';
    btn.style.bottom = '30px';
    btn.style.right = '30px';
    btn.style.zIndex = '9999';
    btn.style.background = '#007bff';
    btn.style.color = '#fff';
    btn.style.border = 'none';
    btn.style.borderRadius = '50px';
    btn.style.padding = '12px 20px';
    btn.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
    btn.style.cursor = 'pointer';
    document.body.appendChild(btn);

    // Create chat window
    const chatWindow = document.createElement('div');
    chatWindow.id = 'ai-chatbot-window';
    chatWindow.style.position = 'fixed';
    chatWindow.style.bottom = '80px';
    chatWindow.style.right = '30px';
    chatWindow.style.width = '340px';
    chatWindow.style.maxHeight = '420px';
    chatWindow.style.background = '#fff';
    chatWindow.style.border = '1px solid #ddd';
    chatWindow.style.borderRadius = '12px';
    chatWindow.style.boxShadow = '0 4px 24px rgba(0,0,0,0.18)';
    chatWindow.style.display = 'none';
    chatWindow.style.flexDirection = 'column';
    chatWindow.style.overflow = 'hidden';
    chatWindow.innerHTML = `
        <div style="background:#007bff;color:#fff;padding:12px 16px;font-weight:bold;display:flex;justify-content:space-between;align-items:center;">
            <span><i class='fas fa-robot'></i> AI Chatbot</span>
            <span id='ai-chatbot-close' style='cursor:pointer;'>&times;</span>
        </div>
        <div id='ai-chatbot-messages' style='padding:12px;height:220px;overflow-y:auto;background:#f8f9fa;'></div>
        <form id='ai-chatbot-form' style='display:flex;border-top:1px solid #eee;'>
            <input id='ai-chatbot-input' type='text' placeholder='Ask me about your spending...' style='flex:1;padding:10px;border:none;outline:none;'>
            <button type='submit' style='background:#007bff;color:#fff;border:none;padding:0 16px;cursor:pointer;'>Send</button>
        </form>
    `;
    document.body.appendChild(chatWindow);

    // Toggle chat window
    btn.onclick = () => {
        chatWindow.style.display = chatWindow.style.display === 'none' ? 'flex' : 'none';
    };
    document.getElementById('ai-chatbot-close').onclick = () => {
        chatWindow.style.display = 'none';
    };

    // Chat logic
    const messagesDiv = document.getElementById('ai-chatbot-messages');
    const form = document.getElementById('ai-chatbot-form');
    const input = document.getElementById('ai-chatbot-input');

    function addMessage(text, from) {
        const msg = document.createElement('div');
        msg.style.margin = '8px 0';
        msg.style.textAlign = from === 'user' ? 'right' : 'left';
        msg.innerHTML = `<span style='display:inline-block;padding:8px 12px;border-radius:16px;background:${from==='user'?'#007bff':'#e9ecef'};color:${from==='user'?'#fff':'#333'};max-width:80%;'>${text}</span>`;
        messagesDiv.appendChild(msg);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    // Initial bot message
    addMessage('Hi! I\'m your AI assistant. Ask me anything about your expenses, savings, or investments!', 'bot');

    form.onsubmit = async function(e) {
        e.preventDefault();
        const userMsg = input.value.trim();
        if (!userMsg) return;
        addMessage(userMsg, 'user');
        input.value = '';
        setTimeout(async () => {
            let response = '';
            const msg = userMsg.toLowerCase();
            // Fetch all transactions for income/expense summary
            let summary = { income: 0, expenses: 0, data: [] };
            try {
                const res = await fetch('/tracker/api/transactions/');
                if (res.ok) {
                    const transactions = await res.json();
                    summary.data = transactions;
                    transactions.forEach(t => {
                        if (t.transaction_type === 'income') summary.income += parseFloat(t.amount);
                        if (t.transaction_type === 'expense') summary.expenses += parseFloat(t.amount);
                    });
                }
            } catch {}
            // Send to backend for GPT answer
            try {
                const gptRes = await fetch('/tracker/api/ask_gpt/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: userMsg,
                        summary: {
                            income: summary.income,
                            expenses: summary.expenses,
                            // Optionally send more data if needed
                        }
                    })
                });
                if (gptRes.ok) {
                    const gptData = await gptRes.json();
                    response = gptData.answer || 'Sorry, I could not get a response from the AI.';
                } else {
                    response = 'Sorry, I could not get a response from the AI.';
                }
            } catch {
                response = 'Sorry, I could not get a response from the AI.';
            }
            addMessage(response, 'bot');
        }, 800);
    };
})(); 