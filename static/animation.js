// --- Card Fade-in Animation on Scroll ---

function initCardObserver() {
    const observer = new IntersectionObserver(
        (entries, observer) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target); // Stop observing once visible
                }
            });
        },
        {
            rootMargin: '0px',
            threshold: 0.1 // Trigger when 10% of the item is visible
        }
    );

    // Find all cards that haven't been animated yet and observe them
    const cardsToAnimate = document.querySelectorAll('.card:not(.is-visible)');
    cardsToAnimate.forEach((card) => {
        observer.observe(card);
    });
}