# AbenFan

## 项目架构

```mermaid
graph TD
    subgraph 硬件层
        ESP32[ESP32-S3]
        OLED[OLED显示屏]
        FAN[风扇电机]
        AHT20[温湿度传感器]
        RGB[RGB LED]
        BTN[按钮]
        WIFI[WiFi模块]
    end

    subgraph 驱动层
        I2C1[I2C总线1]-->|OLED通信|OLED
        I2C2[I2C总线2]-->|AHT20通信|AHT20
        PWM[PWM控制器]-->|速度控制|FAN
        GPIO[GPIO控制器]-->|按键输入|BTN
        GPIO-->|RGB控制|RGB
        GPIO-->|系统开关|OFF[电源控制]
    end

    subgraph 功能模块层
        FAN_CTL[风扇控制模块]-->PWM
        THERMO[温湿度模块]-->I2C2
        DISPLAY[显示控制]-->I2C1
        RGB_CTL[RGB控制]-->GPIO
        MENU[菜单系统]-->DISPLAY
        GAME[恐龙游戏]-->DISPLAY
        POWER[电源管理]-->GPIO
    end

    subgraph 应用层
        MAIN[主程序]-->|初始化|FAN_CTL
        MAIN-->|初始化|THERMO
        MAIN-->|初始化|DISPLAY
        MAIN-->|初始化|RGB_CTL
        MAIN-->|初始化|MENU
        MAIN-->|初始化|GAME
        MAIN-->|初始化|POWER
    end

    subgraph 通信接口层
        BLE[蓝牙模块]-->|状态同步|FAN_CTL
        BLE-->|数据读取|THERMO
        BLE-->|控制|RGB_CTL
        BLE-->|远程控制|REMOTE[远程设备]

        WIFI_MGR[WiFi管理器]-->WIFI
        WIFI_MGR-->|Web配置|CONFIG[系统配置]
    end

    BTN-->|输入触发|MENU
    BTN-->|游戏控制|GAME
    MENU-->|参数设置|THERMO
    MENU-->|开关控制|BLE
    MENU-->|灯光控制|RGB_CTL
    MENU-->|风扇控制|FAN_CTL
```

## 烧录命令

```shell
esptool.py --chip esp32s3 merge_bin -o .pio/build/esp32-s3-devkitc-1/flash.bin --flash_mode dio --flash_size 16MB 0x1000 .pio/build/esp32-s3-devkitc-1/bootloader.bin 0x8000 .pio/build/esp32-s3-devkitc-1/partitions.bin 0x10000 .pio/build/esp32-s3-devkitc-1/firmware.bin

esptool.py --chip esp32s3 merge_bin -o .pio/build/esp32-s3-devkitc-1/flash.bin --flash_mode dio --flash_size 16MB 0x1000 .pio/build/esp32-s3-devkitc-1/bootloader.bin 0x8000 .pio/build/esp32-s3-devkitc-1/partitions.bin 0x10000 .pio/build/esp32-s3-devkitc-1/firmware.bin 0xC90000 .pio/build/esp32-s3-devkitc-1/spiffs.bin

esptool.py --chip esp32s3 --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size 16MB 0x0 .pio/build/esp32-s3-devkitc-1/flash.bin
```
