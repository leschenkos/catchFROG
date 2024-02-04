"""
Motor class

@author: Slawa
"""

import os
import sys
Path=os.path.dirname((os.path.abspath(__file__)))
sys.path.append(Path)
SP=Path.split("\\")
Pypath='\\'.join(SP[:-1])
sys.path.append(Pypath)
import numpy as np
import matplotlib.pyplot as plt

from Thor_motor_class import ThorMotor
# from Zaber_motor_class import ZaberMotor
from Motor_emulator import Motor_emulator

try:
    from SmarActSCU import *
except :
    print('smaract SCU driver doesnt work')
    
try:
    from SmarActMCS2 import *
except :
    print('smaract SCU driver doesnt work')

try:
    from ESP302 import ESP302
except :
    print('ESP driver doesnt work')

# from PololuTic_motor_class import TicMotor 
import classes.error_class as ER
from myconstants import c
import pandas as pd
from Hardware.Nconfig import *
import copy

class Motor():
    def __init__(self,search=True):
        if search:
            self.search()
        self.encodered=False
        self.motor=None
        self.configLoaded=False
        
        self.load_config()
        self.position_correction=0
        self.config_parameters={'vendor' : float('nan'),
                                 'SN' : float('nan'),
                                 'position' : float('nan'),
                                 'home position' : float('nan'),
                                 'units': float('nan'),
                                 'limit min': float('nan'),
                                 'limit max': float('nan'),
                                 'com': float('nan'),
                                 'NexusID': float('nan'),
                                 'userID': '',
                                 'left name': 'left',
                                 'right name': 'right'}
        
    def load_config(self):
        """load config file"""
        if not self.configLoaded:
            #if not loaded yet
            try:
                data=pd.read_json('motor_config.json')
                self.config=data.to_dict('index')
                print(self.config)
                self.configLoaded=True
                
            except FileNotFoundError:
                print('no config file found')
                self.config={}
            
    def save_config(self,NexusID=float('nan'),UserID='',Update_Existing=True):
        """save config file
        Update_Existing is the option to rewrite or not"""
        if len(self.config)>0:
            Keys, IDs=NexusIDs(self.config)
            # print(Keys,IDs)
            if not np.isnan(NexusID) or not np.isnan(self.config_parameters['NexusID']):
                if np.isnan(NexusID):
                    NexusID=self.config_parameters['NexusID']
                if NexusID in IDs:
                    # print(NexusID,IDs)
                    # print(np.argwhere(np.array(IDs) == NexusID))
                    N0=np.argwhere(np.array(IDs) == NexusID)[0][0]
                    K=Keys[N0]
                else:
                    NexusID=int(max(IDs)+1)
                    K=int(max(Keys)+1)
            else:
                NexusID=int(max(IDs)+1)
                K=int(max(Keys)+1)
        else:
            if np.isnan(NexusID):
                NexusID=0
            K=0
        
        # print("NexusID ", NexusID)
        # print(K)
        
        self.config_parameters['units']=self.motor.units
        self.config_parameters['position']=self.position
        self.config_parameters['vendor']=self.Type
        self.config_parameters['SN']=self.motor.SN
        self.config_parameters['NexusID']=NexusID
        if not UserID=='':
            self.config_parameters['userID']=UserID
        
        self.config[K]=self.config_parameters.copy()
        data=pd.DataFrame.from_dict(self.config,orient='index')
        data.to_json('motor_config.json')
        
    def search(self):
        """search for all motors connected to the computer
        
        Works with: Zaber; Thorlabs (Kinesis); SmarAct SCU
        + a motor emulator
        
        for SmarAct SCU works only with one motor """
        self.motorlist=[]
        try:
            TM=ThorMotor(Autoconnect=False)
            self.TM=TM
            self.motorlist+=[['Thorlabs',m[0]] for m in TM.motorlist]
        except Exception as error:
            print('Thorlabs doenst work')
            print(error)
            self.TM=None
        try:
            ZM=ZaberMotor(Autoconnect=False)
            self.ZM=ZM
            self.motorlist += [['Zaber',m] for m in ZM.motorlist]
        except Exception as error:
            print('Zaber doenst work')
            print(error)
            self.ZM=None
        
        try:
            SAM_SCU=SCU()
            self.SAM_SCU=SAM_SCU
            if SAM_SCU.Nmotors>0:
                self.motorlist += [['SmarAct_SCU',0]]
        except Exception as error:
            print('SmarAct_SCU doenst work')
            print(error)
            self.SAM_SCU=None
            
        try:
            SAM_MCS=MCS()
            self.SAM_MCS=SAM_MCS
            if SAM_MCS.Nmotors>0:
                self.motorlist += [['SmarAct_MCS2',m[4] +' ' + m[2]+' ' + m[3]] for m in SAM_MCS.motorlist]
        except Exception as error:
            print('SmarAct_MCS2 doenst work')
            print(error)
            self.SAM_MCS=None
            
        try:
            #motorized iris motor
            Tic=TicMotor()
            if len(Tic.motorlist) > 0:
                for i in range(len(Tic.motorlist)):
                    self.motorlist += [['Polulu_Tic',i]]
                self.Tic=Tic
        except Exception as error:
            print('Polulu_Tic doenst work')
            print(error)
            self.Tic=None
        
        self.motorlist += [['Emulator', 1]]
        
        if len(self.motorlist)==1:
            #add a couple of more emulators
            self.motorlist += [['Emulator', 2]]
            self.motorlist += [['Emulator', 3]]
            
        print(self.motorlist)
        
    def connect(self,MotorNumber=0,useconfig=True):
        """connect to a motor from the list of motors"""
        if MotorNumber > len(self.motorlist):
            pass
            #raise error
        else:
            M=self.motorlist[MotorNumber]
            if M[0] == 'Thorlabs':
                self.Type='Thorlabs'
                self.encodered=True
                self.motor=ThorMotor(init=False)
                self.motor.connect(SN=M[1])
                self.SN=M[1]
            elif M[0] == 'Zaber':
                self.Type='Zaber'
                # print('connection')
                self.encodered=True
                self.motor=ZaberMotor(init=False)
                self.motor.connections = self.ZM.connections
                self.motor.connect(ZaberID=M[1])
                # print(M[1])
                self.SN=str(M[1]).split(' ')[3]
            elif M[0] == 'SmarAct_SCU':
                self.Type='SmarAct_SCU'
                self.encodered=True
                self.motor=self.SAM_SCU
                self.motor.connect()
                self.SN=M[1]
                self.motor.SN=self.SN
            elif M[0] == 'Polulu_Tic':
                self.Type='Polulu_Tic'
                self.encodered=False
                self.motor=self.Tic
                self.SN=self.Tic.SN
            elif M[0] == 'Emulator':
                self.Type='Emulator'
                self.motor=Motor_emulator()
                self.SN=M[1]
                self.motor.SN=self.SN
            else:
                print("Error: no motor")
                raise ER.SL_exception('no motor')
                #add raise error
            
            if useconfig:
                #load parameters from the config file
                K=findID(self.config,self.motor.Type,self.motor.SN)
                if K == None:
                    print('no data in the config file for this motor')
                    self.islimits=False
                    self.config_parameters['home position']=0
                    self.config_parameters['limit min']=-10**10
                    self.config_parameters['limit max']=10**10
                    self.config_parameters['userID']=''
                else:
                    Config=self.config[K].copy()
                    self.config_parameters=Config
                    self.islimits=not(np.isnan(self.config_parameters['limit min']) or np.isnan(self.config_parameters['limit max']))
                    pos=Config['position']
                    hposition=Config['home position']
                    # if not np.isnan(pos):
                    #     self.position_correction=pos
                    if not np.isnan(hposition):
                        self.set_home(hposition)
                if np.isnan(self.config_parameters['home position']):
                    self.config_parameters['home position']=0
                    self.config_parameters['limit min']=-10**10
                    self.config_parameters['limit max']=10**10
                    self.config_parameters['userID']=''
            else:
                #use default config
                self.config_parameters['home position']=0
                self.config_parameters['limit min']=-10**10
                self.config_parameters['limit max']=10**10
                self.config_parameters['userID']=''
            
            self.config_parameters['vendor']=self.Type
            self.config_parameters['SN']=self.SN
            # print('home pos in config ',self.config_parameters['home position'])
    
    def limits(self,Min,Max):
        """define motor limits"""
        self.config_parameters['limit min']=Min
        self.config_parameters['limit max']=Max
        self.islimits=True
    
    def moveA(self,X,units='mm'):
        """move to position X"""
        if units != self.motor.units:
            if self.Type in ['Emulator', 'Thorlabs', 'Zaber', 'SmarAct_SCU']:
                if units == 'fs':
                    X=X*10**-15*c*1000 #convert fs to mm
                    self.motor.moveA(X)
                elif units == '2*fs':
                    X=X*10**-15*c*1000/2 #convert fs to mm. double pass
                else:
                    raise ER.SL_exception('wrong units')
            else:
                pass
        
        # print(X,self.position_correction,self.config_parameters['home position'])
        X+=self.position_correction
        # X-=self.config_parameters['home position']
        
        if self.islimits:
            if self.config_parameters['limit min'] <= X <=self.config_parameters['limit max']:
                self.motor.moveA(X)
            else:
                raise ER.SL_exception('out of limits')
        else:
            self.motor.moveA(X)
        
    def moveR(self,dx,units='mm'):
        """move relative"""
        if units != self.motor.units:
            if self.Type in ['Emulator', 'Thorlabs', 'Zaber', 'SmarAct_SCU']:
                if units == 'fs':
                    dx=dx*10**-15*c*1000 #convert fs to mm
                elif units == '2*fs':
                    dx=dx*10**-15*c*1000/2 #convert fs to mm. double pass
                else:
                    raise ER.SL_exception('wrong units')
            else:
                pass
            
        if self.islimits:
            if self.config_parameters['limit min'] <= self.position + dx <=self.config_parameters['limit max']:
                self.motor.moveR(dx)
            else:
                raise ER.SL_exception('out of limits')
        else:
            self.motor.moveR(dx)
            
    def stop(self):
        self.motor.stop()
    
    def move_home(self):
        """move to the home position"""
        self.motor.move_home()
        
    def home(self):
        """home the motor (move to the end switch and set it as the home position)"""
        self.motor.home()
        
    # def ishomed(self):
    #     """return homed status"""
    #     return self.motor.ishomed
    
    # def ismoving(self):
    #     """check if the motor is moving"""
    #     return self.motor.ismoving()
    
    def set_home(self,home=None):
        """set current position as home"""
        if home==None:
            self.motor.set_home(home=self.position)
        else:
            self.motor.set_home(home)
        self.config_parameters['home position'] = self.motor.home_position
        
    def disconnect(self):
        """disconnect motor and free the port"""
        if self.motor==None:
            raise ER.SL_exception('no motor connected')
        else:
            self.motor.disconnect()
    
    def position_units(self,units='mm',correction=0):
        """return postition in units"""
        if units != self.motor.units:
            if self.Type in ['Emulator', 'Thorlabs', 'Zaber', 'SmarAct_SCU']:
                if units == 'fs':
                    C=1/(10**-15*c*1000) #convert mm to fs
                elif units == '2*fs':
                   C=1/(10**-15*c*1000/2) #convert mm to fs. double pass 
                else:
                    C=1
            else:
                C=1
        else:
            C=1
        # print(self.motor.position)
        return (self.motor.position + self.position_correction-correction)*C
        
    @property
    def position(self):
        return self.motor.position + self.position_correction
    
    @property
    def units(self):
        return self.motor.units
    
    @property
    def is_moving(self):
        return self.motor.is_moving
    
    @property
    def is_homed(self):
        return self.motor.homed
    
    @property
    def fs_position(self):
        pos=self.position + self.position_correction
        if self.units == 'mm':
            return pos/100/c*10**15
        elif self.units == 'fs':
            return pos
        elif self.units == '':
            #add all possible units
            pass

#test
# M=Motor()
# M.connect()
# M.set_home()
# M.moveR(2)
# M.limits(-100, 100)
# M.save_config(UserID='emul 1')