(function (global) {
  "use strict";

  function normalize(value) {
    return String(value || "")
      .normalize("NFKD")
      .toLowerCase()
      .replace(/[’‘`]/g, "'")
      .replace(/'/g, "")
      .replace(/[^\p{L}\p{N}\s]/gu, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function matches(value, expected) {
    const actual = normalize(value);
    if (!actual || expected === null || expected === undefined) return false;
    if (Array.isArray(expected)) return expected.some(option => matches(value, option));
    if (typeof expected === "object" && Array.isArray(expected.all)) {
      return expected.all.every(part => actual.includes(normalize(part)));
    }
    if (typeof expected === "object" && expected.startsWith) {
      return actual.startsWith(normalize(expected.startsWith));
    }
    return actual === normalize(expected);
  }

  function label(expected) {
    if (expected === null || expected === undefined) return "Teacher review";
    if (Array.isArray(expected)) return label(expected[0]);
    if (typeof expected === "object" && Array.isArray(expected.all)) return expected.all.join(", ");
    if (typeof expected === "object" && expected.startsWith) return String(expected.startsWith).toUpperCase();
    return String(expected);
  }

  global.AnswerGrader = { normalize, matches, label };
})(window);
