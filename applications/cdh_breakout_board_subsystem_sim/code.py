"""
Entry point for a testing application that simulates the a subsystem's microcontroller
which may talk to CDH. This testing application runs on a custom breakout board.
"""

from tasks.inter_subsystem_rs485 import inter_subsystem_rs485_reciever_task

if __name__ == "__main__":
    inter_subsystem_rs485_reciever_task()
