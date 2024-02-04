"""
Smaract MSC2 controll class

@author: Slawa
"""


import os
import sys
Path=os.path.dirname((os.path.abspath(__file__)))
sys.path.append(Path)
SP=Path.split("\\")
i=0
while i<len(SP) and SP[i].find('python')<0:
    i+=1
Pypath='\\'.join(SP[:i+1])
sys.path.append(Pypath)

import smaract.ctl as ctl
from time import sleep
import numpy as np

        
def assert_lib_compatibility(driver=ctl):
    """
    Checks that the major version numbers of the Python API and the
    loaded shared library are the same to avoid errors due to 
    incompatibilities.
    Raises a RuntimeError if the major version numbers are different.
    """
    vapi = driver.api_version
    vlib = [int(i) for i in driver.GetFullVersionString().split('.')]
    if vapi[0] != vlib[0]:
        raise RuntimeError("Incompatible SmarActCTL python api and library version.")

class MCS():
    def __init__(self,holdtime=1000,driver=ctl):
        """holdtime time to hold position after movement in ms"""
        self.Type='SmarAct_MCS2'
        self.home_position=0
        self.units="mm" # in the present version (inn principle, native step is is 100nm)
        self.homed=False
        self.motorlist=[]
        self.holdtime=holdtime
        self.driver=driver
        self.move_mode='None'
        
        assert_lib_compatibility(self.driver)
        
        self.search()
        
    def search(self):
        """search for connected devices"""
        numOfDevices = 0
        motorlist=[]
        buffer = self.driver.FindDevices()
        locators = buffer.split("\n")
        # print(locators)
        self.controllers=locators
        if locators[0] != '':
            for i in range (len(self.controllers)):
                d_handle = ctl.Open(locators[i])
                Nmot=ctl.GetProperty_i32(d_handle, 0, ctl.Property.NUMBER_OF_CHANNELS)
                for j in range(Nmot):
                    Mname=ctl.GetProperty_s(d_handle, j, ctl.Property.POSITIONER_TYPE_NAME)
                    SN=ctl.GetProperty_s(d_handle, j, ctl.Property.DEVICE_SERIAL_NUMBER)
                    motorlist.append([d_handle,i,j,Mname,SN])
                    numOfDevices+=1
            
        self.Nmotors=numOfDevices
        self.motorlist=motorlist
        print("MCS2 number of devices:", numOfDevices)
        
    def connect(self,MotorNumber=0,SN=0):
        """connect to a device"""
        if SN != 0:
            self.SN=SN
            Sns=self.motorlist[:,4]
            N=np.argwhere(Sns==SN)[0][0]
            self.motor=self.motorlist[N]
            print('SN ',ctl.GetProperty_s(self.motor[0], self.motor[2], ctl.Property.DEVICE_SERIAL_NUMBER))
            sensorPresent = self.driver.ChannelState.SENSOR_PRESENT
            self.encoded=sensorPresent
        elif MotorNumber < len(self.motorlist):
            self.motor=self.motorlist[MotorNumber]
            self.SN=self.motorlist[MotorNumber][4]
            print('SN ',ctl.GetProperty_s(self.motor[0], self.motor[2], ctl.Property.DEVICE_SERIAL_NUMBER))
            sensorPresent = self.driver.ChannelState.SENSOR_PRESENT
            self.encoded=sensorPresent
        else:
            print('error: no motor found')
            
        
    
    def wait_for_finished_movement(self):
        status = self.driver.ChannelState.ACTIVELY_MOVING or self.driver.ChannelState.CALIBRATING or self.driver.REFERENCING
        while status:
            sleep(0.03) # 30 ms
            status = self.driver.ChannelState.ACTIVELY_MOVING or self.driver.ChannelState.CALIBRATING or self.driver.REFERENCING
    
    def moveR(self, dx, WaitToMove=True):
        """move relative
        by dx in mm"""
        Dx=dx*10**9 #SDK is using 1 pm steps
        if self.move_mode != 'relative':
            ctl.SetProperty_i32(self.motor[0], self.motor[2], ctl.Property.MOVE_MODE, ctl.MoveMode.CL_RELATIVE)
            self.move_mode = 'relative'
        self.driver.Move(self.motor[0], self.motor[2], int(Dx))
        if WaitToMove:
            self.wait_for_finished_movement()
            
    def moveA(self, x, WaitToMove=True):
        """move absolute 
        to x in mm"""
        X=(x+self.home_position)*10**9 #SDK is using 1 pm steps
        if self.move_mode != 'absolute':
            ctl.SetProperty_i32(self.motor[0], self.motor[2], ctl.Property.MOVE_MODE, ctl.MoveMode.CL_ABSOLUTE)
            self.move_mode = 'absolute'
        self.driver.MovePositionAbsolute_S(self.deviceIndex, self.channelIndex, int(X))
        if WaitToMove:
            self.wait_for_finished_movement()
    
    def calibrate(self, WaitToMove=True):
        """This function may be used to increase the accuracy of the position calculation. It is only executable
            by a positioner that has a sensor attached to it.
            This function should be called once for each channel if the mechanical setup changes (different
            positioners connected to different channels)."""
        self.driver.SetProperty_i32(self.motor[0], self.motor[2], ctl.Property.CALIBRATION_OPTIONS, 0)
        self.driver.Calibrate(self.motor[0], self.motor[2])
        if WaitToMove:
            self.wait_for_finished_movement()
    
    def set_home(self,home):
        """set home position"""
        self.home_position=home
    
    def home(self, WaitToMove=True):
        self.driver.Reference(self.motor[0], self.motor[2])
        if WaitToMove:
            self.wait_for_finished_movement()
        self.homed=True
        self.home_position=0
        
    def move_home(self):
        """move to the home position"""
        self.moveA(self.home_position)
        
    def stop(self):
        self.driver.Stop(self.motor[0], self.motor[2])
        
    def set_velocity(self,V,Accel):
        """set velocity amd acceleration in mm/sec and mm/sec^2
        """
        self.driver.SetProperty_i64(self.motor[0], self.motor[2], ctl.Property.MOVE_VELOCITY, V * (10 ** 9))
        self.driver.SetProperty_i64(self.motor[0], self.motor[2], ctl.Property.MOVE_ACCELERATION, Accel * (10 ** 9))
        self.velocity=V
        self.acceleration=Accel
        
    def get_velocity(self):
        """return velocity and accelearation in mm/sec / mm/sec^2"""
        V=self.driver.ctl.GetProperty_i64(self.motor[0], self.motor[2], ctl.MOVE_VELOCITY)/10**9
        A=self.driver.ctl.GetProperty_i64(self.motor[0], self.motor[2], ctl.MOVE_ACCELERATION)/10**9
        self.velocity=V
        self.acceleration=A
        return V, A
    
    def disconnect(self):
        self.driver.Close(self.motor[0])
    
    @property
    def position(self):
        """in mm"""
        return self.driver.ctl.GetProperty_i64(self.motor[0], self.motor[2], ctl.Property.POSITION)/10**9.
    
    @property
    def is_moving(self):
        return self.driver.ChannelState.ACTIVELY_MOVING or self.driver.ChannelState.CALIBRATING or self.driver.REFERENCING
        
    @property
    def is_homed(self):
        return self.homed
    
#test
# M=MCS()