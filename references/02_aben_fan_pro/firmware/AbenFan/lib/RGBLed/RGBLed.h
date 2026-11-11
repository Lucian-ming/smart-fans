#ifndef __RGBLed_H_
#define __RGBLed_H_

#include <Adafruit_NeoPixel.h>
#include <functional>
#include <Preferences.h>

class RGBLed
{
public:
    RGBLed(Adafruit_NeoPixel *pixels);
    virtual ~RGBLed();

    void setup();
    bool isOn();
    void toggle(bool on);

protected:
    Adafruit_NeoPixel *_pixels;
    uint32_t wheel(byte WheelPos);
    static void showInTask(void *);
    bool _on;
    Preferences _preferences;
};

#endif // !__RGBLed_H_