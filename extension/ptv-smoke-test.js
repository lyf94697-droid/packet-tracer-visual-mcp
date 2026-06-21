// Minimal Packet Tracer Script Engine smoke test.
// Import this file in a File Script Module to verify that Packet Tracer
// actually executes JavaScript and can add an Extensions menu item.

var ptvSmokeMenuId = "";
var ptvSmokeRanAt = new Date().toString();

function ptvSmokeClicked() {
  var menu = ipc.appWindow().getMenuBar().getExtensionsPopupMenu();
  menu.insertItem("", "PTV SMOKE CLICKED " + new Date().toLocaleTimeString());
}

function ptvSmokeMain() {
  var menu = ipc.appWindow().getMenuBar().getExtensionsPopupMenu();
  ptvSmokeMenuId = menu.insertItem("", "PTV SMOKE TEST OK");
  menu.getMenuItemByUuid(ptvSmokeMenuId).registerEvent("onClicked", this, ptvSmokeClicked);
}

function main() {
  ptvSmokeMain();
}

ptvSmokeMain();
