(function () {
  var bridgeUrl = "ws://127.0.0.1:7541/ws";
  var socket = null;
  var handled = 0;
  var reconnectTimer = null;

  var statusText = document.getElementById("statusText");
  var statusDot = document.getElementById("statusDot");
  var counter = document.getElementById("counter");
  var logBox = document.getElementById("log");

  function setStatus(state, label) {
    statusDot.className = "dot " + state;
    statusText.textContent = label;
  }

  function html(text) {
    return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function log(message, cls) {
    var line = document.createElement("div");
    line.className = "line " + (cls || "");
    line.innerHTML = '<span class="time">' + new Date().toTimeString().slice(0, 8) + "</span> " + html(message);
    logBox.appendChild(line);
    while (logBox.childNodes.length > 250) logBox.removeChild(logBox.firstChild);
    logBox.scrollTop = logBox.scrollHeight;
    sendLog(message);
  }

  function sendLog(message) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: "log", message: String(message) }));
  }

  function connect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    setStatus("waiting", "connecting");
    try {
      socket = new WebSocket(bridgeUrl);
    } catch (err) {
      setStatus("bad", "websocket unavailable");
      scheduleReconnect();
      return;
    }

    socket.onopen = function () {
      setStatus("ok", "connected");
      log("connected to " + bridgeUrl, "ok");
      socket.send(JSON.stringify({ type: "hello", client: "pt-visual-extension" }));
    };

    socket.onclose = function () {
      setStatus("bad", "disconnected");
      log("bridge disconnected; retrying", "warn");
      scheduleReconnect();
    };

    socket.onerror = function () {
      setStatus("bad", "connection error");
    };

    socket.onmessage = function (event) {
      var message;
      try {
        message = JSON.parse(event.data);
      } catch (err) {
        log("received invalid JSON", "bad");
        return;
      }
      if (message.type === "call") handleCall(message);
    };
  }

  function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(connect, 1000);
  }

  function sendResult(id, ok, data, error) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: "result", id: id, ok: !!ok, data: data || null, error: error || null }));
  }

  function ptEval(action, payload) {
    return new Promise(function (resolve) {
      try {
        var code = "return ptvActions[" + JSON.stringify(action) + "](" + JSON.stringify(payload || {}) + ");";
        var wrapped = $se("ptvRunCode", code);
        if (typeof wrapped === "string") {
          try { wrapped = JSON.parse(wrapped); } catch (_) {}
        }
        if (!wrapped || wrapped.ok === false) {
          resolve({ success: false, error: wrapped && wrapped.error ? wrapped.error : "Packet Tracer execution failed" });
          return;
        }
        resolve(wrapped.data);
      } catch (err) {
        resolve({ success: false, error: String((err && err.message) || err) });
      }
    });
  }

  function sleep(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms || 0); });
  }

  function countSuccess(items) {
    var total = 0;
    for (var i = 0; i < items.length; i++) {
      if (items[i] && items[i].success !== false) total++;
    }
    return total;
  }

  function countFailure(items) {
    return items.length - countSuccess(items);
  }

  function makeOptions(payload) {
    payload = payload || {};
    var mode = payload.qualityMode || "fast-safe";
    var profile = {
      maxRetries: 3,
      retryDelayMs: 30,
      settleMs: 15,
      minSpacing: 55,
      verifyAfterBuild: true,
      stopOnDeviceError: true,
      stopOnLinkError: true,
      autoAssignPorts: true,
      autoFallback: true
    };
    if (mode === "max-speed") {
      profile.maxRetries = 1;
      profile.retryDelayMs = 15;
      profile.settleMs = 5;
      profile.minSpacing = 45;
    } else if (mode === "balanced") {
      profile.maxRetries = 4;
      profile.retryDelayMs = 45;
      profile.settleMs = 25;
      profile.minSpacing = 65;
    } else if (mode === "strict") {
      profile.maxRetries = 6;
      profile.retryDelayMs = 70;
      profile.settleMs = 45;
      profile.minSpacing = 80;
    }

    if (payload.maxRetries !== undefined) profile.maxRetries = Number(payload.maxRetries);
    if (payload.retryDelayMs !== undefined) profile.retryDelayMs = Number(payload.retryDelayMs);
    if (payload.settleMs !== undefined) profile.settleMs = Number(payload.settleMs);
    if (payload.minSpacing !== undefined) profile.minSpacing = Number(payload.minSpacing);
    if (payload.verifyAfterBuild !== undefined) profile.verifyAfterBuild = !!payload.verifyAfterBuild;
    if (payload.stopOnDeviceError !== undefined) profile.stopOnDeviceError = !!payload.stopOnDeviceError;
    if (payload.stopOnLinkError !== undefined) profile.stopOnLinkError = !!payload.stopOnLinkError;
    if (payload.autoAssignPorts !== undefined) profile.autoAssignPorts = !!payload.autoAssignPorts;
    if (payload.autoFallback !== undefined) profile.autoFallback = !!payload.autoFallback;
    profile.qualityMode = mode;
    return profile;
  }

  function retryDelay(options, attempt) {
    return Math.max(0, Number(options.retryDelayMs || 0)) * Math.max(1, attempt);
  }

  function ptEvalWithRetry(action, payload, options, label) {
    return new Promise(function (resolve) {
      var attempt = 0;
      var errors = [];
      var maxRetries = Math.max(0, Number(options.maxRetries || 0));

      function run() {
        ptEval(action, payload).then(function (result) {
          if (result && result.success !== false) {
            result.attempts = attempt + 1;
            resolve(result);
            return;
          }

          errors.push(result && result.error ? result.error : "unknown failure");
          if (attempt < maxRetries) {
            attempt++;
            sleep(retryDelay(options, attempt)).then(run);
            return;
          }

          resolve({
            success: false,
            action: action,
            label: label || action,
            attempts: attempt + 1,
            error: errors[errors.length - 1],
            errors: errors
          });
        });
      }

      run();
    });
  }

  function portKey(deviceName, portName) {
    return String(deviceName || "") + "|" + String(portName || "");
  }

  function reserveLinkPorts(usedPorts, link, result) {
    var fromPort = (result && (result.assignedFromInterface || result.fromInterface)) || link.fromInterface;
    var toPort = (result && (result.assignedToInterface || result.toInterface)) || link.toInterface;
    if (fromPort && fromPort !== "auto") usedPorts[portKey(link.fromDevice, fromPort)] = true;
    if (toPort && toPort !== "auto") usedPorts[portKey(link.toDevice, toPort)] = true;
  }

  function assignedLink(link, result) {
    return {
      fromDevice: link.fromDevice,
      fromInterface: (result && (result.assignedFromInterface || result.fromInterface)) || link.fromInterface,
      toDevice: link.toDevice,
      toInterface: (result && (result.assignedToInterface || result.toInterface)) || link.toInterface,
      linkType: link.linkType || "auto",
      requestedFromInterface: link.fromInterface || "auto",
      requestedToInterface: link.toInterface || "auto"
    };
  }

  function addDevicesTimeline(payload) {
    return new Promise(function (resolve) {
      var devices = payload.devices || [];
      var delayMs = Number(payload.delayMs || 0);
      var options = makeOptions(payload);
      var results = [];
      var i = 0;
      function next() {
        if (i >= devices.length) {
          resolve({
            success: countFailure(results) === 0,
            added: countSuccess(results),
            failed: countFailure(results),
            total: devices.length,
            qualityMode: options.qualityMode,
            results: results
          });
          return;
        }
        var device = devices[i];
        log("device " + (i + 1) + "/" + devices.length + " " + device.name);
        ptEvalWithRetry("addDevice", device, options, device.name).then(function (result) {
          results.push(result);
          if (result && result.success === false && options.stopOnDeviceError) {
            resolve({
              success: false,
              added: countSuccess(results),
              failed: countFailure(results),
              total: devices.length,
              stoppedAt: device.name,
              qualityMode: options.qualityMode,
              results: results
            });
            return;
          }
          i++;
          sleep(Math.max(0, delayMs) + Math.max(0, Number(options.settleMs || 0))).then(next);
        });
      }
      next();
    });
  }

  function addLinksTimeline(payload) {
    return new Promise(function (resolve) {
      var links = payload.links || [];
      var delayMs = Number(payload.delayMs || 0);
      var options = makeOptions(payload);
      var usedPorts = payload.usedPorts || {};
      var results = [];
      var assignedLinks = [];
      var i = 0;
      function next() {
        if (i >= links.length) {
          resolve({
            success: countFailure(results) === 0,
            added: countSuccess(results),
            failed: countFailure(results),
            total: links.length,
            qualityMode: options.qualityMode,
            assignedLinks: assignedLinks,
            results: results
          });
          return;
        }
        var link = links[i];
        var linkPayload = {};
        for (var key in link) {
          if (link.hasOwnProperty(key)) linkPayload[key] = link[key];
        }
        linkPayload.usedPorts = usedPorts;
        linkPayload.autoAssignPorts = options.autoAssignPorts;
        linkPayload.autoFallback = options.autoFallback;
        log("link " + (i + 1) + "/" + links.length + " " + link.fromDevice + " -> " + link.toDevice);
        ptEvalWithRetry("addLink", linkPayload, options, link.fromDevice + "->" + link.toDevice).then(function (result) {
          results.push(result);
          if (result && result.success === false && options.stopOnLinkError) {
            resolve({
              success: false,
              added: countSuccess(results),
              failed: countFailure(results),
              total: links.length,
              stoppedAt: link.fromDevice + "->" + link.toDevice,
              qualityMode: options.qualityMode,
              assignedLinks: assignedLinks,
              results: results
            });
            return;
          }
          if (result && result.success !== false) {
            reserveLinkPorts(usedPorts, link, result);
            assignedLinks.push(assignedLink(link, result));
          }
          i++;
          sleep(Math.max(0, delayMs) + Math.max(0, Number(options.settleMs || 0))).then(next);
        });
      }
      next();
    });
  }

  function configureMany(action, items, label, options) {
    return new Promise(function (resolve) {
      var results = [];
      var i = 0;
      function next() {
        if (i >= items.length) {
          resolve({
            success: countFailure(results) === 0,
            configured: countSuccess(results),
            failed: countFailure(results),
            total: items.length,
            results: results
          });
          return;
        }
        var item = items[i];
        log(label + " " + (i + 1) + "/" + items.length + " " + item.deviceName);
        ptEvalWithRetry(action, item, options || makeOptions({ qualityMode: "balanced" }), item.deviceName).then(function (result) {
          results.push(result);
          i++;
          sleep(Math.max(20, Number((options && options.settleMs) || 20))).then(next);
        });
      }
      next();
    });
  }

  function buildTimeline(payload) {
    var plan = payload.plan || {};
    var options = makeOptions(payload);
    var output = { success: true, stages: [], quality: options };
    log("campus build started: " + (plan.prefix || "no-prefix"), "ok");

    return (payload.validatePlan === false ? Promise.resolve({ success: true, skipped: true }) : ptEval("validatePlan", {
      plan: plan,
      minSpacing: options.minSpacing,
      allowExisting: false,
      autoAssignPorts: options.autoAssignPorts,
      autoFallback: options.autoFallback
    }))
      .then(function (stage) {
        output.stages.push({ name: "preflight", result: stage });
        if (stage && stage.success === false) {
          output.success = false;
          output.error = "preflight failed";
          log("preflight failed: " + (stage.errors || []).join("; "), "bad");
          return output;
        }
        if (stage && stage.warnings && stage.warnings.length) {
          log("preflight warnings: " + stage.warnings.length, "warn");
        }
        return addDevicesTimeline({
          devices: plan.devices || [],
          delayMs: payload.deviceDelayMs || 0,
          qualityMode: options.qualityMode,
          maxRetries: options.maxRetries,
          retryDelayMs: options.retryDelayMs,
          settleMs: options.settleMs,
          stopOnDeviceError: options.stopOnDeviceError
        });
      })
      .then(function (stage) {
        if (stage && stage.stages) return stage;
        output.stages.push({ name: "devices", result: stage });
        if (stage && stage.success === false) {
          output.success = false;
          output.error = "device stage failed";
          return output;
        }
        return addLinksTimeline({
          links: plan.links || [],
          delayMs: payload.linkDelayMs || 0,
          qualityMode: options.qualityMode,
          maxRetries: options.maxRetries,
          retryDelayMs: options.retryDelayMs,
          settleMs: options.settleMs,
          stopOnLinkError: options.stopOnLinkError,
          autoAssignPorts: options.autoAssignPorts,
          autoFallback: options.autoFallback
        });
      })
      .then(function (stage) {
        if (stage && stage.stages) return stage;
        output.stages.push({ name: "links", result: stage });
        if (stage && stage.success === false) {
          output.success = false;
          output.error = "link stage failed";
          return output;
        }
        if (stage && stage.assignedLinks && stage.assignedLinks.length) plan.links = stage.assignedLinks;
        if (!payload.configurePc) return { success: true, skipped: true };
        return configureMany("configurePc", plan.pcConfigs || [], "pc", options);
      })
      .then(function (stage) {
        if (stage && stage.stages) return stage;
        output.stages.push({ name: "pcConfigs", result: stage });
        if (stage && stage.success === false) output.success = false;
        if (!payload.configureIos) return { success: true, skipped: true };
        return configureMany("configureIos", plan.iosConfigs || [], "ios", options);
      })
      .then(function (stage) {
        if (stage && stage.stages) return stage;
        output.stages.push({ name: "iosConfigs", result: stage });
        if (stage && stage.success === false) output.success = false;
        if (!options.verifyAfterBuild) return { success: true, skipped: true };
        return ptEval("verifyPlan", { plan: plan });
      })
      .then(function (stage) {
        if (stage && stage.stages) return stage;
        output.stages.push({ name: "verify", result: stage });
        if (stage && stage.verified === false) {
          output.success = false;
          output.error = "post-build verification failed";
        }
        log("campus build finished", "ok");
        return output;
      });
  }

  function handleCall(message) {
    handled++;
    counter.textContent = String(handled);
    var action = message.action;
    var payload = message.payload || {};
    var promise;

    if (action === "addDevicesTimeline") {
      promise = addDevicesTimeline(payload);
    } else if (action === "addLinksTimeline") {
      promise = addLinksTimeline(payload);
    } else if (action === "buildTimeline") {
      promise = buildTimeline(payload);
    } else if (
      action === "getNetwork" ||
      action === "addDevice" ||
      action === "addLink" ||
      action === "configurePc" ||
      action === "configureIos" ||
      action === "runShowCommands" ||
      action === "getCommandLog" ||
      action === "probeDeviceApi" ||
      action === "probeServerServices"
    ) {
      promise = ptEval(action, payload);
    } else {
      sendResult(message.id, false, null, "unknown action: " + action);
      return;
    }

    promise.then(function (result) {
      if (result && result.success === false) {
        log(action + " failed: " + result.error, "bad");
        sendResult(message.id, false, result, result.error);
      } else {
        sendResult(message.id, true, result, null);
      }
    }, function (err) {
      log(action + " failed: " + err, "bad");
      sendResult(message.id, false, null, String((err && err.message) || err));
    });
  }

  document.getElementById("url").textContent = bridgeUrl;
  connect();
})();
