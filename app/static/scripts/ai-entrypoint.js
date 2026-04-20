(function () {
  const root = document.getElementById("aiEntrypoint");
  if (!root) {
    return;
  }

  function readConfig() {
    const element = document.getElementById("ai-entrypoint-data");
    if (!element) {
      return {
        key: root.dataset.pageKey || "generic",
        label: root.dataset.pageLabel || "Workspace",
        caption: root.dataset.pageCaption || "",
        actions: [],
      };
    }

    try {
      return JSON.parse(element.textContent || "{}");
    } catch (_) {
      return {
        key: root.dataset.pageKey || "generic",
        label: root.dataset.pageLabel || "Workspace",
        caption: root.dataset.pageCaption || "",
        actions: [],
      };
    }
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  const config = readConfig();
  const launcher = document.getElementById("aiEntrypointLauncher");
  const modalBackdrop = document.getElementById("aiEntrypointModal");
  const modalClose = document.getElementById("aiEntrypointCloseModal");
  const drawerBackdrop = document.getElementById("aiEntrypointDrawerBackdrop");
  const drawer = document.getElementById("aiEntrypointDrawer");
  const drawerClose = document.getElementById("aiEntrypointCloseDrawer");
  const actionGrid = document.getElementById("aiEntrypointActionGrid");
  const chat = document.getElementById("aiEntrypointChat");
  const form = document.getElementById("aiEntrypointForm");
  const input = document.getElementById("aiEntrypointInput");
  const drawerTitle = document.getElementById("aiEntrypointDrawerTitle");
  const drawerSubtitle = document.getElementById("aiEntrypointDrawerSubtitle");
  const pagePill = document.getElementById("aiEntrypointPagePill");

  const state = {
    modalOpen: false,
    drawerOpen: false,
    selectedAction: null,
    lastFocusedElement: null,
    hideTimers: new Map(),
  };

  function clearHideTimer(element) {
    const timer = state.hideTimers.get(element);
    if (timer) {
      window.clearTimeout(timer);
      state.hideTimers.delete(element);
    }
  }

  function setLockedState() {
    const shouldLock = state.modalOpen || state.drawerOpen;
    document.body.classList.toggle("ai-entrypoint-lock", shouldLock);
  }

  function showLayer(element, openClass) {
    if (!element) return;
    clearHideTimer(element);
    element.hidden = false;
    window.requestAnimationFrame(() => {
      element.classList.add(openClass);
    });
  }

  function hideLayer(element, openClass) {
    if (!element) return;
    clearHideTimer(element);
    element.classList.remove(openClass);
    const timer = window.setTimeout(() => {
      element.hidden = true;
      state.hideTimers.delete(element);
    }, 220);
    state.hideTimers.set(element, timer);
  }

  function focusFirstAction() {
    const firstAction = actionGrid?.querySelector(".ai-entrypoint__action-card");
    if (firstAction) {
      firstAction.focus();
    }
  }

  function scrollChatToBottom() {
    if (!chat) return;
    chat.scrollTop = chat.scrollHeight;
  }

  function appendMessage(role, body, options = {}) {
    if (!chat) return;

    const wrapper = document.createElement("div");
    wrapper.className = `ai-entrypoint__message ai-entrypoint__message--${role === "user" ? "user" : "assistant"}`;

    const roleLabel = role === "user" ? "You" : options.roleLabel || "AI shell";
    const bubbleClass = options.note ? "ai-entrypoint__message-bubble ai-entrypoint__message-bubble--note" : "ai-entrypoint__message-bubble";
    const promptMarkup = options.prompt
      ? `<div class="ai-entrypoint__message-prompt"><strong>Suggested prompt:</strong> ${escapeHtml(options.prompt)}</div>`
      : "";

    wrapper.innerHTML = `
      <div class="ai-entrypoint__message-role">${escapeHtml(roleLabel)}</div>
      <div class="${bubbleClass}">${escapeHtml(body)}</div>
      ${promptMarkup}
    `;

    chat.appendChild(wrapper);
    scrollChatToBottom();
  }

  function renderInitialConversation(action) {
    if (!chat || !action) return;

    chat.innerHTML = "";
    appendMessage(
      "assistant",
      `Ready for "${action.title}". This panel is a front-end preview, so no real AI request is sent yet.`,
      {
        note: true,
        prompt: action.prompt,
      },
    );
    appendMessage(
      "assistant",
      "The future backend can stream answers here, keep conversation history, and attach page-aware suggestions without changing this UI shell.",
    );
  }

  function openModal() {
    if (state.modalOpen) return;

    state.lastFocusedElement = document.activeElement;
    state.modalOpen = true;
    launcher?.setAttribute("aria-expanded", "true");
    showLayer(modalBackdrop, "is-open");
    setLockedState();
    window.setTimeout(focusFirstAction, 30);
  }

  function closeModal(options = {}) {
    if (!state.modalOpen) return;

    state.modalOpen = false;
    launcher?.setAttribute("aria-expanded", "false");
    hideLayer(modalBackdrop, "is-open");
    setLockedState();

    if (options.returnFocus !== false && state.lastFocusedElement instanceof HTMLElement) {
      window.setTimeout(() => {
        state.lastFocusedElement.focus();
      }, 40);
    }
  }

  function openDrawer() {
    if (state.drawerOpen) return;

    state.drawerOpen = true;
    drawer?.setAttribute("aria-hidden", "false");
    showLayer(drawerBackdrop, "is-open");
    showLayer(drawer, "is-open");
    setLockedState();
  }

  function closeDrawer(options = {}) {
    if (!state.drawerOpen) return;

    state.drawerOpen = false;
    drawer?.setAttribute("aria-hidden", "true");
    hideLayer(drawerBackdrop, "is-open");
    hideLayer(drawer, "is-open");
    setLockedState();

    if (options.returnFocus !== false && launcher instanceof HTMLElement) {
      window.setTimeout(() => {
        launcher.focus();
      }, 40);
    }
  }

  function selectAction(actionButton) {
    if (!(actionButton instanceof HTMLElement)) return;

    state.selectedAction = {
      id: actionButton.dataset.aiActionId || "",
      title: actionButton.dataset.aiActionTitle || "AI action",
      description: actionButton.dataset.aiActionDescription || "",
      prompt: actionButton.dataset.aiActionPrompt || "",
    };

    if (drawerTitle) {
      drawerTitle.textContent = state.selectedAction.title;
    }

    if (drawerSubtitle) {
      drawerSubtitle.textContent = state.selectedAction.description || `${config.label} assistant shell`;
    }

    if (pagePill) {
      pagePill.textContent = config.label;
    }

    renderInitialConversation(state.selectedAction);
    closeModal({ returnFocus: false });
    openDrawer();

    window.setTimeout(() => {
      input?.focus();
    }, 60);
  }

  launcher?.addEventListener("click", openModal);
  modalClose?.addEventListener("click", () => closeModal());
  drawerClose?.addEventListener("click", () => closeDrawer());

  modalBackdrop?.addEventListener("click", event => {
    if (event.target === modalBackdrop) {
      closeModal();
    }
  });

  drawerBackdrop?.addEventListener("click", event => {
    if (event.target === drawerBackdrop) {
      closeDrawer();
    }
  });

  actionGrid?.addEventListener("click", event => {
    const actionButton = event.target.closest("[data-ai-action-id]");
    if (!actionButton) return;
    selectAction(actionButton);
  });

  form?.addEventListener("submit", event => {
    event.preventDefault();
    if (!input) return;

    const message = input.value.trim();
    if (!message) {
      input.focus();
      return;
    }

    appendMessage("user", message);
    appendMessage(
      "assistant",
      "Preview mode is active. This UI is ready for a real AI response handler, but nothing is being sent anywhere yet.",
    );

    input.value = "";
    input.focus();
  });

  document.addEventListener("keydown", event => {
    if (event.key !== "Escape") return;

    if (state.modalOpen) {
      closeModal();
      return;
    }

    if (state.drawerOpen) {
      closeDrawer();
    }
  });
})();
