// Small visual effects. Nothing here is needed for the site to work.
document.addEventListener("DOMContentLoaded", function () {
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Light that follows the mouse on cards
    document.querySelectorAll(".spotlight").forEach(function (card) {
        card.addEventListener("pointermove", function (event) {
            var box = card.getBoundingClientRect();
            card.style.setProperty("--mx", event.clientX - box.left + "px");
            card.style.setProperty("--my", event.clientY - box.top + "px");
        });
    });

    // Numbers that count up when the page opens
    document.querySelectorAll("[data-count]").forEach(function (el) {
        var target = parseInt(el.getAttribute("data-count"), 10);
        if (isNaN(target) || reduceMotion || target === 0) {
            return;
        }
        var start = null;
        var duration = 900;
        el.textContent = "0";
        function step(time) {
            if (start === null) {
                start = time;
            }
            var progress = Math.min((time - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(target * eased);
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        }
        requestAnimationFrame(step);
    });

    // Score ring fills up to the result
    document.querySelectorAll(".score-ring").forEach(function (ring) {
        var score = parseFloat(ring.getAttribute("data-score"));
        var total = parseFloat(ring.getAttribute("data-total"));
        if (!total) {
            return;
        }
        var target = (score / total) * 100;
        if (reduceMotion) {
            ring.style.setProperty("--p", target);
            return;
        }
        var start = null;
        function step(time) {
            if (start === null) {
                start = time;
            }
            var progress = Math.min((time - start) / 1100, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            ring.style.setProperty("--p", target * eased);
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        }
        requestAnimationFrame(step);
    });
});
