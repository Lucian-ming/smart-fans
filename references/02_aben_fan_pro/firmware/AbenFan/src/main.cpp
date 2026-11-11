#include <Arduino.h>
#include <U8g2lib.h>
#include <MUIU8g2.h>
#include <AHT20.h>
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <WiFi.h>

#include "config.h"
#include "Thermometer.h"
#include "Fan.h"
#include "RGBLed.h"
#include "dino_game_arduino.h"
#include "Menu.h"
#include "BLE.h"
#include "wifimanager.h"

#ifdef U8X8_HAVE_HW_SPI
#include <SPI.h>
#endif
#ifdef U8X8_HAVE_HW_I2C
#include <Wire.h>
#endif

// 关闭系统的引脚
#define OFF_PIN 7

// 风扇电机使用的频道
#define FAN_CHANNEL 0
// 风扇引脚
#define FAN_PIN_A 8
#define FAN_PIN_B 9

// OLED使用的引脚
#define OLED_SCL_PIN 12
#define OLED_SDA_PIN 13

// 按钮使用的引脚
#define BUTTON1_PIN 5
#define BUTTON2_PIN 6

// RGBLED使用的引脚
#define RGBLED_PIN 14

// AHT20使用的引脚
#define AHT20_SCL_PIN 10
#define AHT20_SDA_PIN 11

// AHT20的默认校准量
#define DEFAULT_TEMPERATURE_OFFSET -2.0
#define DEFAULT_HUMIDITY_OFFSET -4.0

#define APP_NAME "Aben Fan Pro"
#define BLE_SERVICE_UUID "D8A1B000-0A3C-4996-9E60-832EB8CF6EF8"
#define BLE_TX_CHARACTERISTIC_UUID "D8A1B001-0A3C-4996-9E60-832EB8CF6EF8"
#define BLE_RX_CHARACTERISTIC_UUID "D8A1B002-0A3C-4996-9E60-832EB8CF6EF8"

#define ABENFAN_BLE_ACTION_FAN_NEXT "FAN:NEXT"
#define ABENFAN_BLE_ACTION_FAN_LEVEL0 "FAN:LEVEL0"
#define ABENFAN_BLE_ACTION_FAN_LEVEL1 "FAN:LEVEL1"
#define ABENFAN_BLE_ACTION_FAN_LEVEL2 "FAN:LEVEL2"
#define ABENFAN_BLE_ACTION_FAN_LEVEL3 "FAN:LEVEL3"
#define ABENFAN_BLE_ACTION_FAN_LEVEL4 "FAN:LEVEL4"
#define ABENFAN_BLE_ACTION_RGB_ON "RGB:ON"
#define ABENFAN_BLE_ACTION_RGB_OFF "RGB:OFF"

typedef enum
{
    ABENFAN_SCENE_WELCOME = 0,
    ABENFAN_SCENE_MENU = 1,
    ABENFAN_SCENE_DINORUN = 2,
    ABENFAN_SCENE_DINOULTRAMANRUN = 3,

} AbenFanScene;

U8G2_SSD1306_128X64_NONAME_F_2ND_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

AHT20 aht20;
Thermometer thermometer(&aht20, DEFAULT_TEMPERATURE_OFFSET, DEFAULT_HUMIDITY_OFFSET);

Fan fan(FAN_CHANNEL, FAN_PIN_A, FAN_PIN_B, FAN_PIN_B, 39000, 10, 990, 1000, 1012, 1024);

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(1, RGBLED_PIN, NEO_GRB + NEO_KHZ800);
RGBLed rgbLed = RGBLed(&pixels);

DinoGameArduino dinoGameArduino(&u8g2);

abenfanmenu::Menu menu(&u8g2);

BLE ble(APP_NAME, BLE_SERVICE_UUID, BLE_TX_CHARACTERISTIC_UUID, BLE_RX_CHARACTERISTIC_UUID);

int i = 10;
int buttonTimer = 0;

uint8_t inDinoRun = 0;

AbenFanScene currentScene = ABENFAN_SCENE_WELCOME;

WifiManager wifiManager((char *)"AbenFanPro", &WiFi, &MDNS, &Serial, 8081);

void whenFormInactiveFunc();
std::string bleGetValueToSend();
void bleWhenReceivedValue(std::string value);
void setupMenu();

