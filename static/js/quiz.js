document.addEventListener("DOMContentLoaded", function () {
    var form = document.querySelector(".quiz-form");
    if (!form) {
        return;
    }

    // Stops a double-click from sending the answers twice.
    var button = form.querySelector("button[type=submit]");
    var buttonText = button ? button.textContent : "";
    form.addEventListener("submit", function (event) {
        if (form.dataset.sending) {
            event.preventDefault();
            return;
        }
        form.dataset.sending = "1";
        if (button) {
            button.disabled = true;
            button.textContent = "جاري التسليم…";
        }
    });

    // The back button can bring the page back from cache with the button
    // still disabled, so reset it.
    window.addEventListener("pageshow", function (event) {
        if (event.persisted) {
            delete form.dataset.sending;
            if (button) {
                button.disabled = false;
                button.textContent = buttonText;
            }
        }
    });

    // Fills the progress bar as the user answers questions.
    var bar = document.getElementById("quiz-progress");
    var label = document.getElementById("quiz-progress-label");
    if (!bar || !label) {
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
