from machine import Pin, UART
import genose
import time

uart = UART(2, baudrate=9600)#Begin communication with HMI
end_cmd = b'\xFF\xFF\xFF'
#Send instruction to HMI display
def send(cmd):
    uart.write(cmd)
    uart.write(end_cmd)
    uart.read()
genose.pump("Heating")#Start pum
#Update sleep in HMI
while True:
    instruct = str(uart.read())
    instruct = instruct[-2]
    print(instruct)
    if instruct == "1":
        print("sampling")
        filename = genose.Sampling(10,40,50)
        pred = genose.get_predict(filename,10,40,50)
        send("n0.val=0x0{}".format(pred))
    print("waiting")
    time.sleep(1)