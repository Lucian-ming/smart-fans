#ifndef __MENU_H_
#define __MENU_H_

#include <U8g2lib.h>
#include <MUIU8g2.h>
#include <functional>

namespace abenfanmenu
{
    extern std::function<void()> MenuDinoRunFunc;
    extern std::function<void()> MenuDinoUltramanRunFunc;
    extern std::function<void()> MenuTurnOffFunc;
    extern std::function<void()> MenuWhenWasClosed;
    extern std::function<void(uint8_t)> MenuRGBLightToggleFunc;
    extern std::function<void(int8_t)> MenuChangeTemperatureOffsetFunc;
    extern std::function<void(int8_t)> MenuChangeHumidityOffsetFunc;
    extern std::function<void(uint8_t)> MenuToggleBLEFunc;

    void MenuSetupRGBLightOn(uint8_t);
    void MenuSetupHumidityOffset(uint8_t offset);
    void MenuSetupTemperatureOffset(uint8_t offset);
    void MenuSetupBLEOn(uint8_t);

    uint8_t menuThermometerOffsetValueToIndex(int8_t value);
    int8_t menuThermometerOffsetIndexToValue(uint8_t index);

    class Menu
    {
    public:
        Menu(U8G2 *u8g2);
        virtual ~Menu();

        void setup();
        void loop(std::function<void()> whenFormInactiveFunc);

        void start();
        void gotoForm(uint8_t formId, uint8_t pos);
        void backtoForm();

    protected:
        U8G2 *_u8g2;
        MUIU8G2 _mui;
        bool _isReDraw;
    };

}

#endif // !__MENU_H_
