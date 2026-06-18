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
  ptvMenu = new PtvMenuController();
  ptvWindow = new PtvBridgeWindow();
  ptvMenu.init();
}

function cleanUp() {
  if (ptvMenu) ptvMenu.cleanUp();
  if (ptvWindow) ptvWindow.cleanUp();
}
