#!--encoding:utf-8--

import os
import sys
import hashlib
import json
import uuid

import motor
from tornado import web
from tornado import gen
import bson

from settings import MOTOR_DB as DB
from common.init import WiseHandler
from common.decorator import require_login
from common.api import comet_backend

class Physical_Device_Alerts(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    @require_login
    def get(self):
        alerts = []
        cursor = DB.alerts.find({"type": "physical_device"})
        
        while(yield cursor.fetch_next):
            alert = cursor.next_object()
            alerts.append(alert)
        
        alerts.reverse()
        
        # add page id for every client
        page_id = str(uuid.uuid4())
        if not self.get_secure_cookie("page_id", None) :
            self.set_secure_cookie("page_id", page_id)
        
        self.render("system/system_alerts_physical_device.html", alerts=alerts)
    
    @require_login
    @web.asynchronous
    def post(self):
        cursor = self.get_argument("cursor", None)
        if cursor != "null":
            index = 0
            msg_cache = comet_backend.manager.get_nagios_msg_cache()
            for i in xrange(len(msg_cache)):
                index = len(msg_cache) - i - 1
                if msg_cache[index] == cursor:
                    break
            
            recent = msg_cache[index + 1:]
            if len(recent) > 0:
                self.write_data(recent)
        
        # use page id for every client to set the callback
        user_page_id = self.get_secure_cookie("page_id")
        user_md5 = hashlib.md5(user_page_id).hexdigest()
        comet_backend.nagios_waiters[user_md5] = self.on_new_message
    
    def on_new_message(self, message):
        self.write_data(message)
    
    def write_data(self, message):
        if isinstance(message, list):
            self.finish(json.dumps(message))
        else:
            obj_id = message['message_id']
            DB.alerts.find({"_id": bson.ObjectId(obj_id)}).each(self.on_get_data)
    
    def on_get_data(self, data, error):
        if data:
            msg = {
                "message_id": str(data["_id"]),
                "created_time": data["created_time"],
                "message_type": data["message_type"],
                "message": data["message"]
            }
            self.finish(json.dumps([msg]))


class XenServer_Alerts(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    @require_login
    def get(self):
        alerts = []
        cursor = DB.alerts.find({"type": "xenserver"})
        
        while(yield cursor.fetch_next):
            alert = cursor.next_object()
            alerts.append(alert)
            
        alerts.reverse()
        
        # add page id for every client
        page_id = str(uuid.uuid4())
        if not self.get_secure_cookie("page_id", None) :
            self.set_secure_cookie("page_id", page_id)
        
        self.render("system/system_alerts_xenserver.html", alerts=alerts)
    
    @require_login
    @web.asynchronous
    def post(self):
        cursor = self.get_argument("cursor", None)
        if cursor != "null":
            index = 0
            msg_cache = comet_backend.manager.get_xenserver_msg_cache()
            for i in xrange(len(msg_cache)):
                index = len(msg_cache) - i - 1
                if msg_cache[index] == cursor:
                    break
            
            recent = msg_cache[index + 1:]
            if len(recent) > 0:
                self.write_data(recent)
        
        # use page id for every client to set the callback
        user_page_id = self.get_secure_cookie("page_id")
        user_md5 = hashlib.md5(user_page_id).hexdigest()
        comet_backend.xenserver_waiters[user_md5] = self.on_new_message
    
    def on_new_message(self, message):
        self.write_data(message)
    
    def write_data(self, message):
        if isinstance(message, list):
            self.finish(json.dumps(message))
        else:
            obj_id = message['message_id']
            DB.alerts.find({"_id": bson.ObjectId(obj_id)}).each(self.on_get_data)
    
    def on_get_data(self, data, error):
        if data:
            msg = {
                "message_id": str(data["_id"]),
                "created_time": data["created_time"],
                "message_type": data["message_type"],
                "message": data["message"]
            }
            self.finish(json.dumps([msg]))


class CloudStack_Alerts(WiseHandler):
    @require_login
    def get(self):
        pass
    
