cmake_minimum_required(VERSION 3.16)

# Set cross-compilation toolchain
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_TRY_COMPILE_TARGET_TYPE "STATIC_LIBRARY")

set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_OBJCOPY arm-none-eabi-objcopy)
set(CMAKE_OBJDUMP arm-none-eabi-objdump)
set(CMAKE_SIZE arm-none-eabi-size)

project(smart_fan C ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# CPU and architecture flags
set(CPU_FLAGS "-mcpu=cortex-m3 -mthumb")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${CPU_FLAGS} -Wall -Wextra -Wno-unused-parameter -fdata-sections -ffunction-sections -O2 -g")
set(CMAKE_ASM_FLAGS "${CMAKE_ASM_FLAGS} ${CPU_FLAGS} -x assembler-with-cpp")

# Preprocessor definitions
add_definitions(
    -DSTM32F103xB
    -DUSE_HAL_DRIVER
    -DHSE_VALUE=8000000U
)

# Include directories
include_directories(
    include
    src
    Drivers/CMSIS/Include
    Drivers/CMSIS/Device/ST/STM32F1xx/Include
    Drivers/STM32F1xx_HAL_Driver/Inc
)

# Source files
set(SOURCES
    startup_stm32f103xb.s
    src/syscalls.c
    src/system_stm32f1xx.c
    src/stm32f1xx_it.c
    src/main.c

    # HAL Driver sources
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_gpio.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_gpio_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_cortex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_pwr.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_uart.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_tim.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_tim_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_dma.c

    # Hardware abstraction layer
    src/hal/delay_us.c

    # Modular drivers
    src/drivers/buzzer.c
    src/drivers/button.c
    src/drivers/motor.c
    src/drivers/servo.c
    src/drivers/encoder.c
    src/drivers/i2c_bus.c
    src/drivers/ssd1306.c
    src/drivers/paj7620.c
    src/drivers/dht11.c
    src/drivers/voice_asr.c

    # Application & state machine
    src/app/fan_fsm.c
    src/app/cli_test.c
)

# Linker flags
set(LINKER_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/STM32F103C8Tx_FLASH.ld)
set(CMAKE_EXE_LINKER_FLAGS "${CPU_FLAGS} -T${LINKER_SCRIPT} --specs=nano.specs --specs=nosys.specs -u _printf_float -lc -lm -Wl,-Map=${PROJECT_NAME}.map,--cref -Wl,--gc-sections")

# Executable target
add_executable(${PROJECT_NAME}.elf ${SOURCES})

# Post-build commands: generate bin, hex and display size
add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary ${PROJECT_NAME}.elf ${PROJECT_NAME}.bin
    COMMAND ${CMAKE_OBJCOPY} -O ihex ${PROJECT_NAME}.elf ${PROJECT_NAME}.hex
    COMMAND ${CMAKE_SIZE} --format=berkeley ${PROJECT_NAME}.elf
    COMMENT "Building ${PROJECT_NAME}.bin, ${PROJECT_NAME}.hex and size summary"
)

# ==============================================================================
# MAX7219 Dot Matrix Hardware Test Target (matrix_test.bin / matrix_test.hex)
# ==============================================================================
set(MATRIX_TEST_SOURCES
    startup_stm32f103xb.s
    src/syscalls.c
    src/system_stm32f1xx.c
    src/stm32f1xx_it.c
    src/matrix_test_main.c
    src/drivers/max7219.c
    src/hal/delay_us.c

    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_gpio.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_gpio_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_cortex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_pwr.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_uart.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_tim.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_tim_ex.c
    Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_dma.c
)

add_executable(matrix_test.elf ${MATRIX_TEST_SOURCES})

add_custom_command(TARGET matrix_test.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary matrix_test.elf matrix_test.bin
    COMMAND ${CMAKE_OBJCOPY} -O ihex matrix_test.elf matrix_test.hex
    COMMAND ${CMAKE_SIZE} --format=berkeley matrix_test.elf
    COMMENT "Building matrix_test.bin, matrix_test.hex"
)

