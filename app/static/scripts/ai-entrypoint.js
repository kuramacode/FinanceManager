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
        label: root.dataset.pageLabel || tr("common.app_name", {}, "Workspace"),
        caption: root.dataset.pageCaption || "",
        actions: [],
      };
    }

    try {
      return JSON.parse(element.textContent || "{}");
    } catch (_) {
      return {
        key: root.dataset.pageKey || "generic",
        label: root.dataset.pageLabel || tr("common.app_name", {}, "Workspace"),
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

  function tr(key, replacements = {}, fallback = "") {
    return window.ledgerI18n?.t(key, replacements, fallback) || fallback || key;
  }

  function currentLanguage() {
    return window.ledgerI18n?.language || root.dataset.language || document.documentElement.lang || "en";
  }

  function localizedField(source, field, fallback = "") {
    const key = source?.[`${field}_key`] || source?.[`${field}Key`] || "";
    const value = source?.[field] || fallback;
    return key ? tr(key, {}, value) : value;
  }

  function endpointForLanguage(endpoint) {
    const url = new URL(endpoint, window.location.origin);
    url.searchParams.set("lang", currentLanguage());
    return url.toString();
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
  const actionPill = document.getElementById("aiEntrypointActionPill");
  const statusPill = document.getElementById("aiEntrypointStatusPill");
  const switchAction = document.getElementById("aiEntrypointSwitchAction");

  const state = {
    modalOpen: false,
    drawerOpen: false,
    selectedAction: null,
    lastFocusedElement: null,
    hideTimers: new Map(),
    requestId: 0,
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

    const roleLabel = role === "user" ? tr("ai.you") : options.roleLabel || tr("ai.ai_shell");
    const bubbleClass = options.note ? "ai-entrypoint__message-bubble ai-entrypoint__message-bubble--note" : "ai-entrypoint__message-bubble";
    const promptMarkup = options.prompt
      ? `<div class="ai-entrypoint__message-prompt"><strong>${escapeHtml(tr("ai.suggested_prompt"))}</strong> ${escapeHtml(options.prompt)}</div>`
      : "";

    wrapper.innerHTML = `
      <div class="ai-entrypoint__message-role">${escapeHtml(roleLabel)}</div>
      <div class="${bubbleClass}">${escapeHtml(body)}</div>
      ${promptMarkup}
    `;

    chat.appendChild(wrapper);
    scrollChatToBottom();
  }

  function formatSection(title, items) {
    if (!Array.isArray(items)) {
      return "";
    }

    const lines = items
      .filter(item => item !== null && item !== undefined && String(item).trim())
      .map((item, index) => `${index + 1}. ${String(item).trim()}`);

    if (!lines.length) {
      return "";
    }

    return `${title}\n${lines.join("\n")}`;
  }

  function formatAIActionResponse(data) {
    if (typeof data?.message === "string" && data.message.trim()) {
      return data.message.trim();
    }

    if (data?.raw && typeof data.raw === "object") {
      return formatAIActionResponse(data.raw);
    }

    const sections = [
      formatSection(tr("ai.sections.insights"), data?.insights),
      formatSection(tr("ai.sections.problems"), data?.problems),
      formatSection(tr("ai.sections.recommendations"), data?.recommendations),
      formatSection(tr("ai.sections.problem_categories", {}, "Problem categories"), data?.problem_categories),
      formatSection(tr("ai.sections.advice", {}, "Advice"), data?.advice),
      formatSection(tr("ai.sections.top_categories", {}, "Top categories"), data?.top_categories),
    ].filter(Boolean);

    if (typeof data?.answer === "string" && data.answer.trim()) {
      sections.unshift(data.answer.trim());
    }

    if (Array.isArray(data?.anomalies) && data.anomalies.length) {
      const anomalies = data.anomalies.map(item => {
        if (!item || typeof item !== "object") return String(item || "");
        return Object.entries(item)
          .filter(([, value]) => value !== null && value !== undefined && String(value).trim())
          .map(([key, value]) => `${key}: ${value}`)
          .join("; ");
      });
      sections.push(formatSection(tr("ai.sections.anomalies", {}, "Anomalies"), anomalies));
    }

    if (Array.isArray(data?.budget) && data.budget.length) {
      const budget = data.budget.map(item => {
        if (!item || typeof item !== "object") return String(item || "");
        return Object.entries(item)
          .filter(([, value]) => value !== null && value !== undefined && String(value).trim())
          .map(([key, value]) => `${key}: ${value}`)
          .join("; ");
      });
      sections.push(formatSection(tr("ai.sections.budget", {}, "Budget"), budget));
    }

    if (typeof data?.top_category === "string" && data.top_category.trim()) {
      sections.unshift(`${tr("ai.sections.top_category", {}, "Top category")}\n${data.top_category.trim()}`);
    }

    const forecast = [];
    if (Object.prototype.hasOwnProperty.call(data || {}, "expected_total")) {
      forecast.push(`${tr("ai.sections.expected_total", {}, "Expected total")}: ${data.expected_total}`);
    }
    if (data?.trend) {
      forecast.push(`${tr("ai.sections.trend", {}, "Trend")}: ${data.trend}`);
    }
    if (data?.note) {
      forecast.push(String(data.note));
    }
    if (forecast.length) {
      sections.push(`${tr("ai.sections.forecast", {}, "Forecast")}\n${forecast.join("\n")}`);
    }

    const score = [];
    if (Object.prototype.hasOwnProperty.call(data || {}, "score")) {
      score.push(`${tr("ai.sections.score", {}, "Score")}: ${data.score}`);
    }
    if (data?.status) {
      score.push(`${tr("ai.sections.status", {}, "Status")}: ${data.status}`);
    }
    if (data?.explanation) {
      score.push(String(data.explanation));
    }
    if (score.length) {
      sections.push(`${tr("ai.sections.financial_score", {}, "Financial score")}\n${score.join("\n")}`);
    }

    return sections.join("\n\n") || tr("ai.response_empty");
  }

  function errorMessage(payload, fallback) {
    if (payload && typeof payload.error === "string" && payload.error.trim()) {
      return payload.error.trim();
    }

    return fallback;
  }

  function setSending(isSending) {
    const sendButton = form?.querySelector(".ai-entrypoint__send");
    if (sendButton instanceof HTMLButtonElement) {
      sendButton.disabled = isSending;
    }
    if (input) {
      input.disabled = isSending;
    }
  }

  async function runConnectedAction(action, userMessage = "") {
    if (!action?.endpoint) {
      return;
    }

    const currentRequestId = ++state.requestId;
    if (statusPill) {
      statusPill.textContent = tr("ai.analyzing");
    }
    setSending(true);

    try {
      const response = await fetch(endpointForLanguage(action.endpoint), {
        method: action.method || "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-Ledger-Language": currentLanguage(),
        },
        body: JSON.stringify({
          page_key: config.key || root.dataset.pageKey || "generic",
          message: userMessage || "",
        }),
      });

      let payload = null;
      try {
        payload = await response.json();
      } catch (_) {
        payload = null;
      }

      if (!response.ok || !payload?.ok) {
        throw new Error(errorMessage(payload, tr("ai.request_failed", { status: response.status }, `AI request failed with status ${response.status}`)));
      }

      if (currentRequestId !== state.requestId) {
        return;
      }

      appendMessage("assistant", formatAIActionResponse(payload.data), { roleLabel: "AI" });
      if (statusPill) {
        statusPill.textContent = tr("ai.analysis_ready");
      }
    } catch (error) {
      if (currentRequestId !== state.requestId) {
        return;
      }

      appendMessage(
        "assistant",
        tr("ai.could_not_run", { message: error?.message || tr("common.unknown") }),
        { note: true, roleLabel: "AI" },
      );

      if (statusPill) {
        statusPill.textContent = tr("ai.ai_unavailable");
      }
    } finally {
      if (currentRequestId === state.requestId) {
        setSending(false);
        input?.focus();
      }
    }
  }

  function renderInitialConversation(action) {
    if (!chat || !action) return;

    chat.innerHTML = "";

    appendMessage(
      "assistant",
      tr("ai.running_action", { title: action.title }),
      {
        note: true,
      },
    );
    runConnectedAction(action);
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

  function actionFromButton(actionButton) {
    if (!(actionButton instanceof HTMLElement)) return null;

    return {
      id: actionButton.dataset.aiActionId || "",
      title: localizedField(actionButton.dataset, "title", tr("ai.choose_action_short")),
      titleKey: actionButton.dataset.aiActionTitleKey || "",
      description: localizedField(actionButton.dataset, "description", ""),
      descriptionKey: actionButton.dataset.aiActionDescriptionKey || "",
      prompt: localizedField(actionButton.dataset, "prompt", ""),
      promptKey: actionButton.dataset.aiActionPromptKey || "",
      promptType: actionButton.dataset.aiActionPromptType || "",
      endpoint: actionButton.dataset.aiActionEndpoint || "",
      method: actionButton.dataset.aiActionMethod || "POST",
    };
  }

  function selectAction(action) {
    if (!action) return;

    state.selectedAction = {
      id: action.id || "",
      title: localizedField(action, "title", tr("ai.choose_action_short")),
      titleKey: action.title_key || action.titleKey || "",
      description: localizedField(action, "description", ""),
      descriptionKey: action.description_key || action.descriptionKey || "",
      prompt: localizedField(action, "prompt", ""),
      promptKey: action.prompt_key || action.promptKey || "",
      promptType: action.prompt_type || action.promptType || "",
      endpoint: action.endpoint || "",
      method: action.method || "POST",
    };

    if (drawerTitle) {
      drawerTitle.textContent = state.selectedAction.title;
    }

    if (drawerSubtitle) {
      drawerSubtitle.textContent = state.selectedAction.description || tr("ai.assistant_shell", { page: config.label });
    }

    if (pagePill) {
      pagePill.textContent = config.label;
    }

    if (actionPill) {
      actionPill.textContent = state.selectedAction.title;
    }

    actionGrid?.querySelectorAll("[data-ai-action-id]").forEach(button => {
      button.classList.toggle("is-selected", button.dataset.aiActionId === state.selectedAction.id);
    });

    renderInitialConversation(state.selectedAction);
    closeModal({ returnFocus: false });
    openDrawer();

    window.setTimeout(() => {
      input?.focus();
    }, 60);
  }

  function handleLauncherClick() {
    openModal();
  }

  launcher?.addEventListener("click", handleLauncherClick);
  modalClose?.addEventListener("click", () => closeModal());
  drawerClose?.addEventListener("click", () => closeDrawer());
  switchAction?.addEventListener("click", () => {
    state.lastFocusedElement = switchAction;
    openModal();
  });

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
    selectAction(actionFromButton(actionButton));
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
    input.value = "";

    if (state.selectedAction?.endpoint) {
      appendMessage("assistant", tr("ai.followup_not_connected"), { note: true });
      runConnectedAction(state.selectedAction, message);
      return;
    }

    appendMessage("assistant", tr("ai.preview_mode"), { note: true });
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
