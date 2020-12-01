import network,machine,uos,os,gc,sys,time,sdcard,json,urequests,random,ads1x15
from machine import Pin,PWM,deepsleep,SPI,I2C
from umqtt.robust import MQTTClient

#Change th
#Request predicting
def get_predict(filename,th,ts,tp):
    ts=ts+th
    tp=tp+ts
    #SD card setup
    #MOSI(IO23) MISO(19) SCK(18)
    spisd=SPI(-1,sck=Pin(18),mosi=Pin(23),miso=Pin(19))
    #CS(5)
    sd=sdcard.SDCard(spisd,Pin(5))
    uos.mount(sd,'/sd')

    #WiFi setup
    WIFI_SSID = 'OPPOA5s'
    WIFI_PASSWORD = 'RI@Wifi17'
    ap_if = network.WLAN(network.AP_IF)
    wifi = network.WLAN(network.STA_IF)

    ap_if.active(False)

    # connect the device to the WiFi network
    wifi.active(True)
    wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    time.sleep(5)

    #Read data from csv file
    Data=[]
    label=[]
    no_Rows=0
    filename="/sd/{}".format(filename)
    with open(filename,'r') as file:
        for line in file:
            if no_Rows <= ts & no_Rows > 0:
                line=line.rstrip('\n')
                line=line.rstrip('\r')
                Data.append(line.split(','))
                no_Rows+=1
            elif no_Rows == 0:
                line=line.rstrip('\n')
                line=line.rstrip('\r')
                label.append(line.split(','))
                no_Rows+=1
            else:
                no_Rows+=1
    column = label[0]
    #Convert data into json format
    js = {"columns":column, "data":Data}
    jsd = json.dumps(js)
    dfj = json.loads(jsd)
    #url to cloud system
    url = 'https://test-torc.herokuapp.com/torc-extract/?th={}'.format(ts)
    result = urequests.post(url,data=jsd)
    print(result)
    print(result.text)
    #Unmount SD card and deactivate WiFi
    uos.umount('/sd')
    wifi.active(False)
    ap_if.active(True)
    return result.text[-3]

