// The Bobbing Channel - Catalog Explorer JavaScript

// Random item navigation
async function goToRandom(event) {
    event.preventDefault();
    try {
        const response = await fetch('/random');
        const data = await response.json();
        if (data.identifier) {
            window.location.href = `/item/${data.identifier}`;
        }
    } catch (error) {
        console.error('Error getting random item:', error);
    }
}

// Night mode toggle
function toggleNightMode() {
    document.body.classList.toggle('night-mode');
    localStorage.setItem('nightMode', document.body.classList.contains('night-mode'));
    
    // Adjust static effect
    const staticEl = document.querySelector('.tv-static');
    if (document.body.classList.contains('night-mode')) {
        staticEl.style.setProperty('--static-opacity', '0.01');
    } else {
        staticEl.style.setProperty('--static-opacity', '0.03');
    }
}

// Load saved night mode preference
document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('nightMode') === 'true') {
        document.body.classList.add('night-mode');
    }
    
    // Add TV turn-on effect
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s';
        document.body.style.opacity = '1';
    }, 100);
    
    // Simulate signal strength variation
    setInterval(() => {
        const strength = 70 + Math.random() * 20;
        const bars = '█'.repeat(Math.floor(strength / 10)) + '░'.repeat(10 - Math.floor(strength / 10));
        const signalEl = document.getElementById('signal-strength');
        if (signalEl) {
            signalEl.textContent = bars;
            signalEl.parentElement.innerHTML = signalEl.parentElement.innerHTML.replace(/\d+%/, Math.floor(strength) + '%');
        }
    }, 3000);
    
    // Add glitch effect on hover
    document.querySelectorAll('.media-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.animation = 'glitch 0.3s';
            setTimeout(() => {
                card.style.animation = '';
            }, 300);
        });
    });
    
    // Lazy load images with TV static placeholder
    const images = document.querySelectorAll('.media-thumbnail img');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.style.opacity = '0';
                img.onload = () => {
                    img.style.transition = 'opacity 0.5s';
                    img.style.opacity = '1';
                };
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
});

// Glitch animation
const style = document.createElement('style');
style.textContent = `
    @keyframes glitch {
        0% {
            transform: translateX(0);
        }
        20% {
            transform: translateX(-2px);
        }
        40% {
            transform: translateX(2px);
        }
        60% {
            transform: translateX(-1px);
        }
        80% {
            transform: translateX(1px);
        }
        100% {
            transform: translateX(0);
        }
    }
`;
document.head.appendChild(style);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Press 'R' for random
    if (e.key === 'r' || e.key === 'R') {
        goToRandom(e);
    }
    // Press 'N' for night mode
    if (e.key === 'n' || e.key === 'N') {
        toggleNightMode();
    }
    // Press '/' to focus search
    if (e.key === '/') {
        e.preventDefault();
        const searchInput = document.querySelector('.retro-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
});

// Add channel switching sound effect (visual feedback)
function channelSwitch() {
    const body = document.body;
    body.style.filter = 'brightness(2)';
    setTimeout(() => {
        body.style.filter = 'brightness(0)';
        setTimeout(() => {
            body.style.filter = 'brightness(1)';
        }, 50);
    }, 50);
}

// Channel switch on pagination
document.querySelectorAll('.page-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        channelSwitch();
    });
});