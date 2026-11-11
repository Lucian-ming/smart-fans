# PAJ7620U2 手势传感器参考驱动

## 1. 寄存器速查

- I2C 设备地址：`0x73` (7-bit)，写地址 `0xE6`，读地址 `0xE7`
- 唤醒寄存器：Bank0 寄存器 `0x00`
- 手势标志寄存器：
  - `0x43`：Gesture Result High Byte
  - `0x44`：Gesture Result Low Byte

## 2. 9 种手势位掩码定义

```c
#define PAJ7620_GESTURE_UP             0x0001
#define PAJ7620_GESTURE_DOWN           0x0002
#define PAJ7620_GESTURE_LEFT           0x0004
#define PAJ7620_GESTURE_RIGHT          0x0008
#define PAJ7620_GESTURE_FORWARD        0x0010
#define PAJ7620_GESTURE_BACKWARD       0x0020
#define PAJ7620_GESTURE_CLOCKWISE      0x0040
#define PAJ7620_GESTURE_COUNTER_CLOCK  0x0080
#define PAJ7620_GESTURE_WAVE           0x0100
```

## 3. 读取时序逻辑（STM32 HAL）

```c
uint16_t PAJ7620_ReadGesture(I2C_HandleTypeDef *hi2c)
{
    uint8_t data[2] = {0};
    // 读取 0x43 处 2 个字节
    if (HAL_I2C_Mem_Read(hi2c, (0x73 << 1), 0x43, I2C_MEMADD_SIZE_8BIT, data, 2, 50) == HAL_OK) {
        return ((uint16_t)data[1] << 8) | data[0];
    }
    return 0;
}
```
