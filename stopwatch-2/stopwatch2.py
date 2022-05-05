#!/usr/bin/env python3

# 参考 : https://docs.sunfounder.com/projects/davinci-kit/en/latest/3.1.13_game_10_second.html
# 参考 : https://docs.sunfounder.com/projects/davinci-kit/en/latest/1.1.5_4-Digit_7-segment_display.html
# 参考 : https://docs.sunfounder.com/projects/davinci-kit/en/latest/2.1.1_button.html
# 参考 : https://docs.sunfounder.com/projects/davinci-kit/en/latest/3.1.3_reversing_alarm.html

import RPi.GPIO as GPIO
import threading
import time

BUTTON_PIN = 20 # スタート/ストップボタンの接続先
BUZZER_PIN = 16 # ブザーの接続先
SDI     = 24 # Serial Data Input : データの入力）
SRCLK   = 18 # シフト・レジスター・クロック : レジスタにデータをセットするときにHIGHにする
RCLK    = 23 # ストレージ・レジスター・クロック（ラッチ）: セットしたデータを有効にするときにHIGHにする

DIGIT_PINS = (10, 22, 27, 17) # (下から) 1桁目, 2桁目, 3桁目, 4桁目 につながっているPIN番号（BCM）
NUMBERS = (0xc0, 0xf9, 0xa4, 0xb0, 0x99, 0x92, 0x82, 0xf8, 0x80, 0x90) # Common Anode の 7セグを表示するためのHexCode 0~9

timer_100ms = 0 # 計測時間（単位100ms=0.1秒）
status =0       # 0:待機状態 1:計測中 2:計測時刻表示中

def clear_display():
    for i in range(8):
        GPIO.output(SDI, 1)
        GPIO.output(SRCLK, GPIO.HIGH)
        GPIO.output(SRCLK, GPIO.LOW)
    GPIO.output(RCLK, GPIO.HIGH)
    GPIO.output(RCLK, GPIO.LOW)

def hc595_shift(data):
    for i in range(8):
        GPIO.output(SDI, 0x80 & (data << i))
        GPIO.output(SRCLK, GPIO.HIGH)
        GPIO.output(SRCLK, GPIO.LOW)
    GPIO.output(RCLK, GPIO.HIGH)
    GPIO.output(RCLK, GPIO.LOW)

def activate_digit(digit):
    for i in DIGIT_PINS:
        GPIO.output(i,GPIO.LOW)
    GPIO.output(DIGIT_PINS[digit], GPIO.HIGH)

def display():
    global timer_100ms

    # 下から1桁目を描画
    clear_display()
    activate_digit(0)
    hc595_shift(NUMBERS[timer_100ms % 10])

    # 下から2桁目を描画
    clear_display()
    activate_digit(1)
    hc595_shift(NUMBERS[timer_100ms % 100//10]-0x80) # "."を表示するためコードが異なる

    # 下から3桁目を描画
    clear_display()
    activate_digit(2)
    hc595_shift(NUMBERS[timer_100ms % 1000//100])

    # 下から4桁目を描画
    clear_display()
    activate_digit(3)
    hc595_shift(NUMBERS[timer_100ms % 10000//1000])

def beep():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(0.02)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def on_button():
    global status
    global timer_100ms
    global timer1
    # 0が表示されている待機状態でのボタン押下 -> 時間計測スタート
    if status == 0:
        timer_100ms = 0
        timer()
    # 時間計測中のボタン押下 -> 時間計測ストップ
    elif status ==1:
        timer1.cancel()
    # 計測時間表示中のボタン押下 -> リセットして時刻を0に
    elif status ==2:
        timer_100ms = 0
    # status を1変える（ 0->1, 1->2, 2->0 ）
    status = (status+1)%3
    beep()

def loop():
    global timer_100ms
    current_val = 1
    last_val = 1
    while True:
        display()
        current_val=GPIO.input(BUTTON_PIN) # ボタン押下中のみ 0 が返る
        if (current_val == 0) and (last_val == 1):
            on_button()
        last_val=current_val

def timer():
    # 0.1 秒ごとにcounterを1追加していく counterは100ms単位のストップウオッチ
    global timer_100ms
    global timer1
    timer1 = threading.Timer(0.1, timer)
    timer1.start()
    timer_100ms += 1

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SDI, GPIO.OUT)
    GPIO.setup(RCLK, GPIO.OUT)
    GPIO.setup(SRCLK, GPIO.OUT)
    for i in DIGIT_PINS:
        GPIO.setup(i, GPIO.OUT)
    GPIO.setup(BUTTON_PIN, GPIO.IN)
    GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)

def destroy():
    GPIO.cleanup()
    global timer1
    timer1.cancel()

if __name__ == '__main__':
    setup()
    try:
        loop()
    except: #KeyboardInterrupt:
        destroy()