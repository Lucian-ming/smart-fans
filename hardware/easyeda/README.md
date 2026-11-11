# 嘉立创EDA专业版 与 KiCad 8.x PCB 协同设计指南

本项目同时提供 **KiCad 原生工程文件** 与 **嘉立创EDA专业版改板方案**，兼顾自动化脚本维护与立创一键下单打样。

---

## 一、方案 1：直接在嘉立创EDA专业版导入 / 打开（推荐最快打样路径）

1. **方式 A：打开项目自带的开源基准工程**
   - 打开 [嘉立创EDA专业版客户端或网页版](https://pro.lceda.cn/)；
   - 点击顶部菜单：`文件` → `打开` → `EasyEDA Pro 工程`；
   - 选择工作区中的工程文件：
     `references/01_bishe_voice_fan/pcb/ProDoc_Smart_Fan_PCB_2026-11-03.epro2`
   - **改板动作**：
     1. 将原来的 STM32F103 贴片芯片换成 **HDR-TH_2x20P (STM32 蓝板插座)**；
     2. 将 2-Pin 风扇座更换为 **KF2510-4P (电脑 4-Pin 风扇防呆座)**，Pin 3 (FG) 接 PA8 并上拉 4.7k，Pin 4 (PWM) 接 PA0；
     3. 增加 **EC11 旋转编码器**（A相 PA6, B相 PA7, 中键 PB12）及 3 个轻触按键；
     4. 增加 **PAJ7620U2 手势插座 (1x5P)**，与 OLED 并联于 PB6/PB7，INT 接 PA4；
     5. 增加 **MG90S 舵机排针 (1x3P)**，信号脚接 PB8 (TIM4_CH3)。

2. **方式 B：直接导入 KiCad 8.x 工程**
   - 嘉立创EDA专业版已原生支持 KiCad 导入：
   - 点击菜单：`文件` → `导入` → `KiCad`；
   - 选择本项目目录：`hardware/kicad/fan_ctrl_revA.kicad_pcb`；
   - 系统将自动解析 85×85mm 板框、四角 M3 安装孔、各网络连线与排母位置。

---

## 二、方案 2：使用 KiCad 8.x 本地打开与编辑

工程文件均位于 `hardware/kicad/` 目录：
- **工程配置文件**：`hardware/kicad/fan_ctrl_revA.kicad_pro`
- **原理图文件**：`hardware/kicad/fan_ctrl_revA.kicad_sch`
- **PCB 布局板卡**：`hardware/kicad/fan_ctrl_revA.kicad_pcb`

### 板卡物理尺寸与关键定位点
- **板框外形**：85.0 mm × 85.0 mm（倒圆角 R=3.0 mm），完美置入 3D 打印底座内。
- **4 个 M3 紧固安装孔**（孔径 φ3.2 mm，盘径 φ6.0 mm）：
  - 左上孔：`(X=105, Y=105)`（相对板角偏移 5mm, 5mm）
  - 右上孔：`(X=180, Y=105)`
  - 左下孔：`(X=105, Y=180)`
  - 右下孔：`(X=180, Y=180)`
- **面板朝向与区域规划**：
  - **后侧（Y 轴小侧）**：DC-005 电源座、XL1509 贴片降压滤波、4-Pin 机箱风扇座、MG90S 舵机排针；
  - **中央区域**：STM32 蓝板双排排母 (J1, J2)、ASR-PRO 语音插座、扬声器接口；
  - **前侧微仰面板（Y 轴大侧）**：0.96 OLED (J5)、PAJ7620U2 手势 (J6)、EC11 旋钮 (SW1)、独立轻触按键 (KEY1~KEY3)。

---

## 三、一键导出下单与生产文件

1. **BOM 采购**：直接上传 `hardware/fabrication/bom/BOM_SmartFan_RevA.xlsx` 到立创商城或嘉立创贴片匹配工具。
2. **Gerber 投板**：KiCad 中点击 `文件` → `制造输出` → `Gerbers (.gbr)`，输出至 `hardware/fabrication/gerber/`，打包为 ZIP 即可在嘉立创官网享受免费打样券。
