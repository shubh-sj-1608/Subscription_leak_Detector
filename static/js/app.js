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
            headers: { 'Content-Type': 'application/json' },
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
        return;
    }

    statusMsg.textContent = 'Analyzing...';
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/transactions/upload/', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const err = await response.json();
            statusMsg.textContent = 'Error: ' + (err.error || 'something went wrong');
            return;
        }

        const data = await response.json();
        statusMsg.textContent = `Found ${data.subscriptions.length} subscriptions.`;
        renderResults(data.subscriptions);
    } catch (e) {
        statusMsg.textContent = 'Error connecting to server.';
    }
});