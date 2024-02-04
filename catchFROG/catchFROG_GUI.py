"""


@author: Slawa

"""
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import pyqtgraph as pg
import pandas as pd
import numpy as np
import time


import os
import sys
Path=os.path.dirname((os.path.abspath(__file__)))
sys.path.append(Path)

SP=Path.split("\\")
Pypath='\\'.join(SP[:-1])
sys.path.append(Pypath)

import error_class as ER
from color_maps.color_maps import ImageColorMap
from myconstants import c

from Motors.MotorGUI import MotorGUI

from spectrometer.SpectrometerGUI import SpecGUI

from catchFROG_class import catchFROG

class FROG_GUI(QMainWindow):
    def __init__(self):
        self.app=QApplication(sys.argv)
        super(FROG_GUI, self).__init__()
        uic.loadUi(Path+"\\Qt\\catch_FROG.ui", self)
        self.show()
        
        self.SpecGUI=SpecGUI(show=False)
        self.motor=MotorGUI(show=False)
        self.SpecGUI.show()
        self.motor.show()
        
        self.TakeStart.clicked.connect(self.getStart)
        self.TakeStop.clicked.connect(self.getStop)
        self.startBt.clicked.connect(self.start)
        self.saveBt.clicked.connect(self.save)
        
        self.ScaleVerBt.clicked.connect(self.scaleV)
        self.ScaleHorBt.clicked.connect(self.scaleH)
        
        self.ShowSpectrometer.clicked.connect(self.SpecGUI.show)
        self.ShowMotor.clicked.connect(self.motor.show)
        
        self.definerange.clicked.connect(self.show_slice)
        self.LamMax.valueChanged.connect(self.show_slice)
        self.LamMin.valueChanged.connect(self.show_slice)
        self.Xscale.currentTextChanged.connect(self.Display)
        
        
        """prepare the 2d plot"""
        View=self.plot2d
        S=View.size()
        scene = QGraphicsScene(self)
        
        win = pg.GraphicsLayoutWidget()
        p1 = win.addPlot(labels={'bottom': ('delay fs'),'left': ('wavelength nm')})
        img = pg.ImageItem()
        p1.addItem(img)
        img.setImage(np.ones((2600,2000)))
        
        img.setColorMap(ImageColorMap('Wh_rainbow',512))
        
        bar = pg.ColorBarItem(
        values = (0, 1000),
        colorMap=ImageColorMap('Wh_rainbow',512),
        orientation = 'v'
        )
        bar.setImageItem( img, insert_in=p1 )
        
        self.pgImg=img
        self.pgplot=p1
        self.imgbar=bar
        self.pgwin=win
        self.scene=scene
        
        win.resize(S*0.99)
        scene.addWidget(win)
        View.setScene(scene)
        
        """prepare the 1d plot"""
        View2=self.plot1d
        S2=View2.size()
        scene2 = QGraphicsScene(self)
        
        plot = pg.PlotWidget()
        plot.getAxis('bottom').setLabel(text='delay fs', font_weight='bold')
        plot.getAxis('left').setLabel(text='intensity a.u.', font_weight='bold')
        plot.showGrid(x=True, y=True, alpha=0.7)
        plot.resize(S2*0.99)
        scene2.addWidget(plot)
        View2.setScene(scene2)
        
        self.plot=plot
        self.scene1d=scene2
        
        """set display timer"""
        self.Dtimer = QtCore.QTimer(self)
        self.Dtimer.setInterval(200) #.2 seconds
        self.Dtimer.timeout.connect(self.Display)
        self.Dtimer.start()
        
        self.frog=catchFROG()
    
    def Display(self):
        """update the plots"""
        if len(self.frog.S)>0 and len(self.frog.T)>0:
            #2d plot
            # print(self.frog.S)
            X=np.array(self.frog.T)
            Y=np.array(self.frog.lam)
            Z=np.array(self.frog.S)
            # print(Z.shape)
            if self.Xscale.currentText() == 'ps':
                X*=10**-3
                self.pgplot.getAxis('bottom').setLabel(text='delay ps', font_weight='bold')
            elif self.Xscale.currentText() == 'mm':
                X = X*10**-15*c*10**3
                self.pgplot.getAxis('bottom').setLabel(text='delay mm', font_weight='bold')
            else:
                self.pgplot.getAxis('bottom').setLabel(text='delay fs', font_weight='bold')
            
            self.pgImg.setImage(Z)
            self.pgImg.setRect(X.min(), Y.min(), X.max()-X.min(), Y.max()-Y.min())
            
            if not self.ScaleVerBt.isChecked():
                self.pgplot.setYRange(self.SetYmin.value(), self.SetYmax.value())
            else:
                self.pgplot.setYRange(Y.min(),Y.max())
                self.SetYmin.setValue(Y.min())
                self.SetYmax.setValue(Y.max())
                
            if not self.ScaleHorBt.isChecked():
                self.pgplot.setXRange(self.SetXmin.value(),self.SetXmax.value())
            else:
                self.pgplot.setXRange(X.min(),X.max())
                self.SetXmin.setValue(X.min())
                self.SetXmax.setValue(X.max())
            
            S=self.plot2d.size()
            self.pgwin.resize(S*0.99)
            
            self.show_slice()
                
                
    def show_slice(self):
        """show the integrated slice of the scan"""
        plot = self.plot
        plot.clear()
        
        if self.definerange.isChecked():
            Slice_min=self.LamMin.value()
            Slice_max=self.LamMax.value()
        else:
            Slice_min=self.frog.lam.min()
            Slice_max=self.frog.lam.max()
        self.frog.take_slice([Slice_min,Slice_max])
        X=np.array(self.frog.T)
        Y=np.array(self.frog.slice)
        
        if self.Xscale.currentText() == 'ps':
            X*=10**3
            self.pgplot.getAxis('bottom').setLabel(text='delay ps', font_weight='bold')
        elif self.Xscale.currentText() == 'mm':
            X = X*10**-15*c*10**3
            self.pgplot.getAxis('bottom').setLabel(text='delay mm', font_weight='bold')
        else:
            self.pgplot.getAxis('bottom').setLabel(text='delay fs', font_weight='bold')
        
        
        plot.plot(X,Y, pen=pg.mkPen((0,0,255), width=2.5))
        
        if not self.ScaleHorBt.isChecked():
            plot.setXRange(self.SetXmin.value(),self.SetXmax.value())
        else:
            plot.setXRange(X.min(),X.max())
            self.SetXmin.setValue(X.min())
            self.SetXmax.setValue(X.max())
            
        self.plot.resize(self.plot1d.size()*0.99)
    
    def start(self):
        """start scan"""
        #read scan parameters
        if not self.motor.connected or not self.SpecGUI.connected:
            self.startBt.setChecked(False)
            if not self.motor.connected:
                self.showstatus('no motor connected')
            if not self.SpecGUI.connected:
                self.showstatus('no spectromenter connected')
        else:
            if self.startBt.isChecked():
                # print('start')
                try:
                    self.Pstart=self.ScanStart.value()
                    self.Pstop=self.ScanStop.value()
                    self.Pstep=self.ScanStep.value()
                    self.fast=self.ScanMode.isChecked()
                    # print('fast', self.fast)
                    
                    if self.Pstep == 0:
                        raise ER.SL_exception('step must be non zero')
                    if self.Pstop > self.Pstart and self.Pstep < 0:
                        raise ER.SL_exception('wrong step sign')
                    if self.Pstop < self.Pstart and self.Pstep > 0:
                        raise ER.SL_exception('wrong step sign')
                except ER.SL_exception as error:
                    self.showerror(error)
                    
                else:
                    if self.Pstop > self.Pstart:
                        self.positivscan=True
                    else:
                        self.positivscan=False
                        
                    #prepare
                    self.frog.clear_delays()
                    if self.SpecGUI.startBt.isChecked():
                        #stop the spectrometer
                        self.SpecGUI.startBt.setChecked(False)
                    self.frog.spec_calibration(self.SpecGUI.spectrometer.lam)
                    # print(self.SpecGUI.spectrometer.lam)
                    if self.LamMax.value() == 0:
                        self.LamMax.setValue(self.SpecGUI.spectrometer.lam.max())
                        self.LamMin.setValue(self.SpecGUI.spectrometer.lam.min())
                        
                    if self.motor.getPosition() != self.Pstart:
                        #move motor to the start position
                        self.motor.moveA(self.Pstart-2*self.Pstep)
                        # self.motor.moveA(self.Pstart)
                    
                    Nsteps=int(np.abs(self.Pstart-self.Pstop)/self.Pstep)
                    Step=0
                    Pos=np.linspace(self.Pstart,self.Pstop,Nsteps+1)
                    # print(Pos)
                    while (Step < Nsteps+1) and self.startBt.isChecked():
                        # print('step',Step)
                        #move motor
                        self.motor.moveA(Pos[Step])
                        if not self.fast:
                            # print('slow mode')
                            while self.motor.motor.is_moving:
                                self.app.processEvents()
                                time.sleep(0.1)
                        #get spectrum
                        self.SpecGUI.sampling=True
                        self.SpecGUI.startBt.setChecked(True)
                        self.SpecGUI.getspectrum()
                        self.SpecGUI.startBt.setChecked(False)
                        self.SpecGUI.sampling=False
                        # self.SpecGUI.ShowPlot()
                        if self.SpecGUI.SubstractBkg:
                            S=self.SpecGUI.spec-self.SpecGUI.bkg
                        else:
                            S=self.SpecGUI.spec
                        T=self.motor.Position_fs() #takes into account double pass in a delay stage
                        self.frog.add_delay(T,S)
                        
                        Step+=1
                        
                        
                    #finilizing
                    self.Display()
                    self.startBt.setChecked(False)
            else:
                print('stop')
    
    def showerror(self,error):
        self.error_message.setPlaceholderText(error.Message)
        
    def showstatus(self,message):
        self.error_message.setPlaceholderText(message)
    
    def getStart(self):
        self.ScanStart.setValue(self.motor.getPosition())
        
    def getStop(self):
        self.ScanStop.setValue(self.motor.getPosition())
    
    def scaleV(self):
        """change the vertical scaling behaiviour (fixed or adjusting)"""
        self.AutoScaleV=self.ScaleVerBt.isChecked()
    
    def scaleH(self):
        """change the vertical scaling behaiviour (fixed or adjusting)"""
        self.AutoScaleH=self.ScaleHorBt.isChecked()
        
    def save(self):
        """save scan result"""
        print(self.frog.S.shape)
        self.frog.save()
        
    def closeEvent(self, event):
        """call at closing"""
        try:
            self.motor.motor.disconnect()
        except:
            pass
        
        self.motor.hide()
        
        try: 
            self.SpecGUI.spectrometer.disconnect()
        except:
            pass
        
        self.SpecGUI.hide()
        
if __name__ == '__main__':
    pg.setConfigOption('background', 'w')
    app = QApplication([])
    window = FROG_GUI()

    app.exec_()