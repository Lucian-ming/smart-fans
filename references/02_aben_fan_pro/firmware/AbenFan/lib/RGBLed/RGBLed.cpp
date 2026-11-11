#include "RGBLed.h"

RGBLed::RGBLed(
    Adafruit_NeoPixel *pixels) : _pixels(pixels), _on(true), _preferences()
{
}

RGBLed::~RGBLed()
{
    _pixels = nullptr;
}

void RGBLed::setup()
{
    _preferences.begin("rgbled", true);
    _on = _preferences.getBool("on", true);
    _preferences.end();

    xTaskCreatePinnedToCore(&RGBLed::showInTask, "ShowInTask", 2048, this, 2, NULL, 1);
}

void RGBLed::showInTask(void *p)
{
    RGBLed *ptr = (RGBLed *)p;

    while (true)
    {
        if (ptr->isOn())
        {
            uint32_t j;
            for (j = 0; j < 256; j++)
            {
                if (ptr->isOn())
                {
                    ptr->_pixels->setPixelColor(0, ptr->wheel(j & 255));
                    ptr->_pixels->show();
                    vTaskDelay(100);
                }
                else
                {
                    ptr->_pixels->clear();
                    ptr->_pixels->show();
                }
            }
        }
        else
        {
            ptr->_pixels->clear();
            ptr->_pixels->show();
        }
        vTaskDelay(100);
    }
}

bool RGBLed::isOn()
{
    return _on;
}

void RGBLed::toggle(bool on)
{
    _on = on;
    _preferences.begin("rgbled", false);
    _preferences.putBool("on", _on);
    _preferences.end();
}

uint32_t RGBLed::wheel(byte wheelPos)
{
    if (wheelPos < 85)
    {
        return _pixels->Color(wheelPos * 3, 255 - wheelPos * 3, 0);
    }
    else if (wheelPos < 170)
    {
        wheelPos -= 85;
        return _pixels->Color(255 - wheelPos * 3, 0, wheelPos * 3);
    }
    else
    {
        wheelPos -= 170;
        return _pixels->Color(0, wheelPos * 3, 255 - wheelPos * 3);
    }
}