"""
Entry point for a testing application that simulates the CDH microcontroller on
a custom breakout board.
"""

from tasks.inter_subsystem_rs485 import inter_subsystem_rs485_sender_task

if __name__ == "__main__":
    inter_subsystem_rs485_sender_task()
