(function () {
  function readCatalog() {
    const element = document.getElementById("i18n-data");
    if (!element) {
      return { language: "en", locale: "en-US", translations: {} };
    }

    try {
      return JSON.parse(element.textContent || "{}");
    } catch (_) {
      return { language: "en", locale: "en-US", translations: {} };
    }
  }

  function lookup(catalog, key) {
    return String(key || "")
      .split(".")
      .reduce((value, part) => {
        if (!value || typeof value !== "object") return undefined;
        return value[part];
      }, catalog);
  }

  function interpolate(value, replacements) {
    return String(value).replace(/\{([a-zA-Z0-9_]+)\}/g, (match, name) => {
      if (!Object.prototype.hasOwnProperty.call(replacements, name)) {
        return match;
      }
      return replacements[name];
    });
  }

  const catalog = readCatalog();

  window.ledgerI18n = {
    language: catalog.language || "en",
    locale: catalog.locale || "en-US",
    translations: catalog.translations || {},
    t(key, replacements = {}, fallback = "") {
      const value = lookup(this.translations, key);
      if (typeof value !== "string") {
        return fallback || key;
      }
      return interpolate(value, replacements || {});
    },
  };

  window.t = window.ledgerI18n.t.bind(window.ledgerI18n);
})();
