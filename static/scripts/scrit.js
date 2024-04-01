const darkModeToggle = document.getElementById('dark-mode-toggle');

darkModeToggle.addEventListener('click', () => {
document.body.classList.toggle('dark-mode');
});

const scrollToTopButton = document.getElementById('scroll-to-top-button');
const scrollThreshold = 200; // Adjust this value to your preference

window.addEventListener('scroll', () => {
    if (window.scrollY >= scrollThreshold) {
           scrollToTopButton.style.opacity = 1;
    } else {
           scrollToTopButton.style.opacity = 0;
    }
});
scrollToTopButton.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});