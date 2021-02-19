# -*- coding: utf-8 -*-
"""
The driver file to use a camera that uses xiapi
"""
import numpy as np
from ximea import xiapi
from ximea import xidefs
from pynta.model.cameras.base_camera import BaseCamera
from pynta.model.cameras.exceptions import CameraNotFound, WrongCameraState, CameraException
from pint import UnitRegistry
ureg = UnitRegistry
#here add in all of the imports



#impliment all of these functions
class Camera(BaseCamera):
    def __init__(self, camera):
        super().__init__(camera)
        self.cam_num = camera
        self.max_width = 0
        self.max_height = 0
        self.width = None
        self.height = None
        self.mode = None
        self.X = None
        self.Y = None
        self.friendly_name = None
        
        
    def initialize(self):
        """
        Initializes the camera.
        """
        #function checks if camera is attached and opens it if it finds one
        #need to figure out what happens if >2 devices
        self.camera = xiapi.Camera()
        self.image = xiapi.Image()                   
        self.camera.open_device()
        self.max_width = self.camera.get_width_maximum()
        self.max_height = self.camera.get_height_maximum()
        width = self.camera.get_width()
        height = self.camera.get_height()
        offsetX=self.camera.get_offsetX()
        offsetY=self.camera.get_offsetY()
        self.X = (offsetX,offsetX+width)
        self.Y = (offsetY,offsetY+height)
        self.friendly_name = None
        self.camera.set_trigger_source("XI_TRG_SOFTWARE") #sets software trigger

        return True

    def trigger_camera(self):
        """
        Triggers the camera.
        """
        if self.camera.get_acquisition_status == 'XI_ON':
            print("camera already acq")
        else:
            if self.mode == self.MODE_CONTINUOUS:
                #grab images
                self.camera.start_acquisition()
                self.camera.set_trigger_software(1)
                self.camera.get_image(xiapi.Image())
                q=3
                
            elif  self.mode == self.MODE_SINGLE_SHOT:
                #grab an image
                q=2
        print(q)
        
    
    def set_acquisition_mode(self, mode):
        """
        Set the readout mode of the camera: Single or continuous.
        :param int mode: One of self.MODE_CONTINUOUS, self.MODE_SINGLE_SHOT
        :return:
        """
        if mode == self.MODE_CONTINUOUS:
            #find and add way to change acq mode
            self.camera.set_acq_timing_mode("XI_ACQ_TIMING_MODE_FRAME_RATE")
        elif mode == self.MODE_SINGLE_SHOT:
            #do the same for single shot
            self.camera.set_trigger_selector("XI_TRG_SEL_FRAME_START")
            
           
        self.mode = mode

        
        

    def set_exposure(self, exposure):
        """
        Sets the exposure of the camera.
        """
        exposure_magnitude=exposure
        exposure_magnitude.to("usecond")
        
        self.camera.set_exposure(exposure_magnitude.magnitude)
        self.exposure = exposure

    def get_exposure(self):
        """
        Gets the exposure time of the camera.
        """
        self.exposure=self.cam.get_exposure()
        return self.exposure

    def read_camera(self):
        """
        Reads the camera
        """
        if self.camera.get_acquisition_status == "XI_OFF":
            raise WrongCameraState('You need to trigger the camera before reading from it')
        
        if self.mode == self.MODE_SINGLE_SHOT:
            self.camera.xiGetimage(xiapi.Image())
            
        else:
            frames= []
            nframes= self.camera.get_image("acq_nframe")
            if nframes:
                frames=[None]*nframes
                for i in range(nframes):
                    grab = self.camera.get_iamge(xiapi.Image())
                    if grab:
                        frames[i] = grab
            return [i.T for i in frames]  # Transpose to have the correct size            
                                        
                    
                
                        
            
            
            

    def set_ROI(self, X: [int, int], Y: [int, int]):
       
        width = abs(X[1]-X[0])+1
        width = int(width-width%4)
        x_pos = int(X[0]-X[0]%4)
        height = int(abs(Y[1]-Y[0])+1)
        y_pos = int(Y[0]-Y[0]%2)
        if x_pos+width > self.max_width:
            raise CameraException('ROI width bigger than camera area')
        if y_pos+height > self.max_height:
            raise CameraException('ROI height bigger than camera area')

        # First set offset to minimum, to avoid problems when going to a bigger size
        self.clear_ROI()
        self.camera.set_width(width)
        self.camera.set_offsetX(x_pos)
        self.camera.set_height(height)
        self.camera.set_offsetY(y_pos)
        self.X = (x_pos, x_pos+width)
        self.Y = (y_pos, y_pos+width)
        self.width = self.camera.get_width()
        self.height = self.camera.get_height()
        return self.width, self.height

    def clear_ROI(self):
        """ Resets the ROI to the maximum area of the camera"""
        self.camera.set_offsetX(0)
        self.camera.set_offsetY(0)
        self.camera.set_width(self.max_width)
        self.camera.set_height(self.max_height)


    def get_size(self):
        """Returns the size in pixels of the image being acquired. This is useful for checking the ROI settings.
        """
        
        return self.camera.get_width, self.camera.get_height

    def getSerialNumber(self):
        """Returns the serial number of the camera.
        """
        return self.camera.get_device_sn

    def GetCCDWidth(self):
        """
        Returns the CCD width in pixels
        """
        return self.camera.get_width_maximum()

    def GetCCDHeight(self):
        """
        Returns: the CCD height in pixels
        """
        
        return self.camera.get_height_maximum()

    def stopAcq(self):
        """Stops the acquisition without closing the connection to the camera."""
        self.camera.stop_acquisition
        

    def set_binning(self, xbin, ybin):
        """
        Sets the binning of the camera if supported. Has to check if binning in X/Y can be different or not, etc.
        
        :param xbin:
        :param ybin:
        self.camera.set_binning_horizontal(xbin)
        self.camera.set_binning_vertical(ybin)
        :return:
        
        """
        pass

    def clear_binning(self):
        """
        Clears the binning of the camera to its default value.
        """
        self.camera.set_binning_horizontal(1)
        self.camera.set_binning_vertical(1)
        pass

    def stop_camera(self):
        """Stops the acquisition and closes the connection with the camera.
        """
        self.camera.close_device
        
