(function (global) {
  "use strict";

  function findApi(start) {
    let current = start;
    let attempts = 0;
    while (current && attempts < 12) {
      if (current.API) return current.API;
      if (!current.parent || current.parent === current) break;
      current = current.parent;
      attempts += 1;
    }
    return null;
  }

  function locateApi() {
    let api = null;
    try { api = findApi(window); } catch (_) { /* cross-origin parent */ }
    if (!api && window.opener) {
      try { api = findApi(window.opener); } catch (_) { /* cross-origin opener */ }
    }
    return api;
  }

  class Scorm12Bridge {
    constructor() {
      this.api = null;
      this.connected = false;
      this.finished = false;
    }

    initialize() {
      this.api = locateApi();
      if (!this.api) return false;
      try {
        this.connected = this.api.LMSInitialize("") === "true";
      } catch (_) {
        this.connected = false;
      }
      return this.connected;
    }

    get(name) {
      if (!this.connected) return "";
      try { return this.api.LMSGetValue(name) || ""; } catch (_) { return ""; }
    }

    set(name, value) {
      if (!this.connected) return false;
      try { return this.api.LMSSetValue(name, String(value)) === "true"; } catch (_) { return false; }
    }

    commit() {
      if (!this.connected) return false;
      try { return this.api.LMSCommit("") === "true"; } catch (_) { return false; }
    }

    finish() {
      if (!this.connected || this.finished) return false;
      this.set("cmi.core.exit", "suspend");
      this.commit();
      try {
        this.finished = this.api.LMSFinish("") === "true";
      } catch (_) {
        this.finished = false;
      }
      return this.finished;
    }
  }

  global.ScormBridge = new Scorm12Bridge();
})(window);
