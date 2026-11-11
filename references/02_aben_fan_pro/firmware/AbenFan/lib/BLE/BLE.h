#ifndef __BLE_H_
#define __BLE_H_

#include <functional>
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <Preferences.h>

class BLE : public BLEServerCallbacks, BLECharacteristicCallbacks
{
public:
    BLE(
        const char *name,
        const char *serviceUUID,
        const char *txCharacteristicUUID,
        const char *rxCharacteristicUUID);
    virtual ~BLE();

    void setup();
    void loop();

    void start();
    void stop();

    void onConnect(BLEServer *server);
    void onDisconnect(BLEServer *server);

    void onWrite(BLECharacteristic *characteristic, esp_ble_gatts_cb_param_t *param);
    void onRead(BLECharacteristic *characteristic, esp_ble_gatts_cb_param_t *param);

    bool isConnecting();
    bool isConnected();
    bool isWorking();
    bool isWaiting();
    void toggle(bool on);
    bool isOn();

    void setBLEWhenReceivedValue(std::function<void(std::string)> bleWhenReceivedValue);
    void setBLEGetValueToSend(std::function<std::string()> bleGetValueToSend);

protected:
    const char *_name;
    const char *_serviceUUID;
    const char *_txCharacteristicUUID;
    const char *_rxCharacteristicUUID;
    bool _connecting;
    bool _connected;
    bool _working;
    bool _on;

    BLEServer *_server;
    BLEService *_service;
    BLECharacteristic *_txCharacteristic;
    BLECharacteristic *_rxCharacteristic;

    std::function<void(std::string)> _bleWhenReceivedValue;
    std::function<std::string()> _bleGetValueToSend;
    Preferences _preferences;
};

#endif // !__BLE_H_