#include "Fan.h"
#include <Arduino.h>

Fan::Fan(
    uint8_t channel,
    uint8_t pin_a,
    uint8_t pin_b,
    uint8_t pin_pwm,
    uint32_t freq,
    uint8_t resolution_bits,
    uint32_t speedOfLevel1,
    uint32_t speedOfLevel2,
    uint32_t speedOfLevel3,
    uint32_t speedOfLevel4)
    : _channel(channel),
      _pin_a(pin_a),
      _pin_b(pin_b),
      _pin_pwm(pin_pwm),
      _freq(freq),
      _resolution_bits(resolution_bits),
      _speedOfLevel1(speedOfLevel1),
      _speedOfLevel2(speedOfLevel2),
      _speedOfLevel3(speedOfLevel3),
      _speedOfLevel4(speedOfLevel4)
{
}

Fan::~Fan()
{
}

void Fan::setup()
{
    _speed = _speedOfLevel1;
    _level = 1;

    pinMode(_pin_a, OUTPUT);
    pinMode(_pin_b, OUTPUT);

    ledcSetup(_channel, _freq, _resolution_bits);
    ledcAttachPin(_pin_pwm, _channel);
    ledcWrite(_channel, _speed);
}

void Fan::loop()
{
    ledcWrite(_channel, _speed);
}

void Fan::setLevel(uint8_t level)
{
    _level = level;
    switch (_level)
    {
    case 1:
        _speed = _speedOfLevel1;
        break;
    case 2:
        _speed = _speedOfLevel2;
        break;
    case 3:
        _speed = _speedOfLevel3;
        break;
    case 4:
        _speed = _speedOfLevel4;
        break;
    case 0:
        _speed = 0;
        break;
    }
}

void Fan::nextLevel()
{
    switch (_level)
    {
    case 0:
        _speed = _speedOfLevel1;
        _level = 1;
        break;
    case 1:
        _speed = _speedOfLevel2;
        _level = 2;
        break;
    case 2:
        _speed = _speedOfLevel3;
        _level = 3;
        break;
    case 3:
        _speed = _speedOfLevel4;
        _level = 4;
        break;
    case 4:
        _speed = 0;
        _level = 0;
        break;
    }
}

uint8_t Fan::getLevel()
{
    return _level;
}

uint32_t Fan::getSpeed()
{
    return _speed;
}