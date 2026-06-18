function PtvBridgeWindow() {
  this.webview = null;
  this.webviewId = "";
}

var ptvInterfaceUrl = typeof PTV_INTERFACE_URL !== "undefined" ? PTV_INTERFACE_URL : "this-sm:index.html";

PtvBridgeWindow.prototype.show = function () {
  if (!this.webviewId || webViewManager.getWebView(this.webviewId) == null) {
    this.webview = webViewManager.createWebView("PT Visual MCP", ptvInterfaceUrl, 760, 460);
    this.webviewId = this.webview.getWebViewId();
    this.webview.registerEvent("closed", this, this.onClosed);
    this.webview.setMinimumWidth(480);
    this.webview.setMinimumHeight(320);
  }
  this.webview.hide();
  this.webview.show();
};

PtvBridgeWindow.prototype.onClosed = function () {
  if (this.webview) this.webview.unregisterEvent("closed", this, this.onClosed);
  this.webview = null;
  this.webviewId = "";
};

PtvBridgeWindow.prototype.cleanUp = function () {
  if (this.webview) this.webview.unregisterEvent("closed", this, this.onClosed);
  this.webview = null;
  this.webviewId = "";
};
