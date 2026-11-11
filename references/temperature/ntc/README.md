# NTC 热敏电阻参考 (From Reference 1)

## 1. 硬件连接
- 型号：MF58 104F3950（标称阻值 100kΩ @ 25℃，B值 3950）
- 分压电路：VCC (3.3V) -> 10kΩ 精密电阻 (0.1% 或 1%) -> ADC_IN (PA5) -> NTC -> GND
- 滤波：并联 100nF 贴片电容到地抑制噪声。

## 2. 计算算法（Steinhart-Hart 公式）

```c
#include <math.h>

#define T25  (273.15f + 25.0f)
#define R25  100000.0f          /* 25℃时阻值 100k */
#define B_VAL 3950.0f           /* B常数 */

float NTC_CalculateTemp(uint16_t adc_val)
{
    float v_ntc = (float)adc_val * 3.3f / 4096.0f;
    float r_ntc = (v_ntc / (3.3f - v_ntc)) * 10000.0f; // 10k上拉分压
    float n1 = (logf(R25) - logf(r_ntc)) / B_VAL;
    float n2 = (1.0f / T25) - n1;
    float temp_c = (1.0f / n2) - 273.15f;
    return temp_c;
}
```
