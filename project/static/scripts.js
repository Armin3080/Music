document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const statusText = document.getElementById('status-text');
    const confidenceText = document.getElementById('confidence');

    // Update status every 2 seconds
    setInterval(updateStatus, 2000);

    startBtn.addEventListener('click', () => {
        fetch('/start_auth', { method: 'POST' })
            .then(res => res.json())
            .then(data => statusText.textContent = data.status);
    });

    stopBtn.addEventListener('click', () => {
        fetch('/stop_auth', { method: 'POST' })
            .then(res => res.json())
            .then(data => statusText.textContent = data.status);
    });

    function updateStatus() {
        fetch('/status')
            .then(res => res.json())
            .then(data => {
                statusText.textContent = data.status;
                confidenceText.textContent = `Progress: ${data.progress}`;
            });
    }
});