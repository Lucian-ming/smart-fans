#include "Menu.h"
#include "config.h"

#define MUI_TITLE(text) MUI_STYLE(1) MUI_LABEL(5, 10, text) MUI_XY("HR", 0, 13) MUI_STYLE(0)
#define MUI_LISTBUTTONS(id) MUI_XYA(id, 5, 25, 0) MUI_XYA(id, 5, 37, 1) MUI_XYA(id, 5, 49, 2) MUI_XYA(id, 5, 61, 3)

namespace abenfanmenu
{

    uint8_t menuRGBLightOn = 1;
    uint8_t menuTemperatureOffsetIndex = 5;
    uint8_t menuHumidityOffsetIndex = 5;
    uint8_t menuBLEOn = 0;

    void MenuSetupRGBLightOn(uint8_t on)
    {
        menuRGBLightOn = on;
    }

    void MenuSetupTemperatureOffset(uint8_t offset)
    {
        menuTemperatureOffsetIndex = menuThermometerOffsetValueToIndex(offset);
    }

    void MenuSetupHumidityOffset(uint8_t offset)
    {
        menuHumidityOffsetIndex = menuThermometerOffsetValueToIndex(offset);
    }

    uint8_t menuThermometerOffsetValueToIndex(int8_t value)
    {
        return value + 5;
    }

    int8_t menuThermometerOffsetIndexToValue(uint8_t index)
    {
        return index - 5;
    }

    void MenuSetupBLEOn(uint8_t on)
    {
        menuBLEOn = on;
    }

    uint8_t muiHrule(mui_t *ui, uint8_t msg)
    {
        u8g2_t *u8g2 = mui_get_U8g2(ui);
        switch (msg)
        {
        case MUIF_MSG_DRAW:
            u8g2_DrawHLine(u8g2, 0, mui_get_y(ui), u8g2_GetDisplayWidth(u8g2));
            break;
        }
        return 0;
    }

    uint8_t muiStartDinoRun(mui_t *ui, uint8_t msg)
    {
        if (msg == MUIF_MSG_FORM_START)
        {
            ((MUIU8G2 *)ui)->leaveForm();
            if (MenuDinoRunFunc != nullptr)
            {
                MenuDinoRunFunc();
            }
        }
        return 0;
    }

    uint8_t muiStartDinoUltramanRun(mui_t *ui, uint8_t msg)
    {
        if (msg == MUIF_MSG_FORM_START)
        {
            ((MUIU8G2 *)ui)->leaveForm();
            if (MenuDinoUltramanRunFunc != nullptr)
            {
                MenuDinoUltramanRunFunc();
            }
        }
        return 0;
    }

    uint8_t muiTurnOff(mui_t *ui, uint8_t msg)
    {
        if (msg == MUIF_MSG_FORM_START)
        {
            ((MUIU8G2 *)ui)->leaveForm();
            if (MenuTurnOffFunc != nullptr)
            {
                MenuTurnOffFunc();
            }
        }
        return 0;
    }

    uint8_t muiSaveValues(mui_t *ui, uint8_t msg)
    {
        if (msg == MUIF_MSG_FORM_START)
        {
            if (MenuRGBLightToggleFunc != nullptr)
            {
                MenuRGBLightToggleFunc(menuRGBLightOn);
            }
            if (MenuChangeTemperatureOffsetFunc != nullptr)
            {
                MenuChangeTemperatureOffsetFunc(menuThermometerOffsetIndexToValue(menuTemperatureOffsetIndex));
            }
            if (MenuChangeHumidityOffsetFunc != nullptr)
            {
                MenuChangeHumidityOffsetFunc(menuThermometerOffsetIndexToValue(menuHumidityOffsetIndex));
            }
            if (MenuToggleBLEFunc != nullptr)
            {
                MenuToggleBLEFunc(menuBLEOn);
            }

            Serial.println("save values from menu");
        }
        return 0;
    }

    muif_t muifList[] = {
        /* normal text style */
        MUIF_U8G2_FONT_STYLE(0, u8g2_font_helvR08_tr),

        /* bold text style */
        MUIF_U8G2_FONT_STYLE(1, u8g2_font_helvB08_tr),

        /* monospaced font */
        MUIF_U8G2_FONT_STYLE(2, u8g2_font_profont12_tr),

        /* food and drink */
        MUIF_U8G2_FONT_STYLE(3, u8g2_font_streamline_food_drink_t),

        /* horizontal line (hrule) */
        MUIF_RO("HR", muiHrule),

        /* main menu */
        MUIF_RO("GP", mui_u8g2_goto_data),
        MUIF_BUTTON("GC", mui_u8g2_goto_form_w1_pi),

        /* Goto Form Button where the width is equal to the size of the text, spaces can be used to extend the size */
        MUIF_BUTTON("G1", mui_u8g2_btn_goto_wm_fi),

        /* MUI_GOTO uses the fixed ".G" id and is intended for goto buttons. This is a full display width style button */
        MUIF_GOTO(mui_u8g2_btn_goto_w1_pi),

        /* register MUI_LABEL, which is used to place read only text on a form */
        MUIF_U8G2_LABEL(),

        // games
        MUIF_RO("LG", mui_u8g2_goto_data),

        // save values
        MUIF_RO("SV", muiSaveValues),

        // Dino Run
        MUIF_RO("DR", muiStartDinoRun),

        // Dino Ultraman Run
        MUIF_RO("DU", muiStartDinoUltramanRun),

        // Turn Off
        MUIF_RO("TO", muiTurnOff),

        // rgb light on
        MUIF_VARIABLE("IO", &menuRGBLightOn, mui_u8g2_u8_opt_line_wa_mse_pi),

        // temperature offset
        MUIF_VARIABLE("IT", &menuTemperatureOffsetIndex, mui_u8g2_u8_opt_line_wa_mse_pi),

        // humidity Offset
        MUIF_VARIABLE("IH", &menuHumidityOffsetIndex, mui_u8g2_u8_opt_line_wa_mse_pi),

        // BLE
        MUIF_VARIABLE("IB", &menuBLEOn, mui_u8g2_u8_opt_line_wa_mse_pi),

    };

