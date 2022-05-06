#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import LCD1602
import threading

class Keypad():

    def __init__(self, rowsPins, colsPins, keys):
        self.rowsPins = rowsPins
        self.colsPins = colsPins
        self.keys = keys
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.rowsPins, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.colsPins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def read(self):
        pressed_keys = []
        for i, row in enumerate(self.rowsPins):
            GPIO.output(row, GPIO.HIGH)
            for j, col in enumerate(self.colsPins):
                index = i * len(self.colsPins) + j
                if (GPIO.input(col) == 1):
                    pressed_keys.append(self.keys[index])
            GPIO.output(row, GPIO.LOW)
        return pressed_keys

time_s = 0 # タイマーの設定時刻（秒単位）
BEEP_PIN = 20 # ブザーを設定しているPIN

def setup():
    global keypad, last_key_pressed,keys, time_s
    rowsPins = [18,23,24,25]
    colsPins = [ 9,22,27,17] # '9' は、'SPI0_MISO' のPINのこと
    keys = ["1","2","3","A",
            "4","5","6","B",
            "7","8","9","C",
            "*","0","#","D"]
    keypad = Keypad(rowsPins, colsPins, keys)
    last_key_pressed = []
    time_s = 0
    LCD1602.init(0x27, 1)    # init(slave address, background light)
    LCD1602.clear()
    LCD1602.write(0, 0, 'Press \'A\' key to')
    LCD1602.write(2, 1, 'set the TIMER')
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BEEP_PIN, GPIO.OUT, initial=GPIO.LOW)

def lcd_show_set_timer():
    LCD1602.clear()
    LCD1602.write(0,0,'TIMER: %05s sec' % time_s)
    LCD1602.write(0,1,'Press B to START')

def lcd_show_overflow_error():
    LCD1602.clear()
    LCD1602.write(2,0,'OVERFLOW!')
    LCD1602.write(2,1,'Set up AGAIN')

def lcd_show_countdown_time():
    LCD1602.clear()
    LCD1602.write(0,0,'TIMER: %05s sec' % time_s)
    LCD1602.write(0,1,'Press C to STOP')

def lcd_show_time():
    LCD1602.clear()
    LCD1602.write(0,0,'TIME IS UP!')
    LCD1602.write(0,1,'Press D to TOP')

def beep():
    for i in range(5):
        GPIO.output(BEEP_PIN, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(BEEP_PIN, GPIO.LOW)
        time.sleep(0.2)
        i += 1

def start_timer():
    # 1 秒ごとにtimer_sを1減らしていく
    global time_s
    global timer1
    if time_s == 0:
        if 'timer1' in globals():
            timer1.cancel()
        lcd_show_time()
        beep()
        return
    lcd_show_countdown_time()
    timer1 = threading.Timer(1, start_timer)
    timer1.start()
    time_s -= 1

def stop_timer():
    global timer1
    if 'timer1' in globals():
        timer1.cancel()
    lcd_show_set_timer()

def loop():
    global keypad, last_key_pressed, time_s, timer1
    while(True):
        pressed_keys = keypad.read()
        if len(pressed_keys) != 0 and last_key_pressed != pressed_keys:
            if pressed_keys == ["A"]:
                # "A"ボタン押下で、時刻設定画面へ遷移
                lcd_show_set_timer()
            elif pressed_keys == ["B"]:
                # "B"ボタン押下で、タイマー開始
                start_timer()
            elif pressed_keys == ["C"]:
                # "C"ボタン押下で、タイマー一時停止
                stop_timer()
            elif pressed_keys == ["D"]:
                # "D"ボタン押下で、トップページへ遷移
                setup()
            elif pressed_keys[0] in keys:
                # A,B,C,D 以外の数字が押された場合、時刻設定を行う
                if pressed_keys[0] in list(["A","B","C","D","#","*"]):
                    # 数字以外の記号などは無視
                    continue
                # 入力された数値を1の桁として保存していく。例: 1,2を順に押した時、time_s = 12 になる
                time_s = time_s * 10
                time_s += int(pressed_keys[0])
                # 6桁以上の時はエラーを表示して、設定画面へ遷移
                if len(str(time_s)) >= 6:
                    lcd_show_overflow_error()
                    time.sleep(2.5)
                    time_s = 0
                    lcd_show_set_timer()
                lcd_show_set_timer()
            print(pressed_keys)
        last_key_pressed = pressed_keys
        time.sleep(0.1)

def destroy():
    # Release resource
    GPIO.cleanup()
    LCD1602.clear() 
    global timer1
    if 'timer1' in globals():
        timer1.cancel() 

if __name__ == '__main__':
    try:
        setup()
        while True:
            loop()
    except KeyboardInterrupt:
        destroy()
    except Exception:
        destroy()