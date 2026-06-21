var ptvMenu = null;
var ptvWindow = null;
var ptvStarted = false;
var ptvStartupError = "";

function PtvMenuController() {
  this.itemId = "";
}

PtvMenuController.prototype.init = function () {
  var menu = ipc.appWindow().getMenuBar().getExtensionsPopupMenu();
  this.itemId = menu.insertItem("", "PT Visual MCP");
  menu.getMenuItemByUuid(this.itemId).registerEvent("onClicked", this, this.openBridge);
};

PtvMenuController.prototype.cleanUp = function () {
  if (!this.itemId) return;
  var menu = ipc.appWindow().getMenuBar().getExtensionsPopupMenu();
  _ScriptModule.unregisterIpcEventByID("MenuItem", this.itemId, "onClicked", this, this.openBridge);
  menu.removeItemUuid(this.itemId);
  this.itemId = "";
};

PtvMenuController.prototype.openBridge = function () {
  ptvWindow.show();
};

function main() {
  if (ptvStarted) {
    if (ptvWindow) ptvWindow.show();
    return;
  }
  ptvStarted = true;
  ptvWindow = new PtvBridgeWindow();
  ptvMenu = new PtvMenuController();
  try {
    ptvMenu.init();
  } catch (err1) {
    ptvStartupError = "menu registration failed: " + String((err1 && err1.message) || err1);
  }
  ptvWindow.show();
}

function cleanUp() {
  if (ptvMenu) ptvMenu.cleanUp();
  if (ptvWindow) ptvWindow.cleanUp();
  ptvMenu = null;
  ptvWindow = null;
  ptvStarted = false;
}

try {
  main();
} catch (err) {
  ptvStarted = false;
  ptvStartupError = String((err && err.message) || err);
}
