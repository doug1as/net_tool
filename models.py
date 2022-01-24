#!/usr/bin/env python

#from enum import unique
#from routes import index
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(140), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    #
    is_admin = db.Column(db.Boolean, index=True, unique=False, default=False)
    is_engineer = db.Column(db.Boolean, index=True, unique=False, default=False)
    is_read_only = db.Column(db.Boolean, index=True, unique=False, default=True)
    #
    send_email = db.Column(db.Boolean, index=True, unique=False, default=False)
    whatsapp_message = db.Column(db.Boolean, index=True, unique=False, default=False)
    #
    joined_at_date = db.Column(db.DateTime(), index=True, default=datetime.now())

    def __repr__(self):
        return '<User: {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class NetworkDevice(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #
    #
    hostname = db.Column(db.String(30), index=True, unique=True)
    hardware_model = db.Column(db.String(30), index=True, unique=False, default='N/A')
    serial_number = db.Column(db.String(30), index=True, unique=False, default='N/A')
    vendor = db.Column(db.String(30), index=True, unique=False)
    firmware_version = db.Column(db.String(50), index=True, unique=False, default='N/A')
    management_ip = db.Column(db.String(15), index=True, unique=True)
    network_side = db.Column(db.String(30), index=True, unique=False)
    device_type = db.Column(db.String(30), index=True, unique=False)
    #
    last_check = db.Column(db.Boolean, index=True, unique=False, default=False)
    last_check_date = db.Column(db.DateTime(), index=True, default=datetime.now())
    inserted_at_date = db.Column(db.DateTime(), index=True, default=datetime.now())
    #
    #####
    interfaces = db.relationship('DeviceInterfacesType', backref='deviceinterfacestype', lazy='dynamic', cascade = 'all, delete, delete-orphan')
    interfaces = db.relationship('DeviceInterfacesTraffic', backref='deviceinterfacestraffic', lazy='dynamic', cascade = 'all, delete, delete-orphan')

    def __repr__(self):
        return '<Network Device: {}>'.format(self.hostname)


class DeviceInterfacesType(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #
    #####
    network_device_id = db.Column(db.Integer, db.ForeignKey('network_device.id'))
    #####    
    #
    ports_10gb = db.Column(db.Integer, index=True, unique=False, default=0)
    ports_100gb = db.Column(db.Integer, index=True, unique=False, default=0)
    #
    total_ports_10_100gb = db.Column(db.Integer, index=True, unique=False, default=0)
    #    
    oper_status_1gb = db.Column(db.Integer, index=True, unique=False, default=0)
    oper_status_10gb = db.Column(db.Integer, index=True, unique=False, default=0)
    oper_status_100gb = db.Column(db.Integer, index=True, unique=False, default=0)
    #    
    ports_10gb_free = db.Column(db.Integer, index=True, unique=False, default=0)
    ports_100gb_free = db.Column(db.Integer, index=True, unique=False, default=0)
    #
    ports_in_use = db.Column(db.Integer, index=True, unique=False, default=0)
    ports_down = db.Column(db.Integer, index=True, unique=False, default=0)
    ports_admin_down = db.Column(db.Integer, index=True, unique=False, default=0)
    #
    ports_capacity_10gb = db.Column(db.Integer, index=True, unique=False, default=0)
    ports_capacity_100gb = db.Column(db.Integer, index=True, unique=False, default=0)
    ports_capacity_total = db.Column(db.Integer, index=True, unique=False, default=0)
    #
    last_check = db.Column(db.Boolean, index=True, unique=False, default=False)
    last_check_date = db.Column(db.DateTime(), index=True, default=datetime.now())

    def __repr__(self):
        return '<Device Interfaces For NetworkDevice ID: {}>'.format(self.network_device_id)   


class DeviceInterfacesTraffic(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #
    #####
    network_device_id = db.Column(db.Integer, db.ForeignKey('network_device.id'))
    #####
    #
    interface = db.Column(db.String(50), index=True, unique=False)
    traffic_in = db.Column(db.String(10), index=True, unique=False, default=0)
    traffic_out = db.Column(db.String(10), index=True, unique=False, default=0)
    description = db.Column(db.String(100), index=True, unique=False, default="NO DESCRIPTION FOUND !")
    #
    last_check = db.Column(db.Boolean, index=True, unique=False, default=False)
    last_check_date = db.Column(db.DateTime(), index=True, default=datetime.now())    

    def __repr__(self):
        return '<Interfaces Traffic For NetworkDevice ID: {}>'.format(self.network_device_id)    