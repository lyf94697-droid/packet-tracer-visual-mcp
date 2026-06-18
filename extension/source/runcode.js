function ptvRunCode(scriptText) {
  try {
    var fn = new Function(scriptText);
    return { ok: true, data: fn() };
  } catch (err) {
    return {
      ok: false,
      error: String((err && err.message) || err),
      errorType: (err && err.name) || "Error",
      stack: err && err.stack,
    };
  }
}