    fds_t fdsData[] =
        MUI_FORM(1) MUI_AUX("SV") MUI_TITLE("Aben Fan Pro") MUI_DATA("GP", MUI_10 "Turn Off|" MUI_20 "Games|" MUI_30 "RGB Light|" MUI_40 "Settings|") MUI_LISTBUTTONS("GC")
            MUI_FORM(10) MUI_AUX("TO")
                MUI_FORM(20) MUI_TITLE("Games") MUI_DATA("LG", MUI_1 "Goto Main Menu|" MUI_21 "Dino Run|" MUI_22 "Dino Ultraman|" MUI_23 "Street Fighter|") MUI_LISTBUTTONS("GC")
                    MUI_FORM(21) MUI_AUX("DR")
                        MUI_FORM(22) MUI_AUX("DU")
                            MUI_FORM(23) MUI_STYLE(1) MUI_LABEL(5, 10, "Street Fighter") MUI_XY("HR", 0, 13) MUI_STYLE(0) MUI_LABEL(5, 29, "Coming soon...") MUI_XYAT("G1", 64, 59, 20, " OK ")
                                MUI_FORM(30) MUI_TITLE("RGB Light") MUI_LABEL(5, 29, "Turn:") MUI_XYAT("IO", 60, 29, 60, "Off|On") MUI_XYAT("G1", 64, 59, 1, " OK ")

                                    MUI_FORM(40) MUI_AUX("SV") MUI_TITLE("Settings") MUI_DATA("LG", MUI_1 "Goto Main Menu|" MUI_41 "Thermometer Offset|" MUI_42 "Wi-Fi|" MUI_43 "Bluetooth|" MUI_99 "Version|") MUI_LISTBUTTONS("GC")
                                        MUI_FORM(41) MUI_TITLE("Thermometer Offset") MUI_LABEL(5, 27, "Temp. Offset:") MUI_XYAT("IT", 76, 27, 10, "-5|-4|-3|-2|-1|+0|+1|+2|+3|+4|+5") MUI_XY("DT", 100, 27) MUI_LABEL(5, 41, "Hum. Offset:") MUI_XYAT("IH", 76, 41, 10, "-5|-4|-3|-2|-1|+0|+1|+2|+3|+4|+5") MUI_XYAT("G1", 64, 59, 40, " OK ")
                                            MUI_FORM(43) MUI_TITLE("Bluetooth") MUI_LABEL(5, 29, "Turn:") MUI_XYAT("IB", 60, 29, 60, "Off|On") MUI_XYAT("G1", 64, 59, 40, " OK ")
                                                MUI_FORM(99) MUI_TITLE("Version") MUI_LABEL(5, 29, VERSION) MUI_XYAT("G1", 64, 59, 40, " OK ")

        ;

    Menu::Menu(U8G2 *u8g2) : _u8g2(u8g2), _isReDraw(true), _mui()
    {
    }

    Menu::~Menu()
    {
        _u8g2 = nullptr;
        _isReDraw = true;
    }

    void Menu::setup()
    {
        _mui.begin(*_u8g2, fdsData, muifList, sizeof(muifList) / sizeof(muif_t));
    }

    void Menu::start()
    {
        _mui.gotoForm(1, 0);
        _isReDraw = true;
    }

    void Menu::gotoForm(uint8_t formId, uint8_t pos)
    {
        _mui.gotoForm(formId, pos);
        _isReDraw = true;
    }

    void Menu::backtoForm()
    {
        _mui.restoreForm();
        _isReDraw = true;
    }

    void Menu::loop(std::function<void()> whenFormInactiveFunc)
    {
        if (_mui.isFormActive())
        {
            if (_isReDraw)
            {
                _u8g2->firstPage();
                do
                {
                    _mui.draw();
                } while (_u8g2->nextPage());
                _isReDraw = false;
            }

            uint8_t pos;
            uint8_t formId;
            switch (_u8g2->getMenuEvent())
            {
            case U8X8_MSG_GPIO_MENU_SELECT:
                _mui.sendSelect();
                _isReDraw = true;
                break;
            case U8X8_MSG_GPIO_MENU_NEXT:
                formId = _mui.getCurrentFormId();
                pos = _mui.getCurrentCursorFocusPosition();
                if (formId == 1 && pos == 3)
                {
                    MenuWhenWasClosed();
                    _mui.leaveForm();
                    break;
                }
                _mui.nextField();
                _isReDraw = true;
                break;
            case U8X8_MSG_GPIO_MENU_PREV:
                _mui.prevField();
                _isReDraw = true;
                break;
            }
        }
        else
        {
            if (whenFormInactiveFunc != nullptr)
            {
                whenFormInactiveFunc();
            }
        }
    }

}