#Sampling phase
def Sampling(th,ts,tp):
    thi = th
    tsi = ts+th
    tpi = tp+ts
    spisd=SPI(-1,sck=Pin(18),mosi=Pin(23),miso=Pin(19))
    sd=sdcard.SDCard(spisd,Pin(5))
    uos.mount(sd,'/sd')
    filename = time.localtime()
    filename = "Sampling_{}-{}-{}_{}-{}-{}.csv".format(filename[3],filename[4],filename[5],filename[2],filename[1],filename[0])
    f = open("/sd/{}".format(filename),"a")
    f.write("time(s),TGS 2600,TGS 2602,TGS 2611,TGS 2620,TGS 813,TGS 816,TGS 821,TGS 822,TGS 826,TGS 832,Temp,Humid\n")
    t = 0
    ti = 0
    data = Sensor_Read(th)
    while t<thi:
        print("Heating_t:{}".format(t))
        S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12 = data[ti]
        f.write("{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(t,S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12))
        print("{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(t,S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12))
        ti+=1
        t+=1
    pump("Sampling")
    data = Sensor_Read(ts)
    ti=0
    while t>=thi and t<tsi:
        print("Sampling_t:{}".format(t))
        S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12 = data[ti]
        f.write("{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(t,S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12))
        print("{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(t,S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12))
        ti+=1
        t+=1
    pump("Purging")
    data = Sensor_Read(tp)
    ti=0
    while t>=tsi and t<tpi:
        print("Purging_t:{}".format(t))
        S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12 = data[ti]
        f.write("{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(t,S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12))
        print("{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(t,S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12))
        ti+=1
        t+=1
    f.close()
    uos.umount('/sd')
    return filename

#Reading sensor values
def Sensor_Read(t):
    import ads1x15, bme680
    from machine import Pin,I2C
    #Turn on sensor
    SO = Pin(4,Pin.OUT)
    SO.on()
    i2c = I2C(scl=Pin(22),sda=Pin(21))
    i2c.init(scl=Pin(22),sda=Pin(21))
    i2c.scan()
    #address=0x77
    bme = bme680.BME680_I2C(i2c)
    adc = ads1x15.ADS1115(i2c)
    iaq_read = 0
    iaq_pred = 0
    iaq_stat = 0
    iaq_b3 = 0
    iaq_resist = 0
    iaq_tvoc = 0

    data = []
    for i in range(t):
        time.sleep(1)
        S1 = adc.read(channel1=0) * 0.125
        S2 = adc.read(channel1=1) * 0.125
        S3 = adc.read(channel1=2) * 0.125
        S4 = adc.read(channel1=3) * 0.125
        S5 = bme.temperature#temperature
        S6 = bme.humidity#humidity
        S7 = bme.pressure#pressure
        S8 = bme.gas#gas
        try:
            iaq_read = i2c.readfrom(90,9)
        except:
            print("etimedout")
            i2c = I2C(scl=Pin(22),sda=Pin(21))
            i2c.init(scl=Pin(22),sda=Pin(21))
            i2c.scan()
            iaq_read = i2c.readfrom(90,9)
        #bug: if the first reading is the error?
        if iaq_read[8]==255 and iaq_read[7]==255:
            iaq_pred = iaq_pred
            iaq_stat = iaq_stat
            iaq_b3 = iaq_b3
            iaq_resist = iaq_resist
            iaq_tvoc = iaq_tvoc
        else:
            iaq_pred = (iaq_read[0]*2**8)+iaq_read[1]
            iaq_stat = iaq_read[2]
            iaq_b3 = iaq_read[3]
            iaq_resist = (iaq_read[4]*2**(16))+(iaq_read[5]*2**8)+iaq_read[6]
            iaq_tvoc = (iaq_read[7]*2**8)+iaq_read[8]
        S9 = iaq_pred
        S10 = iaq_resist
        S11 = iaq_tvoc
        S12=random.uniform(100,5000)
        data.append([S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12])
    return data

'''
def iaq_reading(t):
    from machine import Pin,I2C
    import time
    SO = Pin(4,Pin.OUT)#Sensor power
    SO.on()
    i2c = I2C(scl=Pin(22),sda=Pin(21))
    i2c.init(scl=Pin(22),sda=Pin(21))
    i2c.scan()
    iaq_read = 0
    iaq_pred = 0
    iaq_stat = 0
    iaq_b3 = 0
    iaq_resist = 0
    iaq_tvoc = 0
    for i in range(t):
        try:
            iaq_read = i2c.readfrom(90,9)
        except:
            print("etimedout")
            i2c = I2C(scl=Pin(22),sda=Pin(21))
            i2c.init(scl=Pin(22),sda=Pin(21))
            i2c.scan()
            iaq_read = i2c.readfrom(90,9)
        #bug: if the first reading is the error?
        if iaq_read[8]==255 and iaq_read[7]==255:
            print(
                "t={},read={},pred={},stat={},b3={},resist={},tvoc={}".format(
                i,iaq_read, iaq_pred, iaq_stat,
                iaq_b3, iaq_resist, iaq_tvoc))
            time.sleep(1)
        else:
            iaq_pred = (iaq_read[0]*2**8)+iaq_read[1]
            iaq_stat = iaq_read[2]
            iaq_b3 = iaq_read[3]
            iaq_resist = (iaq_read[4]*2**(16))+(iaq_read[5]*2**8)+iaq_read[6]
            iaq_tvoc = (iaq_read[7]*2**8)+iaq_read[8]
            print(
                "t={},read={},pred={},stat={},b3={},resist={},tvoc={}".format(
                i,iaq_read, iaq_pred, iaq_stat,
                iaq_b3, iaq_resist, iaq_tvoc))
            time.sleep(1)
'''
#Pump setting
def pump(state):
    if state=="Heating":
        p2 = Pin(2,Pin.OUT)
        p2wm = machine.PWM(p2)
        p13 = Pin(13,Pin.OUT)
        p13.on()
        p2wm.freq(1000)
        p2wm.duty(512)
    if state=="Sampling":
        p32 = Pin(32,Pin.OUT)
        p25 = Pin(25,Pin.OUT)
        p33 = Pin(33,Pin.OUT)
        p26 = Pin(26,Pin.OUT)
        p32.on()
        p25.on()
        p33.off()
        p26.off()
    if state=="Purging":
        p32 = Pin(32,Pin.OUT)
        p25 = Pin(25,Pin.OUT)
        p33 = Pin(33,Pin.OUT)
        p26 = Pin(26,Pin.OUT)
        p32.off()
        p25.off()
        p33.off()
        p26.off()