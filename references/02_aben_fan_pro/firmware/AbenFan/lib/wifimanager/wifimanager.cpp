#include "wifimanager.h"
#include <ArduinoJson.h>
#include "stringify.h"
#include <SPIFFS.h>

#ifdef AP_SSID
static const char *apSsid = EXPAND_AND_STRINGIFY(AP_SSID);
#else
static const char *apSsid = "esp32s3-ap";
#endif

#ifdef AP_PASSWORD
static const char *apPassword = EXPAND_AND_STRINGIFY(AP_PASSWORD);
#else
static const char *apPassword = "12345678";
#endif

WifiManager::WifiManager(
    char *hostName,
    WiFiClass *wifi,
    MDNSResponder *mdns,
    HWCDC *serial,
    int serverPort)
    : _preferences(),
      _webServer(serverPort),
      _hostName(hostName),
      _wifi(wifi),
      _mdns(mdns),
      _serial(serial),
      _isAP(0)
{
}

WifiManager::~WifiManager()
{
    _webServer.stop();
}

void WifiManager::setup()
{
    if (!SPIFFS.begin(true))
    {
        Serial.println("An Error has occurred while mounting SPIFFS");
        return;
    }

    autoConnect();

    std::function<void(void)> handleSavePassword = std::bind(&WifiManager::handleSavePassword, this);
    std::function<void(void)> handleClearPassword = std::bind(&WifiManager::handleClearPassword, this);

    _webServer.serveStatic("/", SPIFFS, "/wifimanager/index.html");

    _webServer.on(
        "/save",
        HTTP_POST,
        handleSavePassword);

    _webServer.on(
        "/clear",
        HTTP_POST,
        handleClearPassword);

    _webServer.begin();
}

void WifiManager::loop()
{

    if (!_isAP && _wifi->status() != WL_CONNECTED)
    {
        _serial->println("Retry connect...");
        autoConnect();
    }

    _webServer.handleClient();
}

void WifiManager::handleSavePassword()
{

    String message = _webServer.arg("plain");

    JsonDocument receivedJsonData;
    deserializeJson(receivedJsonData, message);

    String ssid = receivedJsonData["ssid"];
    String password = receivedJsonData["password"];

    JsonDocument sendingJsonData;
    sendingJsonData["success"] = 1;

    _preferences.begin("wifimanage", false);
    _preferences.putString("wifi_ssid", ssid);
    _preferences.putString("wifi_password", password);
    _preferences.end();

    _serial->printf("wifi_ssid: %s \r\n", ssid);
    _serial->printf("wifi_password: %s \r\n", password);

    String sendingJsonString;
    serializeJson(sendingJsonData, sendingJsonString);
    _webServer.sendHeader("Content-Type", "application/json");
    _webServer.send(200, "application/json", sendingJsonString);
}

void WifiManager::handleClearPassword()
{
    JsonDocument sendingJsonData;
    sendingJsonData["success"] = 1;

    _preferences.begin("wifimanage", false);
    _preferences.putString("wifi_ssid", "");
    _preferences.putString("wifi_password", "");
    _preferences.end();

    _serial->printf("wifi_ssid and wifi_password cleared\r\n");

    String sendingJsonString;
    serializeJson(sendingJsonData, sendingJsonString);

    _webServer.sendHeader("Content-Type", "application/json");
    _webServer.send(200, "application/json", sendingJsonString);
}

void WifiManager::autoConnect()
{
    int tried = tryConnect();
    _serial->printf("tried: ");
    _serial->println(tried);
    if (!tried)
    {
        createAP();
    }
}

void WifiManager::createAP()
{
    if (!_wifi->softAP(apSsid, apPassword, 11))
    {
        log_e("Soft AP creation failed.");
        _serial->print("Soft AP creation failed.");

        while (1)
            ;
    }
    _isAP = 1;
    _serial->print("apSsid:");
    _serial->print(apSsid);
    _serial->print("apPassword:");
    _serial->print(apPassword);
    _serial->print("IP Address: ");
    _serial->println(_wifi->softAPIP());
}

int WifiManager::tryConnect()
{
    int tried = 0;

    _preferences.begin("wifimanage", true);
    String ssid = _preferences.getString("wifi_ssid", "");
    String password = _preferences.getString("wifi_password", "");
    _serial->printf("wifi_ssid: %s \r\n", ssid);
    _serial->printf("wifi_password: %s \r\n", password);
    _preferences.end();

    _wifi->begin(ssid, password);
    _wifi->setHostname(_hostName);

    while (
        _wifi->status() == WL_NO_SHIELD ||
        _wifi->status() == WL_SCAN_COMPLETED ||
        _wifi->status() == WL_IDLE_STATUS ||
        _wifi->status() == WL_DISCONNECTED)
    {
        _serial->println("Connecting to WiFi...");
        _serial->printf("Wifi Status: %d, IP Address: %s \r\n", _wifi->status(), _wifi->localIP().toString());
        delay(300);
        tried++;
        if (tried > 10)
        {
            return 0;
        }
    }

    if (_wifi->status() == WL_CONNECTED)
    {
        _serial->printf("Wifi Status: %d, IP Address: %s \r\n", _wifi->status(), _wifi->localIP().toString());
        _serial->println("Connected to WiFi");

        if (!_mdns->begin(_hostName))
        {
            _serial->println("Error setting up MDNS responder");
        }

        _isAP = 0;
        return 1;
    }

    return 0;
}
