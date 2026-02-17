/* ============================================
   GSAP ScrollTrigger Animations
   Inspired by seccosquared.com scroll feel
   ============================================ */

(function() {
    'use strict';

    // Wait for GSAP to be available
    if (typeof gsap === 'undefined') {
        console.warn('GSAP not loaded');
        return;
    }

    gsap.registerPlugin(ScrollTrigger);

    // ==========================================
    // Page entrance animation
    // ==========================================
    function initPageEntrance() {
        const main = document.querySelector('main');
        if (!main) return;

        gsap.fromTo(main,
            { opacity: 0, y: 30 },
            { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' }
        );
    }

    // ==========================================
    // Scroll-driven section reveals
    // Each section slides up and fades in as you scroll
    // Scrubbed to scroll position for that "advancing" feel
    // ==========================================
    function initScrollReveal() {
        // Fade-in elements: scrubbed to scroll position
        document.querySelectorAll('.fade-in').forEach(el => {
            gsap.fromTo(el,
                { y: 60, opacity: 0 },
                {
                    y: 0,
                    opacity: 1,
                    duration: 1,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: el,
                        start: 'top 90%',
                        end: 'top 50%',
                        scrub: 0.8,
                    }
                }
            );
        });

        // Fade-in-left
        document.querySelectorAll('.fade-in-left').forEach(el => {
            gsap.fromTo(el,
                { x: -60, opacity: 0 },
                {
                    x: 0,
                    opacity: 1,
                    duration: 1,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: el,
                        start: 'top 90%',
                        end: 'top 50%',
                        scrub: 0.8,
                    }
                }
            );
        });

        // Fade-in-right (sidebar)
        document.querySelectorAll('.fade-in-right').forEach(el => {
            gsap.fromTo(el,
                { x: 60, opacity: 0 },
                {
                    x: 0,
                    opacity: 1,
                    duration: 1,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: el,
                        start: 'top 90%',
                        end: 'top 50%',
                        scrub: 0.8,
                    }
                }
            );
        });

        // Scale-in
        document.querySelectorAll('.scale-in').forEach(el => {
            gsap.fromTo(el,
                { scale: 0.9, opacity: 0 },
                {
                    scale: 1,
                    opacity: 1,
                    duration: 1,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: el,
                        start: 'top 90%',
                        end: 'top 60%',
                        scrub: 0.8,
                    }
                }
            );
        });
    }

    // ==========================================
    // Stagger children - cards animate in sequence
    // ==========================================
    function initStaggerAnimations() {
        document.querySelectorAll('.stagger-children').forEach(parent => {
            const children = parent.children;
            if (children.length === 0) return;

            gsap.fromTo(children,
                { y: 40, opacity: 0 },
                {
                    y: 0,
                    opacity: 1,
                    duration: 0.8,
                    stagger: 0.12,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: parent,
                        start: 'top 85%',
                        end: 'top 40%',
                        scrub: 0.6,
                    }
                }
            );
        });
    }

    // ==========================================
    // Text line reveal - lines slide up from below
    // Like seccosquared's animated-line effect
    // ==========================================
    function initTextReveals() {
        document.querySelectorAll('.reveal-text').forEach(el => {
            gsap.fromTo(el,
                { yPercent: 100, opacity: 0 },
                {
                    yPercent: 0,
                    opacity: 1,
                    duration: 1.2,
                    ease: 'power4.out',
                    scrollTrigger: {
                        trigger: el,
                        start: 'top 95%',
                        end: 'top 70%',
                        scrub: 0.5,
                    }
                }
            );
        });
    }

    // ==========================================
    // Glass cards - parallax depth on scroll
    // Cards move at slightly different speeds
    // ==========================================
    function initParallaxCards() {
        document.querySelectorAll('.glass-card').forEach((card, i) => {
            const speed = (i % 3 + 1) * 8;
            gsap.fromTo(card,
                { y: speed },
                {
                    y: -speed,
                    ease: 'none',
                    scrollTrigger: {
                        trigger: card,
                        start: 'top bottom',
                        end: 'bottom top',
                        scrub: true,
                    }
                }
            );
        });
    }

    // ==========================================
    // Navbar scroll effect - still glass-based
    // ==========================================
    function initNavScroll() {
        const nav = document.querySelector('nav');
        if (!nav) return;

        nav.classList.add('glass-nav');

        ScrollTrigger.create({
            start: 20,
            onUpdate: (self) => {
                if (self.scroll() > 20) {
                    nav.classList.add('scrolled');
                } else {
                    nav.classList.remove('scrolled');
                }
            }
        });
    }

    // ==========================================
    // Parallax background orbs
    // ==========================================
    function initParallaxBackground() {
        if (document.querySelector('.parallax-bg')) return;

        const bg = document.createElement('div');
        bg.className = 'parallax-bg';
        bg.innerHTML = `
            <div class="orb orb-1"></div>
            <div class="orb orb-2"></div>
            <div class="orb orb-3"></div>
        `;
        document.body.prepend(bg);

        // Orbs move with scroll (parallax depth)
        const orbs = bg.querySelectorAll('.orb');
        orbs.forEach((orb, i) => {
            gsap.to(orb, {
                y: (i + 1) * -100,
                ease: 'none',
                scrollTrigger: {
                    trigger: document.body,
                    start: 'top top',
                    end: 'bottom bottom',
                    scrub: true,
                }
            });
        });

        // Subtle mouse-driven parallax
        let animFrame;
        document.addEventListener('mousemove', (e) => {
            if (animFrame) cancelAnimationFrame(animFrame);
            animFrame = requestAnimationFrame(() => {
                const x = (e.clientX / window.innerWidth - 0.5) * 2;
                const y = (e.clientY / window.innerHeight - 0.5) * 2;

                orbs.forEach((orb, i) => {
                    const speed = (i + 1) * 3;
                    gsap.to(orb, {
                        x: x * speed,
                        duration: 0.8,
                        ease: 'power2.out',
                        overwrite: 'auto'
                    });
                });
            });
        }, { passive: true });
    }

    // ==========================================
    // Counter animation for stat numbers
    // ==========================================
    function animateCounter(element, target, duration) {
        if (isNaN(target)) return;

        const obj = { val: 0 };
        const isPercent = element.textContent.includes('%');
        const suffix = isPercent ? '%' : '';

        gsap.to(obj, {
            val: target,
            duration: duration / 1000,
            ease: 'power2.out',
            onUpdate: () => {
                element.textContent = Math.round(obj.val) + suffix;
            }
        });
    }

    function initCounterAnimations() {
        document.querySelectorAll('.counter-animate').forEach(counter => {
            const text = counter.textContent.trim();
            const value = parseInt(text.replace(/[^0-9]/g, ''));
            if (isNaN(value)) return;

            ScrollTrigger.create({
                trigger: counter,
                start: 'top 80%',
                onEnter: () => animateCounter(counter, value, 1200),
                once: true,
            });
        });
    }

    // ==========================================
    // Progress bar animation - scrubbed
    // ==========================================
    function initProgressBars() {
        document.querySelectorAll('.progress-bar').forEach(bar => {
            const targetWidth = bar.dataset.width || bar.style.width;
            bar.style.width = '0%';

            gsap.to(bar, {
                width: targetWidth,
                duration: 1.5,
                ease: 'power2.out',
                scrollTrigger: {
                    trigger: bar,
                    start: 'top 85%',
                    once: true,
                }
            });
        });
    }

    // ==========================================
    // Page header - big heading parallax
    // Header text moves slower than the page
    // ==========================================
    function initHeaderParallax() {
        document.querySelectorAll('.page-header h1').forEach(h1 => {
            gsap.fromTo(h1,
                { y: 0 },
                {
                    y: -30,
                    ease: 'none',
                    scrollTrigger: {
                        trigger: h1,
                        start: 'top 80%',
                        end: 'bottom top',
                        scrub: true,
                    }
                }
            );
        });
    }

    // ==========================================
    // HTMX content load - reinitialize animations
    // ==========================================
    function initHtmxAnimations() {
        document.addEventListener('htmx:afterSwap', function(e) {
            setTimeout(() => {
                ScrollTrigger.refresh();
                initScrollReveal();
                initStaggerAnimations();
                initCounterAnimations();
                initProgressBars();
                initTextReveals();
            }, 100);
        });

        document.addEventListener('htmx:beforeSwap', function(e) {
            const target = e.detail.target;
            if (target) {
                gsap.to(target, { opacity: 0.5, duration: 0.2 });
            }
        });

        document.addEventListener('htmx:afterSwap', function(e) {
            const target = e.detail.target;
            if (target) {
                gsap.fromTo(target,
                    { opacity: 0 },
                    { opacity: 1, duration: 0.4, ease: 'power2.out' }
                );
            }
        });
    }

    // ==========================================
    // Initialize everything
    // ==========================================
    function init() {
        initParallaxBackground();
        initNavScroll();
        initPageEntrance();
        initScrollReveal();
        initStaggerAnimations();
        initTextReveals();
        initParallaxCards();
        initHeaderParallax();
        initCounterAnimations();
        initHtmxAnimations();
        initProgressBars();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
