// AIFormation - Main JavaScript

// Auto-refresh stats (optional)
function refreshStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            console.log('Stats updated:', data);
            // Update UI elements if needed
        })
        .catch(error => console.error('Error fetching stats:', error));
}

// Check for updates every 30 seconds (optional)
// setInterval(refreshStats, 30000);

// Smooth scroll for anchor links
document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Add loading indicator for buttons
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-primary') && e.target.tagName === 'BUTTON') {
        const originalText = e.target.innerHTML;
        e.target.innerHTML = '⏳ Bezig...';
        e.target.disabled = true;

        // Re-enable after 2 seconds (example)
        setTimeout(() => {
            e.target.innerHTML = originalText;
            e.target.disabled = false;
        }, 2000);
    }
});

// Console welcome message
console.log('%c🤖 AIFormation Web Interface', 'font-size: 20px; font-weight: bold; color: #4f46e5;');
console.log('%cAI-Driven Development Orchestration System', 'font-size: 14px; color: #6b7280;');
