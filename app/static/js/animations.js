/* ============================================================
   LIQUID GLASS — Scroll Advance Animation System
   "You're not scrolling, you're advancing through space."
   ============================================================ */

(function() {
    'use strict';

    if (typeof gsap === 'undefined') {
        console.warn('GSAP not loaded');
        return;
    }

    gsap.registerPlugin(ScrollTrigger);

    // ── PAGE ENTRANCE ──
    // Whole page rises from depth on load
    function initPageEntrance() {
        const main = document.querySelector('main');
        if (!main) return;
        gsap.fromTo(main,
            { opacity: 0, y: 32, filter: 'blur(4px)' },
            { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.9, ease: 'power3.out', delay: 0.05 }
        );
    }

    // ── SCROLL REVEAL — "Advancing" feel ──
    // Elements scale up from depth (z-axis) and fade in
    function initScrollReveal() {
        // Primary fade-in: scale from depth
        document.querySelectorAll('.fade-in').forEach(el => {
            gsap.fromTo(el,
                { y: 50, opacity: 0, scale: 0.97 },
                {
                    y: 0, opacity: 1, scale: 1,
                    duration: 0.9,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: el,
                        start: 'top 88%',
                        end: 'top 55%',
                        scrub: 0.7,
                    }
                }
            );
        });

        // Slide from left
        document.querySelectorAll('.fade-in-left').forEach(el => {
            gsap.fromTo(el,
                { x: -40, opacity: 0 },
                {
                    x: 0, opacity: 1,
                    duration: 0.8,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: el,
                        start: 'top 88%',
                        end: 'top 55%',
                        scrub: 0.7,
                    }
                }
            );
        });

        // Slide from right (sidebar)
        document.querySelectorAll('.fade-in-right').forEach(el => {
            gsap.fromTo(el,
                { x: 40, opacity: 0 },
                {
                    x: 0, opacity: 1,
                    duration: 0.8,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: el,
                        start: 'top 88%',
                        end: 'top 55%',
                        scrub: 0.7,
                    }
                }
            );
        });

        // Scale in from depth
        document.querySelectorAll('.scale-in').forEach(el => {
            gsap.fromTo(el,
                { scale: 0.88, opacity: 0, filter: 'blur(6px)' },
                {
                    scale: 1, opacity: 1, filter: 'blur(0px)',
                    duration: 0.9,
                    ease: 'back.out(1.4)',
                    scrollTrigger: {
                        trigger: el,
                        start: 'top 88%',
                        end: 'top 58%',
                        scrub: 0.6,
                    }
                }
            );
        });
    }

    // ── STAGGER CHILDREN ──
    // Each child card flies in from depth with a stagger
    function initStaggerAnimations() {
        document.querySelectorAll('.stagger-children').forEach(parent => {
            const children = Array.from(parent.children);
            if (children.length === 0) return;

            gsap.fromTo(children,
                { y: 50, opacity: 0, scale: 0.90, filter: 'blur(4px)' },
                {
                    y: 0, opacity: 1, scale: 1, filter: 'blur(0px)',
                    duration: 0.8,
                    stagger: 0.10,
                    ease: 'back.out(1.3)',
                    // immediateRender: false prevents GSAP from immediately applying
                    // the `from` state (blur/invisible) before the trigger fires
                    immediateRender: false,
                    scrollTrigger: {
                        trigger: parent,
                        start: 'top 85%',
                        end: 'top 40%',
                        scrub: 0.5,
                    }
                }
            );
        });
    }

    // ── TEXT REVEALS ──
    // Text lines slide up from below, clip-path style
    function initTextReveals() {
        document.querySelectorAll('.reveal-text').forEach(el => {
            gsap.fromTo(el,
                { y: 28, opacity: 0 },
                {
                    y: 0, opacity: 1,
                    duration: 1.0,
                    ease: 'power3.out',
                    scrollTrigger: {
                        trigger: el,
                        start: 'top 92%',
                        end: 'top 68%',
                        scrub: 0.5,
                    }
                }
            );
        });
    }

    // ── GLASS CARDS — Subtle parallax ──
    // Cards at different depths move at slightly different rates
    function initParallaxCards() {
        document.querySelectorAll('.glass-card').forEach((card, i) => {
            const speed = (i % 3 + 1) * 6;
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

    // ── PAGE HEADER PARALLAX ──
    // Hero title moves slightly slower — depth anchoring effect
    function initHeaderParallax() {
        document.querySelectorAll('.page-header h1').forEach(h1 => {
            gsap.fromTo(h1,
                { y: 0 },
                {
                    y: -24,
                    ease: 'none',
                    scrollTrigger: {
                        trigger: h1.closest('.page-header') || h1,
                        start: 'top 80%',
                        end: 'bottom top',
                        scrub: true,
                    }
                }
            );
        });
    }

    // ── COUNTER ANIMATIONS ──
    // Numbers count up when they enter view — satisfying
    function animateCounter(element, target, duration) {
        if (isNaN(target)) return;
        const obj = { val: 0 };
        // Read suffix from data attribute (stable) — textContent changes mid-animation
        const rawTarget = element.dataset.countTarget || '';
        const suffix = rawTarget.includes('%') ? '%' : '';
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
            // Skip already-initialized counters — prevents duplicate triggers
            // across multiple htmx:afterSwap events on the same page
            if (counter.dataset.countInit) return;
            counter.dataset.countInit = '1';

            // Read from data attribute (stable value) not textContent (changes during animation)
            const rawTarget = counter.dataset.countTarget ?? counter.textContent.trim();
            const value = parseFloat(rawTarget.replace(/[^0-9.]/g, ''));
            if (isNaN(value)) return;
            ScrollTrigger.create({
                trigger: counter,
                start: 'top 82%',
                onEnter: () => animateCounter(counter, value, 1100),
                once: true,
            });
        });
    }

    // ── PROGRESS BARS ──
    // Bars fill from left as they enter view
    function initProgressBars() {
        document.querySelectorAll('.progress-bar').forEach(bar => {
            const targetWidth = bar.dataset.width || bar.style.width || '0%';
            bar.style.width = '0%';
            gsap.to(bar, {
                width: targetWidth,
                duration: 1.3,
                ease: 'power2.out',
                scrollTrigger: {
                    trigger: bar,
                    start: 'top 87%',
                    once: true,
                }
            });
        });
    }

    // ── HTMX LIFECYCLE ──
    // Re-run animations after HTMX swaps content in
    function initHtmxAnimations() {
        // Fade out target before swap
        document.addEventListener('htmx:beforeSwap', function(e) {
            const target = e.detail.target;
            if (target && target.children.length > 0) {
                gsap.to(target, { opacity: 0.4, duration: 0.15 });
            }
        });

        // Animate in after swap
        document.addEventListener('htmx:afterSwap', function(e) {
            const target = e.detail.target;
            if (target) {
                gsap.fromTo(target,
                    { opacity: 0, y: 16 },
                    { opacity: 1, y: 0, duration: 0.45, ease: 'power2.out' }
                );
            }

            // Re-init scroll animations for new content
            setTimeout(() => {
                initStaggerAnimations();
                initScrollReveal();
                initCounterAnimations();
                initProgressBars();
                initTextReveals();
                // Refresh AFTER creating all triggers so above-fold elements
                // fire immediately rather than waiting for the next scroll event
                ScrollTrigger.refresh();
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }, 80);
        });
    }

    // ── STAT CARD HOVER GLOW ──
    // Add a subtle glow pulse on card hover
    function initStatCardInteractions() {
        document.querySelectorAll('.stat-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                gsap.to(card, { y: -5, duration: 0.25, ease: 'power2.out' });
            });
            card.addEventListener('mouseleave', () => {
                if (!card.classList.contains('stat-card-active')) {
                    gsap.to(card, { y: 0, duration: 0.25, ease: 'power2.out' });
                }
            });
        });
    }

    // ── INIT ──
    function init() {
        initPageEntrance();
        initScrollReveal();
        initStaggerAnimations();
        initTextReveals();
        initParallaxCards();
        initHeaderParallax();
        initCounterAnimations();
        initProgressBars();
        initHtmxAnimations();
        initStatCardInteractions();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
