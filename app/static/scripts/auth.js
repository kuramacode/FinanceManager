(function () {
  const showLabel = window.t ? window.t("auth.show_password", {}, "Show password") : "Show password";
  const hideLabel = window.t ? window.t("auth.hide_password", {}, "Hide password") : "Hide password";

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    const inputId = button.getAttribute("aria-controls");
    const input = inputId ? document.getElementById(inputId) : button.closest(".input-wrap")?.querySelector("input");

    if (!input) return;

    button.addEventListener("click", () => {
      const shouldShow = input.type === "password";

      input.type = shouldShow ? "text" : "password";
      button.classList.toggle("is-visible", shouldShow);
      button.setAttribute("aria-pressed", String(shouldShow));
      button.setAttribute("aria-label", shouldShow ? hideLabel : showLabel);
    });
  });
})();
