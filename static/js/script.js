document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#prediction-form");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    const goals = Number(form.elements.goals.value);
    const shots = Number(form.elements.shots.value);
    const accuracy = Number(form.elements.pass_accuracy.value);

    if (goals > shots) {
      event.preventDefault();
      form.elements.goals.setCustomValidity("Goals cannot be greater than shots.");
      form.elements.goals.reportValidity();
      form.elements.goals.addEventListener("input", () => {
        form.elements.goals.setCustomValidity("");
      }, { once: true });
    } else if (accuracy < 0 || accuracy > 100) {
      event.preventDefault();
      form.elements.pass_accuracy.setCustomValidity("Enter a percentage from 0 to 100.");
      form.elements.pass_accuracy.reportValidity();
      form.elements.pass_accuracy.addEventListener("input", () => {
        form.elements.pass_accuracy.setCustomValidity("");
      }, { once: true });
    }
  });
});
