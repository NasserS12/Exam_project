// Picks light or dark before the page draws, then wires the toggle button.
(function () {
    var root = document.documentElement;
    var saved = null;
    try {
        saved = localStorage.getItem("theme");
    } catch (e) {
        saved = null;
    }
    var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.setAttribute("data-theme", saved || (prefersDark ? "dark" : "light"));

    document.addEventListener("DOMContentLoaded", function () {
        var button = document.getElementById("theme-toggle");
        if (!button) {
            return;
        }
        button.addEventListener("click", function () {
            var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
            root.setAttribute("data-theme", next);
            try {
                localStorage.setItem("theme", next);
            } catch (e) {
                // Storage blocked: the choice lasts for this page only.
            }
        });
    });
})();
