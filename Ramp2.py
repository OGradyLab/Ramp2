#!/usr/bin/env python3

import tkinter as tk
import RPi.GPIO as GPIO
from threading import Thread
import time

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

motor_pins = [
    {'step': 27, 'direction': 21, 'enable': 4},
    {'step': 26, 'direction': 23, 'enable': 13},
    {'step': 12, 'direction': 20, 'enable': 22},
    {'step': 24, 'direction': 25, 'enable': 19},
    {'step': 16, 'direction': 6, 'enable': 5},
    {'step': 17, 'direction': 18, 'enable': 10}
]

motor_speed = [100] * len(motor_pins)
motor_threads = [None] * len(motor_pins)
motor_direction = [GPIO.HIGH] * len(motor_pins)

for pin_set in motor_pins:
    for pin in pin_set.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

# New global variables to hold the user's settings
ramp_up_speed_var = tk.DoubleVar(value=50)
ramp_down_speed_var = tk.DoubleVar(value=50)
cycle_time_var = tk.DoubleVar(value=2.0)

def start_motor(index):
    global motor_threads
    if motor_threads[index] is None or not motor_threads[index].is_alive():
        motor_threads[index] = Thread(target=run_motor, args=(index,))
        motor_threads[index].start()

def stop_motor(index):
    GPIO.output(motor_pins[index]['enable'], GPIO.HIGH)
    if motor_threads[index] is not None:
        motor_threads[index].join()
        motor_threads[index] = None

def stop_all_motors():
    for index in range(len(motor_pins)):
        stop_motor(index)

def quit_program():
    stop_all_motors()
    root.destroy()

def run_motor(index):
    step_pin = motor_pins[index]['step']
    dir_pin = motor_pins[index]['direction']
    en_pin = motor_pins[index]['enable']

    GPIO.output(en_pin, GPIO.LOW)
    GPIO.output(dir_pin, motor_direction[index])

    while GPIO.input(en_pin) == GPIO.LOW:
        ramp_up_speed = ramp_up_speed_var.get()
        ramp_down_speed = ramp_down_speed_var.get()
        cycle_time = cycle_time_var.get()

        ramp_up_time = cycle_time / (1 + ramp_up_speed / ramp_down_speed)
        ramp_down_time = cycle_time - ramp_up_time

        end_time = time.time() + ramp_up_time
        while time.time() < end_time:
            GPIO.output(step_pin, GPIO.HIGH)
            time.sleep(1.0 / ramp_up_speed / 2)
            GPIO.output(step_pin, GPIO.LOW)
            time.sleep(1.0 / ramp_up_speed / 2)

        end_time = time.time() + ramp_down_time
        while time.time() < end_time:
            GPIO.output(step_pin, GPIO.HIGH)
            time.sleep(1.0 / ramp_down_speed / 2)
            GPIO.output(step_pin, GPIO.LOW)
            time.sleep(1.0 / ramp_down_speed / 2)

def toggle_direction(index):
    motor_direction[index] = GPIO.LOW if motor_direction[index] == GPIO.HIGH else GPIO.HIGH
    GPIO.output(motor_pins[index]['direction'], motor_direction[index])

def create_motor_control(page, motor_index):
    motor_frame = tk.Frame(page, bg='black')
    motor_frame.pack(fill="x", padx=10, pady=5)

    start_button = tk.Button(motor_frame, text=f"Start Motor {motor_index+1}", command=lambda: start_motor(motor_index), bg='green', fg='white')
    start_button.grid(row=0, column=0, padx=(0, 5))

    stop_button = tk.Button(motor_frame, text=f"Stop Motor {motor_index+1}", command=lambda: stop_motor(motor_index), bg='red', fg='white')
    stop_button.grid(row=0, column=1, padx=5)

    direction_button = tk.Button(motor_frame, text=f"Toggle Direction {motor_index+1}", command=lambda: toggle_direction(motor_index), bg='purple', fg='white')
    direction_button.grid(row=0, column=2, padx=5)

    ramp_up_slider = tk.Scale(motor_frame, from_=1, to=255, orient=tk.HORIZONTAL, variable=ramp_up_speed_var, label="Ramp Up Speed", sliderlength=15)
    ramp_up_slider.grid(row=0, column=3, padx=5)

    ramp_down_slider = tk.Scale(motor_frame, from_=1, to=255, orient=tk.HORIZONTAL, variable=ramp_down_speed_var, label="Ramp Down Speed", sliderlength=15)
    ramp_down_slider.grid(row=0, column=4, padx=5)

    cycle_time_slider = tk.Scale(motor_frame, from_=0.1, to=10, resolution=0.1, orient=tk.HORIZONTAL, variable=cycle_time_var, label="Cycle Time (s)", sliderlength=15)
    cycle_time_slider.grid(row=0, column=5, padx=5)

# Create the GUI
root = tk.Tk()
root.title("Pump Perfusion Control")
root.geometry("800x600")

canvas = tk.Canvas(root, bg='black')
canvas.pack(side="left", fill="both", expand=True)

scrollbar = tk.Scrollbar(root, command=canvas.yview)
scrollbar.pack(side="left", fill="y")

canvas.configure(yscrollcommand=scrollbar.set)

frame = tk.Frame(canvas, bg='black')
canvas.create_window((0, 0), window=frame, anchor="nw")

for i in range(len(motor_pins)):
    create_motor_control(frame, i)

stop_all_motors_button = tk.Button(frame, text="Stop All Motors", command=stop_all_motors, bg='blue', fg='white', font=("Arial", 20))
stop_all_motors_button.pack(fill="x", padx=10, pady=5)

quit_program_button = tk.Button(frame, text="Quit Program", command=quit_program, bg='orangered', fg='white', font=("Arial", 20))
quit_program_button.pack(fill="x", padx=10, pady=(0, 5))

frame.update_idletasks()

canvas.config(scrollregion=canvas.bbox("all"))
canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))  # Enable scrolling with the mouse wheel

root.mainloop()
