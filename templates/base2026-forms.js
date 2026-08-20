(() => {
  const forms = document.querySelectorAll("[data-b26-form]");
  for (const form of forms) {
    form.dataset.startedAt = String(Date.now());
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const status = form.querySelector(".b26-form-status");
      const button = form.querySelector("button[type='submit']");
      const kind = form.dataset.b26Form;
      const values = Object.fromEntries(new FormData(form).entries());
      values.startedAt = Number(form.dataset.startedAt || Date.now());
      status.textContent = "Sending…";
      status.dataset.state = "pending";
      button.disabled = true;
      try {
        const response = await fetch(`/api/forms/${kind}`, {
          method: "POST",
          headers: { "content-type": "application/json", "accept": "application/json" },
          body: JSON.stringify(values),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload?.error?.message || "The proposal could not be sent.");
        form.reset();
        form.dataset.startedAt = String(Date.now());
        status.textContent = `Thank you. Your proposal was received. Reference: ${payload.reference}`;
        status.dataset.state = "success";
      } catch (error) {
        status.textContent = error instanceof Error ? error.message : "The proposal could not be sent. Please try again.";
        status.dataset.state = "error";
      } finally {
        button.disabled = false;
      }
    });
  }
})();
