"""
FROG acquisition class

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
from tkinter import filedialog
from classes.width import width

class catchFROG():
    def __init__(self):
        self.T=[] #delay data
        self.S=[] #spectral data
        self.lam=None #spectral calibration data
        self.delayUnits='fs'
        self.lamUnits='nm'
        self.slice=None
    
    def add_delay(self,delay,spec):
        if len(self.T) == 0:
            self.T=np.array([delay])
            self.S=np.array([spec])
        else:
            self.T = np.append(self.T,delay)
            self.S = np.append(self.S,[spec],axis=0)
        # print(self.T.shape, self.S.shape)
        
    def clear_delays(self):
        self.T=[]
        self.S=[]
        
    def spec_calibration(self,lam):
        self.lam=lam.copy()
        
    def units(self,delay='fs',lam='nm'):
        """define units"""
        self.delayUnits=delay
        self.lamUnits=lam
        
    def save(self,file=None):
        """save the frog data"""
        if file==None:
            file = filedialog.asksaveasfilename()
        if file != '':
            filename=file+'.pyfrog'
            T=np.array(self.T)
            lam=np.array(self.lam)
            # print(self.S.shape)
            np.savetxt(filename,T.reshape((1,-1)),delimiter='\t',comments='')
            with open(filename, "a") as f:
                np.savetxt(f, lam.reshape((1,-1)),delimiter='\t',comments='')
                np.savetxt(f, self.S,delimiter='\t',comments='')
                
    def take_slice(self,LamRange=[],normalize=True):
        """convert 2D data into 1D by integration over the LamRange=[LamMin,LamMax]
        normalize is the option to normalize the slice to maximum of 1"""
        if len(LamRange)<2:
            Nmin=0
            Nmax=len(self.lam)
        else:
            LamMin=LamRange[0]
            LamMax=LamRange[1]
            if LamMin>LamMax:
                LamMin, LamMax = [LamMax, LamMin]
        Nmin=np.argwhere(self.lam >= LamMin)[0][0]
        if self.lam.max() <= LamMax:
            Nmax=-1
        else:
            Nmax=np.argwhere(self.lam <= LamMax)[-1][0]
        
        Slice=np.sum(self.S[:,Nmin:Nmax],axis=1)
        
        self.slice=Slice
        return Slice
    
    def width(self,method='FWHM'):
        """widnt of the slice"""
        if not self.slice==None:
            W=width(self.T,self.Slice,method=method)
            self.width=W
            return W
    
    
    
    
    
    
    
    
    
    
    
    