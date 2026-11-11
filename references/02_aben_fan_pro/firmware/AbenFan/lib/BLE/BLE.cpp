#include "BLE.h"

BLE::BLE(
    const char *name,
    const char *serviceUUID,
    const char *txCharacteristicUUID,
    const char *rxCharacteristicUUID)
    : _name(name),
      _serviceUUID(serviceUUID),
      _txCharacteristicUUID(txCharacteristicUUID),
      _rxCharacteristicUUID(rxCharacteristicUUID),
      _connecting(false),
      _connected(false),
      _working(false),
      _on(false),
      _preferences()
{
}

BLE::~BLE()
{
}

void BLE::setup()
{
    _preferences.begin("ble", true);
    _on = _preferences.getBool("on", true);
    _preferences.end();

    Serial.println("Setup BLE work!");
    BLEDevice::init(_name);

    _server = BLEDevice::createServer();
    _server->setCallbacks(this);

    _service = _server->createService(_serviceUUID);

    _txCharacteristic = _service->createCharacteristic(
        _txCharacteristicUUID,
        BLECharacteristic::PROPERTY_NOTIFY);
    _txCharacteristic->addDescriptor(new BLE2902());

    _rxCharacteristic = _service->createCharacteristic(
        _rxCharacteristicUUID,
        BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
    _rxCharacteristic->setCallbacks(this);
    _rxCharacteristic->addDescriptor(new BLE2902());
}

void BLE::start()
{
    _service->start();
    _server->getAdvertising()->setScanResponse(true);
    _server->getAdvertising()->setMinPreferred(0x06);
    _server->getAdvertising()->setMinPreferred(0x12);
    _server->getAdvertising()->start();
    _working = true;
}

void BLE::stop()
{
    _server->getAdvertising()->stop();
    _service->stop();
    _working = false;
    _connecting = false;
    _connected = false;
}

void BLE::loop()
{
    if (_on)
    {
        if (!_working)
        {
            start();
        }
    }
    else
    {
        if (_working)
        {
            stop();
        }
    }

    if (!_working)
    {
        return;
    }

    if (_connecting)
    {
        if (_bleGetValueToSend != nullptr)
        {
            static unsigned long notifyTimer = 0;

            if (millis() - notifyTimer >= 100)
            {
                _txCharacteristic->setValue(_bleGetValueToSend());
                _txCharacteristic->notify();
                notifyTimer = millis();
            }
        }
    }

    if (!_connecting && _connected)
    {
        static unsigned long startAdvertisingTimer = 0;

        if (millis() - startAdvertisingTimer >= 500)
        {
            _server->startAdvertising();
            Serial.println("Start Advertising");
            _connected = _connecting;
            startAdvertisingTimer = millis();
        }
    }

    if (_connecting && !_connected)
    {
        _connected = _connecting;
    }
}

void BLE::onConnect(BLEServer *server)
{
    _connecting = true;
}

void BLE::onDisconnect(BLEServer *server)
{
    _connecting = false;
}

bool BLE::isOn()
{
    return _on;
}

void BLE::toggle(bool on)
{
    _on = on;
    _preferences.begin("ble", false);
    _preferences.putBool("on", _on);
    _preferences.end();
}

void BLE::onWrite(BLECharacteristic *characteristic, esp_ble_gatts_cb_param_t *param)
{
    std::string value = characteristic->getValue();

    if (value.length() > 0)
    {
        Serial.print("Received:");
        for (int i = 0; i < value.length(); i++)
        {
            Serial.print(value[i]);
        }
        Serial.print("\r\n");

        characteristic->setValue("received:" + value);
        characteristic->notify();

        if (_bleWhenReceivedValue != nullptr)
        {
            _bleWhenReceivedValue(value);
        }
    }
}

void BLE::onRead(BLECharacteristic *characteristic, esp_ble_gatts_cb_param_t *param)
{
}

bool BLE::isConnecting()
{
    return _connecting;
}

bool BLE::isConnected()
{
    return _connected;
}

bool BLE::isWorking()
{
    return _working;
}

bool BLE::isWaiting()
{
    return _working && !_connecting;
}

void BLE::setBLEWhenReceivedValue(std::function<void(std::string)> bleWhenReceivedValue)
{
    _bleWhenReceivedValue = bleWhenReceivedValue;
}

void BLE::setBLEGetValueToSend(std::function<std::string()> bleGetValueToSend)
{
    _bleGetValueToSend = bleGetValueToSend;
}