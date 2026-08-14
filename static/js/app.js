const chartSection = document.getElementById('chartSection');
const chartTitle = document.getElementById('chartTitle');
let priceChartInstance = null;
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('csvFile');
const statusMsg = document.getElementById('statusMsg');
const resultsSection = document.getElementById('resultsSection');
const subscriptionCards = document.getElementById('subscriptionCards');
const simulatorList = document.getElementById('simulatorList');
const totalSavings = document.getElementById('totalSavings');

let currentSubscriptions = [];

function riskClass(score) {
    if (score >= 0.6) return 'risk-high';
    if (score >= 0.4) return 'risk-medium';
    return 'risk-low';
}

function renderResults(subscriptions) {
    currentSubscriptions = subscriptions;
    subscriptionCards.innerHTML = '';
    simulatorList.innerHTML = '';

    subscriptions.forEach((sub, index) => {
        // Subscription card
      const card = document.createElement('div');
        card.className = 'sub-card';
        card.innerHTML = `
            <div class="sub-info" style="cursor: pointer;">
                <h3>${sub.merchant}</h3>
                <p>₹${sub.avg_amount} per charge · ₹${sub.annual_cost}/year · ${sub.risk_reasons}</p>
            </div>
            <div class="card-actions">
                <span class="risk-badge ${riskClass(sub.risk_score)}">${Math.round(sub.risk_score * 100)}% risk</span>
                <button class="feedback-btn confirm-btn" data-id="${sub.id}" data-type="confirmed">Still use it</button>
                <button class="feedback-btn wrong-btn" data-id="${sub.id}" data-type="cancelled">Want to cancel</button>
            </div>
        `;
        card.querySelector('.sub-info').addEventListener('click', () => showPriceChart(sub.id, sub.merchant));
        subscriptionCards.appendChild(card);

        // Simulator row
        const row = document.createElement('div');
        row.className = 'simulator-row';
        row.innerHTML = `
            <input type="checkbox" class="sim-checkbox" data-index="${index}">
            <label>${sub.merchant} — ₹${sub.annual_cost}/year</label>
        `;
        simulatorList.appendChild(row);
    });

    document.querySelectorAll('.sim-checkbox').forEach(cb => {
        cb.addEventListener('change', updateSavings);
    });

    document.querySelectorAll('.feedback-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            submitFeedback(btn.dataset.id, btn.dataset.type, btn);
        });
    });

    updateSavings();
    resultsSection.classList.remove('hidden');
}

async function showPriceChart(subscriptionId, merchantName) {
    try {
        const response = await fetch(`/api/subscriptions/price-history/${subscriptionId}/`);
        const data = await response.json();

        const labels = data.history.map(h => h.date);
        const amounts = data.history.map(h => h.amount);

        if (priceChartInstance) {
            priceChartInstance.destroy();
        }

        const ctx = document.getElementById('priceChart').getContext('2d');
        priceChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `${merchantName} - Price Over Time`,
                    data: amounts,
                    borderColor: '#F5A623',
                    backgroundColor: 'rgba(245, 166, 35, 0.1)',
                    tension: 0.2,
                    fill: true,
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: false } }
            }
        });

        chartTitle.textContent = `Price History: ${merchantName}`;
        chartSection.classList.remove('hidden');
        chartSection.scrollIntoView({ behavior: 'smooth' });
    } catch (e) {
        console.error('Failed to load price history', e);
    }
}

async function submitFeedback(subscriptionId, feedbackType, buttonEl) {
    try {
       const response = await fetch(`/api/subscriptions/feedback/${subscriptionId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CSRF_TOKEN,
            },
            body: JSON.stringify({ feedback_type: feedbackType }),
        });
        if (response.ok) {
            const card = buttonEl.closest('.sub-card');
            card.style.opacity = '0.5';
            const actionsDiv = buttonEl.closest('.card-actions');
            actionsDiv.querySelectorAll('.feedback-btn').forEach(b => b.disabled = true);
            const note = document.createElement('span');
            note.className = 'feedback-note';
            note.textContent = feedbackType === 'confirmed' ? 'Marked as still used' : 'Marked to cancel';
            actionsDiv.appendChild(note);
        }
    } catch (e) {
        console.error('Feedback submission failed', e);
    }
}

function updateSavings() {
    let total = 0;
    document.querySelectorAll('.sim-checkbox:checked').forEach(cb => {
        const idx = cb.getAttribute('data-index');
        total += currentSubscriptions[idx].annual_cost;
    });
    totalSavings.textContent = total > 0
        ? `You would save ₹${total.toLocaleString()} per year`
        : '';
}

uploadBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
        statusMsg.textContent = 'Please choose a CSV file first.';
        statusMsg.style.color = '#E24A3B';
        return;
    }

    if (!file.name.toLowerCase().endsWith('.csv')) {
        statusMsg.textContent = 'Please upload a .csv file — other formats aren\'t supported yet.';
        statusMsg.style.color = '#E24A3B';
        return;
    }

    uploadBtn.disabled = true;
    const originalText = uploadBtn.textContent;
    uploadBtn.innerHTML = '<span class="spinner"></span>Analyzing...';
    statusMsg.style.color = '#5A6472';
    statusMsg.textContent = 'Reading your statement and detecting subscriptions...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/transactions/upload/', {
            method: 'POST',
            headers: { 'X-CSRFToken': window.CSRF_TOKEN },
            body: formData,
        });

        if (!response.ok) {
            let message = 'Something went wrong while analyzing your file.';
            try {
                const err = await response.json();
                if (err.error) message = err.error;
            } catch (_) {}

            if (response.status === 403) {
                message = 'Your session expired — please log in again.';
            } else if (response.status === 400) {
                message = message.includes('CSV')
                    ? message
                    : 'That file couldn\'t be read. Make sure it has "date", "raw_merchant_text", and "amount" columns.';
            } else if (response.status >= 500) {
                message = 'Server error — please try again in a moment.';
            }

            statusMsg.textContent = message;
            statusMsg.style.color = '#E24A3B';
            return;
        }

        const data = await response.json();

        if (data.subscriptions.length === 0) {
            statusMsg.textContent = 'No recurring subscriptions were detected in this statement.';
            statusMsg.style.color = '#5A6472';
            resultsSection.classList.add('hidden');
            return;
        }

        statusMsg.textContent = `Found ${data.subscriptions.length} subscription${data.subscriptions.length > 1 ? 's' : ''}.`;
        statusMsg.style.color = '#2EC4B6';
        renderResults(data.subscriptions);
    } catch (e) {
        statusMsg.textContent = 'Could not connect to the server. Please check your connection and try again.';
        statusMsg.style.color = '#E24A3B';
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = originalText;
    }
});