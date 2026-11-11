#ifndef __THERMOMETER_H_
#define __THERMOMETER_H_

#include <AHT20.h>
#include <Preferences.h>

typedef struct
{
    float temperature;
    float humidity;
} ThermometerValue;

class Thermometer
{
public:
    Thermometer(AHT20 *aht20, float temperatureOffset, float humidityOffset);
    Thermometer(AHT20 *aht20, ThermometerValue *value, float temperatureOffset, float humidityOffset);
    virtual ~Thermometer();

    void setup();
    void loop();

    float getTemperature();
    float getHumidity();

    float getTemperatureOffset();
    float getHumidityOffset();
    void setTemperatureOffset(float temperatureOffset);
    void setHumidityOffset(float humidityOffset);

    uint8_t isAvailable();

protected:
    AHT20 *_aht20;
    ThermometerValue *_value;
    uint8_t _isAvailable;
    float _temperatureOffset;
    float _humidityOffset;
    static bool refreshAHT20(void *);
    Preferences _preferences;
};

#endif // !__THERMOMETER_H_