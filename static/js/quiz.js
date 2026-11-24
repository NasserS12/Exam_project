// Fills the progress bar as the user answers questions.
document.addEventListener("DOMContentLoaded", function () {
    var form = document.querySelector(".quiz-form");
    var bar = document.getElementById("quiz-progress");
    var label = document.getElementById("quiz-progress-label");
    if (!form || !bar || !label) {
        return;
    }

    function update() {
        var answered = form.querySelectorAll("input[type=radio]:checked").length;
        bar.value = answered;
        label.textContent = answered;
    }

    form.addEventListener("change", update);
    update();
});
