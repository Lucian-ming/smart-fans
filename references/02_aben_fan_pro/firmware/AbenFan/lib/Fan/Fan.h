#ifndef __FAN_H_
#define __FAN_H_

#include <functional>

class Fan
{
public:
    Fan(
        uint8_t channel,
        uint8_t pin_a,
        uint8_t pin_b,
        uint8_t pin_pwm,
        uint32_t freq,
        uint8_t resolution_bits,
        uint32_t speedOfLevel1,
        uint32_t speedOfLevel2,
        uint32_t speedOfLevel3,
        uint32_t speedOfLevel4);
    virtual ~Fan();

    void setup();
    void loop();

    uint32_t getSpeed();
    uint8_t getLevel();
    void nextLevel();
    void setLevel(uint8_t level);

protected:
    uint32_t _speed;
    uint8_t _level;

    uint8_t _channel;
    uint8_t _pin_a;
    uint8_t _pin_b;
    uint8_t _pin_pwm;
    uint32_t _freq;
    uint8_t _resolution_bits;
    uint32_t _speedOfLevel1;
    uint32_t _speedOfLevel2;
    uint32_t _speedOfLevel3;
    uint32_t _speedOfLevel4;
};

#endif // !__FAN_H_