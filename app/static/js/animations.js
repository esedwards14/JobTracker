/* ============================================
   Modern Animations & Interactions
   ============================================ */

(function() {
    'use strict';

    // ==========================================
    // Scroll-based Reveal Animations
    // ==========================================
    const observerOptions = {
        root: null,
        rootMargin: '0px 0px -50px 0px',
        threshold: 0.1
    };

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Unobserve after revealing (animate once)
                revealObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    function initScrollAnimations() {
        const animatedElements = document.querySelectorAll(
            '.fade-in, .fade-in-left, .fade-in-right, .scale-in, .stagger-children'
        );
        animatedElements.forEach(el => {
            revealObserver.observe(el);
        });
    }

    // ==========================================
    // Navbar scroll effect
    // ==========================================
    function initNavScroll() {
        const nav = document.querySelector('nav');
        if (!nav) return;

        nav.classList.add('glass-nav');

        let lastScroll = 0;
        window.addEventListener('scroll', () => {
            const currentScroll = window.scrollY;
            if (currentScroll > 20) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
            lastScroll = currentScroll;
        }, { passive: true });
    }

    // ==========================================
    // Parallax background orbs
    // ==========================================
    function initParallaxBackground() {
        // Only add if not already present
        if (document.querySelector('.parallax-bg')) return;

        const bg = document.createElement('div');
        bg.className = 'parallax-bg';
        bg.innerHTML = `
            <div class="orb orb-1"></div>
            <div class="orb orb-2"></div>
            <div class="orb orb-3"></div>
        `;
        document.body.prepend(bg);

        // Subtle mouse-driven parallax for orbs
        let animFrame;
        document.addEventListener('mousemove', (e) => {
            if (animFrame) cancelAnimationFrame(animFrame);
            animFrame = requestAnimationFrame(() => {
                const x = (e.clientX / window.innerWidth - 0.5) * 2;
                const y = (e.clientY / window.innerHeight - 0.5) * 2;

                const orbs = bg.querySelectorAll('.orb');
                orbs.forEach((orb, i) => {
                    const speed = (i + 1) * 3;
                    orb.style.transform = `translate(${x * speed}px, ${y * speed}px)`;
                });
            });
        }, { passive: true });
    }

    // ==========================================
    // Counter animation for stat numbers
    // ==========================================
    function animateCounter(element, target, duration) {
        if (isNaN(target)) return;

        const start = 0;
        const startTime = performance.now();
        const isPercent = element.textContent.includes('%');
        const suffix = isPercent ? '%' : '';

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (target - start) * eased);

            element.textContent = current + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    function initCounterAnimations() {
        const counters = document.querySelectorAll('.counter-animate');
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const text = el.textContent.trim();
                    const value = parseInt(text.replace(/[^0-9]/g, ''));
                    if (!isNaN(value)) {
                        animateCounter(el, value, 800);
                    }
                    counterObserver.unobserve(el);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(counter => counterObserver.observe(counter));
    }

    // ==========================================
    // HTMX content load animation
    // ==========================================
    function initHtmxAnimations() {
        document.addEventListener('htmx:afterSwap', function(e) {
            // Re-initialize scroll animations for new content
            setTimeout(() => {
                initScrollAnimations();
                initCounterAnimations();
            }, 50);
        });

        document.addEventListener('htmx:beforeSwap', function(e) {
            const target = e.detail.target;
            if (target) {
                target.style.opacity = '0.5';
                target.style.transition = 'opacity 0.2s';
            }
        });

        document.addEventListener('htmx:afterSwap', function(e) {
            const target = e.detail.target;
            if (target) {
                target.style.opacity = '0';
                target.style.transition = 'opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
                requestAnimationFrame(() => {
                    target.style.opacity = '1';
                });
            }
        });
    }

    // ==========================================
    // Page transition animation
    // ==========================================
    function initPageTransitions() {
        // Fade in on load
        const main = document.querySelector('main');
        if (main) {
            main.style.opacity = '0';
            main.style.transform = 'translateY(10px)';
            main.style.transition = 'opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1), transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)';

            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    main.style.opacity = '1';
                    main.style.transform = 'translateY(0)';
                });
            });
        }
    }

    // ==========================================
    // Progress bar animation
    // ==========================================
    function initProgressBars() {
        const bars = document.querySelectorAll('.progress-bar');
        const barObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    const width = bar.dataset.width || bar.style.width;
                    bar.style.width = '0%';
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            bar.style.width = width;
                        });
                    });
                    barObserver.unobserve(bar);
                }
            });
        }, { threshold: 0.2 });

        bars.forEach(bar => barObserver.observe(bar));
    }

    // ==========================================
    // Initialize everything
    // ==========================================
    function init() {
        initParallaxBackground();
        initNavScroll();
        initPageTransitions();
        initScrollAnimations();
        initCounterAnimations();
        initHtmxAnimations();
        initProgressBars();
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
