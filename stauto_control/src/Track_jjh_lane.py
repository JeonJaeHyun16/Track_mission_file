#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# @Author  : Luo Yao
# @Modified  : AdamShan
# @Original site    : https://github.com/MaybeShewill-CV/lanenet-lane-detection
# @File    : lanenet_node.py


import cv2
import numpy as np
import roslib
import sys
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import Image
from nav_msgs.msg import Path
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Pose
from ackermann_msgs.msg import AckermannDriveStamped
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import math
import time
import sys
import os.path
import rospkg
from darknet_ros_msgs.msg import BoundingBoxes
from std_msgs.msg import Int32MultiArray
from std_msgs.msg import Int16MultiArray
from std_msgs.msg import MultiArrayLayout
from geometry_msgs.msg import Point , PoseStamped

def draw_lines(img, lines, color=[255, 0, 0], thickness=3):
        line_img = np.zeros((img.shape[0],img.shape[1],3),dtype=np.uint8)
        img = np.copy(img)
        if lines is None:
            return

        for line in lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_img, (x1, y1), (x2, y2), color, thickness)

        img = cv2.addWeighted(img, 0.8, line_img, 1.0, 0.0)

        return img


class Track_lanenet_detector():

    def __init__(self):
        # tf.enable_eager_execution()
        print("init")
        self.image_topic = "/darknet_ros/detection_image"
        self.output_image ="/lane_images"
        self.boundingboxes_topic = "/darknet_ros/bounding_boxes"
        self.bridge = CvBridge()
        sub_image = rospy.Subscriber(self.image_topic, Image, self.img_callback, queue_size=1)
        sub_boundingBoxes = rospy.Subscriber(self.boundingboxes_topic, BoundingBoxes, self.BoundingBoxes_callback)
        self.pub_image = rospy.Publisher(self.output_image, Image, queue_size=1)
        self.pub_ist_image = rospy.Publisher(self.output_image, Image, queue_size=1)
        self.Blue_x_cen,self.Blue_y_cen = [],[] 
        self.Yello_x_cen,self.Yello_y_cen = [],[] 

    def BoundingBoxes_callback(self, data):
        BoundingBoxes = []
        for i in range(len(data.bounding_boxes)):
            cone_xmin = data.bounding_boxes[i].xmin
            cone_ymin = data.bounding_boxes[i].ymin #ymin
            cone_xmax = data.bounding_boxes[i].xmax #xmax
            cone_ymax = data.bounding_boxes[i].ymax #ymax
            cone_class = data.bounding_boxes[i].Class
            cone_y_center = (cone_ymax+cone_ymin)/2
            cone_x_center = (cone_xmax+cone_xmin)/2
            BoundingBoxes.append([cone_xmin,cone_ymin,cone_xmax,cone_ymax,cone_x_center,cone_y_center,cone_class])
        Blue_informations,Yello_informations = self.Cone_information(BoundingBoxes)
        self.Blue_x_cen,self.Blue_y_cen = self.make_x_y_pixel(Blue_informations)
        self.Yello_x_cen,self.Yello_y_cen = self.make_x_y_pixel(Yello_informations)
        
    
    def img_callback(self, data):
        t1 = time.time()
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            print(e)
        Blue_x_cen = self.Blue_x_cen
        Blue_y_cen = self.Blue_y_cen
        Yello_x_cen = self.Yello_x_cen
        Yello_y_cen = self.Yello_y_cen
        Blue_x_cen,Blue_y_cen = sort_x_y_pixel(Blue_x_cen,Blue_y_cen)
        Yello_x_cen,Yello_y_cen = sort_x_y_pixel(Yello_x_cen,Yello_y_cen)
        
      

        original_img = cv_image.copy()
        h,w,c = original_img.shape
        empty_img = np.zeros((h,w,c),np.uint8())
        
        
        for i in range ((len(Blue_x_cen))-1):
            empty_img = draw_lines(empty_img,
                [[
                [int(Blue_x_cen[i]), int(Blue_y_cen[i]), int(Blue_x_cen[i+1]), int(Blue_y_cen[i+1])],
                ]],
                [0,0,255],
                3)
        for i in range ((len(Yello_x_cen))-1):
            empty_img = draw_lines(empty_img,
                [[
                [int(Yello_x_cen[i]), int(Yello_y_cen[i]), int(Yello_x_cen[i+1]), int(Yello_y_cen[i+1])],
                ]],
                [0,0,255],
                3)
        empty_img2 = cv2.resize(empty_img, (640, 480), interpolation=cv2.INTER_LINEAR)
        out_img_msg = self.bridge.cv2_to_imgmsg(empty_img2, "8UC3")
        self.pub_image.publish(out_img_msg)
        print(1/(time.time() - t1)) 
        

    

    def Cone_information(self,data):
    #print(data) 
        Blue_informations = []
        Yello_informations = []
        Blue_information = []
        Yello_information = []
        for i in range(len(data)):
            Class=data[i][6]
            #print(Class)
            if (Class =='blue'):
                [blue_cone_xmin,blue_cone_ymin,blue_cone_xmax,blue_cone_ymax,blue_cone_x_center,blue_cone_y_center,blue_class] = data[i][0:7]
                Blue_information = [blue_cone_xmin,blue_cone_ymin,blue_cone_xmax,blue_cone_ymax,blue_cone_x_center ,blue_cone_y_center,blue_class]
                Blue_informations.append(Blue_information)
                
            elif (Class=='yellow'):
                
                [yello_cone_xmin,yello_cone_ymin,yello_cone_xmax,yello_cone_ymax,yello_cone_x_center,yello_cone_y_center,yellow_class] = data[i][0:7]
                Yello_information = [yello_cone_xmin,yello_cone_ymin,yello_cone_xmax,yello_cone_ymax,yello_cone_x_center,yello_cone_y_center,yellow_class]
                Yello_informations.append(Yello_information)
            
        
        #print(Blue_informations,Yello_informations)
        return Blue_informations,Yello_informations
        data.clear()

    def make_x_y_pixel(self, data):
        x_cens = []
        y_cens = []
        for i in range(len(data)):
            x_cen = data[i][4]
            y_cen = data[i][5]
            x_cens.append(x_cen)
            y_cens.append(y_cen)
        #print(x_cens,y_cens)
        return x_cens,y_cens


    def sort_x_y_pixel(self,x_cord,y_cord):
        cordination = []
        for elem_x,elem_y in zip(x_cord,y_cord):
            cordination.append([elem_x,elem_y])
        cordination = sorted(cordination, key = lambda x: x[0])
        x = [i[0] for i in cordination]
        y = [i[1] for i in cordination]
        return x,y

if __name__ == '__main__':
    # init args
    rospy.init_node('TracK_lanenet_node')
    Track_lanenet_detector()
    rospy.spin()