void setup()
{
    Serial.begin(115200);

    // 按住2秒后启动
    pinMode(OFF_PIN, OUTPUT_OPEN_DRAIN);
    digitalWrite(OFF_PIN, LOW);
    delay(2000);
    digitalWrite(OFF_PIN, HIGH);

    // 设置按键
    pinMode(BUTTON1_PIN, INPUT_PULLUP);
    pinMode(BUTTON2_PIN, INPUT_PULLUP);

    // fan
    fan.setup();

    // thermometer
    Wire.begin(AHT20_SDA_PIN, AHT20_SCL_PIN);
    thermometer.setup();

    // rgbled
    rgbLed.setup();

    // oled
    Wire1.begin(OLED_SDA_PIN, OLED_SCL_PIN);
    u8g2.begin(BUTTON1_PIN, BUTTON2_PIN, U8X8_PIN_NONE, U8X8_PIN_NONE, U8X8_PIN_NONE, U8X8_PIN_NONE);
    u8g2.setFontMode(1);

    // ble
    ble.setup();
    ble.setBLEGetValueToSend(bleGetValueToSend);
    ble.setBLEWhenReceivedValue(bleWhenReceivedValue);

    // menu
    menu.setup();

    // wifi
    wifiManager.setup();
}

void loop()
{
    thermometer.loop();
    fan.loop();
    menu.loop(whenFormInactiveFunc);
    ble.loop();
    wifiManager.loop();
}

std::string bleGetValueToSend()
{
    std::string value;
    JsonDocument jsonData;
    JsonObject fanObj = jsonData["fan"].to<JsonObject>();
    fanObj["level"] = fan.getLevel();
    JsonObject thermometerObj = jsonData["thermometer"].to<JsonObject>();
    thermometerObj["temperature"] = thermometer.getTemperature();
    thermometerObj["humidity"] = thermometer.getHumidity();
    thermometerObj["temperature_offset"] = thermometer.getTemperatureOffset();
    thermometerObj["humidity_offset"] = thermometer.getHumidityOffset();
    JsonObject rgbLightObj = jsonData["rgb_light"].to<JsonObject>();
    rgbLightObj["on"] = rgbLed.isOn();

    serializeJson(jsonData, value);

    return value;
}

void bleWhenReceivedValue(std::string value)
{
    if (value == ABENFAN_BLE_ACTION_FAN_NEXT)
    {
        fan.nextLevel();
    }
    else if (value == ABENFAN_BLE_ACTION_FAN_LEVEL0)
    {
        fan.setLevel(0);
    }
    else if (value == ABENFAN_BLE_ACTION_FAN_LEVEL1)
    {
        fan.setLevel(1);
    }
    else if (value == ABENFAN_BLE_ACTION_FAN_LEVEL2)
    {
        fan.setLevel(2);
    }
    else if (value == ABENFAN_BLE_ACTION_FAN_LEVEL3)
    {
        fan.setLevel(3);
    }
    else if (value == ABENFAN_BLE_ACTION_FAN_LEVEL4)
    {
        fan.setLevel(4);
    }
    else if (value == ABENFAN_BLE_ACTION_RGB_ON)
    {
        rgbLed.toggle(true);
    }
    else if (value == ABENFAN_BLE_ACTION_RGB_OFF)
    {
        rgbLed.toggle(false);
    }

    setupMenu();
}

void setupMenu()
{
    abenfanmenu::MenuSetupRGBLightOn(rgbLed.isOn());
    abenfanmenu::MenuSetupTemperatureOffset(uint8_t(thermometer.getTemperatureOffset()));
    abenfanmenu::MenuSetupHumidityOffset(uint8_t(thermometer.getHumidityOffset()));
    abenfanmenu::MenuSetupBLEOn(ble.isOn());
}

void startMenu()
{
    setupMenu();
    menu.start();
}

