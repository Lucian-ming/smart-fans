#include "Thermometer.h"
#include <stdio.h>
#include <arduino-timer.h>

auto timer = timer_create_default();

Thermometer::Thermometer(AHT20 *aht20,
                         ThermometerValue *value,
                         float temperatureOffset = 0.0,
                         float humidityOffset = 0.0)
    : _aht20(aht20),
      _value(value),
      _temperatureOffset(temperatureOffset),
      _humidityOffset(humidityOffset),
      _isAvailable(0)
{
    if (aht20 == nullptr)
    {
        printf("error: aht20 is null \n");
    }
    if (value == nullptr)
    {
        printf("error: thermometer value is null \n");
    }
}

Thermometer::Thermometer(AHT20 *aht20,
                         float temperatureOffset = 0.0,
                         float humidityOffset = 0.0)
    : _aht20(aht20),
      _temperatureOffset(temperatureOffset),
      _humidityOffset(humidityOffset),
      _preferences()
{
    if (aht20 == nullptr)
    {
        printf("error: aht20 is null \n");
    }

    _value = new ThermometerValue;
}

Thermometer::~Thermometer()
{
    _aht20 = nullptr;
    _value = nullptr;
    _temperatureOffset = 0;
    _humidityOffset = 0;
    _isAvailable = 0;
}

void Thermometer::setup()
{

    _preferences.begin("thermometer", true);
    _temperatureOffset = _preferences.getFloat("toffset", _temperatureOffset);
    _humidityOffset = _preferences.getFloat("hoffset", _humidityOffset);
    _preferences.end();

    if (_aht20->begin() == false)
    {
        Serial.println("AHT20 not detected. Please check wiring. Freezing.");
        _isAvailable = 0;
    }
    else
    {
        _value->temperature = _aht20->getTemperature() + _temperatureOffset;
        _value->humidity = _aht20->getHumidity() + _humidityOffset;
        _isAvailable = 1;
    }

    timer.every(60000, &Thermometer::refreshAHT20, this);
}

void Thermometer::loop()
{
    timer.tick();
}

float Thermometer::getTemperature()
{
    return _value->temperature;
}

float Thermometer::getHumidity()
{
    return _value->humidity;
}

float Thermometer::getTemperatureOffset()
{
    return _temperatureOffset;
}

float Thermometer::getHumidityOffset()
{
    return _humidityOffset;
}

void Thermometer::setTemperatureOffset(float temperatureOffset)
{
    _temperatureOffset = temperatureOffset;
    if (_temperatureOffset > 5 || _temperatureOffset < -5)
    {
        _temperatureOffset = 0;
    }
    _preferences.begin("thermometer", false);
    _preferences.putFloat("toffset", _temperatureOffset);
    _preferences.end();

    _value->temperature = _aht20->getTemperature() + _temperatureOffset;
}

void Thermometer::setHumidityOffset(float humidityOffset)
{
    _humidityOffset = humidityOffset;
    if (_humidityOffset > 5 || _humidityOffset < -5)
    {
        _humidityOffset = 0;
    }
    _preferences.begin("thermometer", false);
    _preferences.putFloat("hoffset", _humidityOffset);
    _preferences.end();

    _value->humidity = _aht20->getHumidity() + _humidityOffset;
}

uint8_t Thermometer::isAvailable()
{
    return _isAvailable;
}

bool Thermometer::refreshAHT20(void *p)
{
    if (p == nullptr)
    {
        return false;
    }
    Thermometer *ptr = (Thermometer *)p;
    if (!ptr->_aht20->isConnected() || !ptr->_aht20->available())
    {
        return false;
    }
    ptr->_value->temperature = ptr->_aht20->getTemperature() + ptr->_temperatureOffset;
    ptr->_value->humidity = ptr->_aht20->getHumidity() + ptr->_humidityOffset;

    Serial.println("temperatureOffset:");
    Serial.println(ptr->_temperatureOffset);

    Serial.println("humidityOffset:");
    Serial.println(ptr->_humidityOffset);
    return true;
}