void whenFormInactiveFunc()
{
    if (currentScene == ABENFAN_SCENE_DINORUN || currentScene == ABENFAN_SCENE_DINOULTRAMANRUN)
    {
        if (digitalRead(BUTTON1_PIN) == LOW && digitalRead(BUTTON2_PIN) == LOW)
        {
            // dinoGameArduino.setCheatMode(CHEAT_MODE_CHEAT);
            dinoGameArduino.quitGame();
            if (currentScene == ABENFAN_SCENE_DINORUN)
            {
                menu.gotoForm(20, 1);
            }
            else if (currentScene == ABENFAN_SCENE_DINOULTRAMANRUN)
            {
                menu.gotoForm(20, 2);
            }
            currentScene = ABENFAN_SCENE_MENU;

            delay(300);
        }
        else
        {
            if (digitalRead(BUTTON1_PIN) == LOW)
            {
                dinoGameArduino.startGame();
            }
            if (digitalRead(BUTTON2_PIN) == LOW)
            {
                dinoGameArduino.dinoJump();
            }
        }
        dinoGameArduino.loop();
    }
    else if (currentScene == ABENFAN_SCENE_WELCOME)
    {
        if (digitalRead(BUTTON1_PIN) == LOW)
        {
            if (millis() - buttonTimer >= 500)
            {
                buttonTimer = millis();
                fan.nextLevel();
            }
        }
        else if (digitalRead(BUTTON2_PIN) == LOW)
        {
            startMenu();
            delay(300);
        }

        // 欢迎屏
        u8g2.firstPage();
        do
        {
            // 画线动画
            if (i < u8g2.getWidth())
            {
                i = i + fan.getLevel();
            }
            else
            {
                i = 0;
            }
            if (fan.getLevel() == 0)
            {
                i = 0;
            }
            u8g2.drawHLine(0, u8g2.getHeight() - 1, i);

            char words[20];
            sprintf(words, "Level: %d", fan.getLevel());
            u8g2.setFont(u8g2_font_8x13B_tf);
            u8g2.drawStr(0, 24, words);

            // 显示温湿度
            if (thermometer.isAvailable())
            {
                u8g2.setFont(u8g2_font_7x13_tf);
                sprintf(words, "%.1fC", thermometer.getTemperature());
                u8g2.drawStr(0, 54, words);
                sprintf(words, "%.1fRH", thermometer.getHumidity());
                u8g2.drawStr(50, 54, words);
            }

            if (ble.isOn())
            {
                u8g2.setFont(u8g2_font_open_iconic_embedded_1x_t);
                u8g2.drawGlyph(120, 10, 74);
            }
        } while (u8g2.nextPage());
    }
}

// Actions
void actionStartDinoRun()
{
    dinoGameArduino.setup();
    currentScene = ABENFAN_SCENE_DINORUN;
}

void actionStartDinoUltramanRun()
{
    dinoGameArduino.setup();
    dinoGameArduino.showUltraman();
    currentScene = ABENFAN_SCENE_DINOULTRAMANRUN;
}

void actionTurnOff()
{
    digitalWrite(OFF_PIN, LOW);
    delay(1000);
}

void actionToggleRGBLight(uint8_t on)
{
    rgbLed.toggle(on);
}

void actionChangeTemperatureOffset(int8_t offset)
{
    thermometer.setTemperatureOffset(float(offset));
}

void actionChangeHumidityOffset(int8_t offset)
{
    thermometer.setHumidityOffset(float(offset));
}

void actionWhenMenuWasClosed()
{
    currentScene = ABENFAN_SCENE_WELCOME;
}

void actionToggleBLE(uint8_t on)
{
    ble.toggle(on);
}

// Menu Actions
std::function<void()> abenfanmenu::MenuDinoRunFunc = actionStartDinoRun;
std::function<void()> abenfanmenu::MenuDinoUltramanRunFunc = actionStartDinoUltramanRun;
std::function<void()> abenfanmenu::MenuTurnOffFunc = actionTurnOff;
std::function<void(uint8_t)> abenfanmenu::MenuRGBLightToggleFunc = actionToggleRGBLight;
std::function<void(int8_t)> abenfanmenu::MenuChangeTemperatureOffsetFunc = actionChangeTemperatureOffset;
std::function<void(int8_t)> abenfanmenu::MenuChangeHumidityOffsetFunc = actionChangeHumidityOffset;
std::function<void()> abenfanmenu::MenuWhenWasClosed = actionWhenMenuWasClosed;
std::function<void(uint8_t)> abenfanmenu::MenuToggleBLEFunc = actionToggleBLE;