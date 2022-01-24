#!/usr/bin/env python

import time
import sys
from datetime import datetime
from app import app, login_manager, db
from flask import render_template, flash, redirect, url_for
from forms import LoginForm, ChangePassword, RegistrationForm, AddElement, UpdateElement, MassiveUpdateElement
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import asc, desc  # distinct
from models import User, NetworkDevice, DeviceInterfacesType, DeviceInterfacesTraffic
from mylibs.toolbox import NetworkElement
from mylibs import color


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # check if current_user logged in, if so redirect to a page that makes sense
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password !')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login_2.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:  # check if current_user logged in, if so redirect to a page that makes sense
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        email = User.query.filter_by(email=form.email.data).first()
        if user or email:
            flash('Username or email already in use, try again or sign in !')
            return render_template('register.html', form=form)
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('register'))
    return render_template('register_2.html', form=form)


@app.route('/')
@login_required
def index():
    caches = NetworkDevice.query.all()
    interfaces_type = DeviceInterfacesType.query.all()
    models = []
    versions = []
    total_ports = 0
    total_ports_in_use = 0
    total_ports_down = 0
    total_ports_admin_down = 0
    total_oper_status_1gb = 0
    total_oper_status_10gb = 0
    total_oper_status_100gb = 0
    total_caches_environment = 0
    hosts_capacity_sorted = DeviceInterfacesType.query.order_by(desc('ports_capacity_total')).limit(3).all()
    hosts_capacity = {}
    for host in hosts_capacity_sorted:
        hosts_capacity[NetworkDevice.query.get(host.network_device_id).hostname] = host.ports_capacity_total
    for cache in caches:
        total_caches_environment += 1
        for port in interfaces_type:
            if cache.id == port.network_device_id:
                total_ports += port.total_ports_10_100gb
                total_ports_in_use += port.ports_in_use
                total_ports_down += port.ports_down
                total_ports_admin_down += port.ports_admin_down
                total_oper_status_1gb += port.oper_status_1gb
                total_oper_status_10gb += port.oper_status_10gb
                total_oper_status_100gb += port.oper_status_100gb
            else:
                continue        
        if cache.hardware_model not in models:
            if cache.hardware_model != 'N/A':
                models.append(cache.hardware_model)
                models.sort()
        if cache.firmware_version not in versions:
            if cache.firmware_version != 'N/A':
                versions.append(cache.firmware_version)
                versions.sort()
        # if cache.ports_capacity_total > 75:
        #    if len(hosts_capacity) < 3:
        #        hosts_capacity[cache.hostname] = cache.ports_capacity_total
        #        hosts_capacity_sorted = sorted(hosts_capacity.items(), key=lambda x: x[1], reverse=True)

    return render_template(
        'index.html',
        template_user=current_user,
        template_model=models,
        template_firmware=versions,
        template_total_ports=total_ports,
        template_total_ports_in_use=total_ports_in_use,
        template_total_ports_down=total_ports_down,
        template_total_ports_admin_down=total_ports_admin_down,
        template_total_oper_status_1gb=total_oper_status_1gb,
        template_total_oper_status_10gb=total_oper_status_10gb,
        template_total_oper_status_100gb=total_oper_status_100gb,
        template_total_caches_environment=total_caches_environment,
        template_capacity=hosts_capacity,
    )


@app.route('/cache_register', methods=['GET', 'POST'])
@login_required
def cache_register():
    form = AddElement()
    if form.validate_on_submit():
        # Validating Form
        if 'Select' in form.vendor.data and 'Select' in form.net_side.data:
            flash('You need to select Vendor and Network Side !')
            return redirect(url_for('cache_register'))
        elif 'Select' in form.vendor.data:
            flash('You need to select Vendor correctly !')
            return redirect(url_for('cache_register'))
        elif 'Select' in form.net_side.data:
            flash('You need to select Network Side !')
            return redirect(url_for('cache_register'))

        # Retrieving Form Data Fields
        hostname = form.hostname.data.upper()
        management_ip = form.management_ip.data
        vendor = form.vendor.data
        net_side = form.net_side.data
        tacacs_user = form.tacacs_user.data
        tacacs_pass = form.tacacs_pass.data

        hostname_check = NetworkDevice.query.filter_by(hostname=hostname).first()
        management_ip_check = NetworkDevice.query.filter_by(management_ip=management_ip).first()
        if hostname_check or management_ip_check:
            flash('Hostname or Management IP Already Exist, Please Verify !')
            return redirect(url_for('cache_register'))

        # Device Dict For Later Connection
        device = {
            'device_type': '',
            'host': hostname,
            'username': tacacs_user,
            'password': tacacs_pass,
            'ssh_config_file': ''
        }

        # Populating device_type
        if vendor.upper() == 'CISCO NEXUS':
            device['device_type'] = 'cisco_nxos'
        elif vendor.upper() == 'BROCADE':
            device['device_type'] = 'brocade_nos'
        elif vendor.upper() == 'HP':
            device['device_type'] = 'hp_comware'

        # Populating ssh_config_file
        if net_side == 'Vivo I':
            device['ssh_config_file'] = 'vivo1'
        else:
            device['ssh_config_file'] = 'vivo2'


        try:
            # Instantiate Objects From Class For Retrieve Information
            host = NetworkElement(device)
            interfaces = host.check_qtde_interfaces_slots()
            interfaces_status = host.check_status_ports()
            interfaces_total = host.check_qtde_total_interfaces()

            ##########
            # Object From Models Tables NetworkDevice(network_device table)
            network_device = NetworkDevice()

            # Populating Database Table NetworkDevice(network_device) Params
            network_device.hostname = hostname.upper()
            network_device.hardware_model = host.check_hardware_model()['1']
            network_device.serial_number = host.check_serial_number()
            network_device.vendor = vendor.split()[0].upper()
            network_device.firmware_version = host.check_firmware_version()
            network_device.management_ip = management_ip
            network_device.network_side = net_side
            network_device.device_type = host.connection.device_type
            network_device.last_check = True
            #last_check_date = db.Column(db.DateTime(), index=True, default=datetime.now())
            #inserted_at_date = db.Column(db.DateTime(), index=True, default=datetime.now())            

            # Add device in database for network_device table, commit in ELSE block (try/except/else)
            db.session.add(network_device)       
            ##########

            ##########
            # Object From Models Tables DeviceInterfacesType (device_interfaces_type table)
            device_interfaces_type = DeviceInterfacesType()            
            # Object From Models Tables (network_device for catch id, id of network_device is foreign key of device_interfaces_type)
            hostname_for_id = NetworkDevice.query.filter_by(hostname=hostname.upper()).first()         

            # Populating Database Table DeviceInterfacesType(device_interfaces_type) Params
            device_interfaces_type.network_device_id = hostname_for_id.id
            device_interfaces_type.total_ports_10_100gb = interfaces_total
            # Initializing Variables For 'NoneType' To 'int'
            device_interfaces_type.ports_10gb = 0
            device_interfaces_type.ports_100gb = 0
            device_interfaces_type.ports_10gb_free = 0
            device_interfaces_type.ports_100gb_free = 0

            if len(interfaces['qtde_interfaces_10']) > 0:
                for value in interfaces['qtde_interfaces_10'].values():
                    device_interfaces_type.ports_10gb += value

            if len(interfaces['qtde_interfaces_100']) > 0:
                for value in interfaces['qtde_interfaces_100'].values():
                    device_interfaces_type.ports_100gb += value

            # Free Ports Section

            if interfaces_status['ports_10gb_free'] > 0:
                device_interfaces_type.ports_10gb_free += interfaces_status['ports_10gb_free']

            if interfaces_status['ports_100gb_free'] > 0:
                device_interfaces_type.ports_100gb_free += interfaces_status['ports_100gb_free']

            ###
            device_interfaces_type.ports_in_use = interfaces_status['ports_in_use']
            device_interfaces_type.ports_down = interfaces_status['ports_down']
            device_interfaces_type.ports_admin_down = interfaces_status['ports_admin_down']
            device_interfaces_type.oper_status_1gb = interfaces_status['oper_status_1gb']
            device_interfaces_type.oper_status_10gb = interfaces_status['oper_status_10gb']
            device_interfaces_type.oper_status_100gb = interfaces_status['oper_status_100gb']

            # Calculating ports capacity, total, 10GB and 100GB
            # Capacity Total
            capacity = (interfaces_status['ports_in_use'] / interfaces_total) * 100
            capacity = float("{:.2f}".format(capacity))

            # Capacity 10GB
            capacity_10gb = 0
            try:

                if device_interfaces_type.ports_10gb > 0:
                    capacity_10gb = (
                        (
                            device_interfaces_type.oper_status_10gb + device_interfaces_type.oper_status_1gb) / device_interfaces_type.ports_10gb
                        ) * 100
                else:
                    capacity_10gb = 100

                capacity_10gb = float("{:.2f}".format(capacity_10gb))

            except Exception as e:
                capacity_10gb = 'Exception'
                print('\n{}'.format(
                    '*****--------------------<<<<<<<<<< BEGIN >>>>>>>>>>--------------------*****')
                )
                print(
                    type(e).__name__,  # Type of Error
                    __file__,  # File Path
                    e.__traceback__.tb_lineno  # Line Error
                )
                print('{}'.format(
                    '*****--------------------<<<<<<<<<< *END* >>>>>>>>>>--------------------*****\n')
                )
            
            # Capacity 100GB
            capacity_100gb = 0
            try:
                if network_device.vendor == 'BROCADE':
                    if '6940' in network_device.hardware_model:
                        capacity_100gb = (device_interfaces_type.oper_status_100gb / 4) * 100
                    else: # 6740 hasn't 100GB interfaces, your capacity is fulfilled with 100%
                        capacity_100gb = 100

                elif network_device.vendor == 'CISCO':
                    if device_interfaces_type.ports_100gb > 0:
                        capacity_100gb = (device_interfaces_type.oper_status_100gb / device_interfaces_type.ports_100gb) * 100
                    else:
                        capacity_100gb = 100

                elif network_device.vendor == 'HP':                    
                        capacity_100gb = 100            

                capacity_100gb = float("{:.2f}".format(capacity_100gb))

            except Exception as e:
                capacity_100gb = 'Exception'
                print('\n{}'.format(
                    '*****--------------------<<<<<<<<<< BEGIN >>>>>>>>>>--------------------*****')
                )
                print(
                    type(e).__name__,  # Type of Error
                    __file__,  # File Path
                    e.__traceback__.tb_lineno  # Line Error
                )
                print('{}'.format(
                    '*****--------------------<<<<<<<<<< *END* >>>>>>>>>>--------------------*****\n')
                )

            device_interfaces_type.ports_capacity_10gb = capacity_10gb
            device_interfaces_type.ports_capacity_100gb = capacity_100gb
            device_interfaces_type.ports_capacity_total = capacity
            device_interfaces_type.last_check = True
            # last_check_date = db.Column(db.DateTime(), index=True, default=datetime.now())
            # network_device.inserted_at_date = db.Column(db.DateTime(), index=True, default=datetime.utcnow)

            # Add device in database for network_device table, commit in ELSE block (try/except/else)
            # db.session.add_all((network_device, device_interfaces_type))
            db.session.add(device_interfaces_type)
            ##########

            ##########
            # Object From Models Tables (network_device for catch id, id of network_device is foreign key of interface_traffic)
            hostname_for_id = NetworkDevice.query.filter_by(hostname=hostname.upper()).first()

            # Objects From Class NetworkElement For Retrieve Information
            interfaces_traffic = host.check_interface_traffic()

            # Populating Database Params
            for interface, traffic in interfaces_traffic.items():
                # Object From Models Tables (interfaces_traffic table)
                # Needs to be instanciate each every loop
                interface_traffic = DeviceInterfacesTraffic()
                interface_traffic.network_device_id = hostname_for_id.id
                interface_traffic.interface = interface
                interface_traffic.traffic_in = traffic[0]
                interface_traffic.traffic_out = traffic[1]
                interface_traffic.description = traffic[2]
                interface_traffic.last_check = True
                db.session.add(interface_traffic)   
                # db.session.add_all([interface_traffic])   
            ##########

        except Exception as e:

            # Rollback previous actions database
            db.session.rollback()

            # Object From Models Tables (network_device table)
            network_device = NetworkDevice()

            # Populating Database Params
            network_device.hostname = hostname.upper()
            #hardware_model = db.Column(db.String(30), index=True, unique=False, default='N/A')
            #serial_number = db.Column(db.String(30), index=True, unique=False, default='N/A')            
            network_device.vendor = vendor.split()[0].upper()
            #firmware_version = db.Column(db.String(50), index=True, unique=False, default='N/A')
            network_device.management_ip = management_ip
            network_device.network_side = net_side
            #last_check_date = db.Column(db.DateTime(), index=True, default=datetime.now())
            #inserted_at_date = db.Column(db.DateTime(), index=True, default=datetime.now())

            # Add device in database for network_device table, commit in ELSE block (try/except/else)
            db.session.add(network_device)

            ##########
            # Object From Models Tables DeviceInterfacesType (device_interfaces_type table)
            device_interfaces_type = DeviceInterfacesType()            
            # Object From Models Tables (network_device for catch id, id of network_device is foreign key of device_interfaces_type)
            hostname_for_id = NetworkDevice.query.filter_by(hostname=hostname.upper()).first() 

            # Populating Database Table device_interfaces_type Params
            device_interfaces_type.network_device_id = hostname_for_id.id
            device_interfaces_type.ports_10gb = 0
            device_interfaces_type.ports_100gb = 0   
            device_interfaces_type.total_ports_10_100gb = 0               
            device_interfaces_type.oper_status_1gb = 0
            device_interfaces_type.oper_status_10gb = 0
            device_interfaces_type.oper_status_100gb = 0 
            device_interfaces_type.ports_10gb_free = 0
            device_interfaces_type.ports_100gb_free = 0               
            device_interfaces_type.ports_in_use = 0
            device_interfaces_type.ports_down = 0               
            device_interfaces_type.ports_admin_down = 0           
            device_interfaces_type.ports_capacity_10gb = 100
            device_interfaces_type.ports_capacity_100gb = 100
            device_interfaces_type.ports_capacity_total = 100
            device_interfaces_type.last_check = False
            device_interfaces_type.last_check_date = datetime.now()

            # Add device in database for device_interfaces_type table, commit in ELSE block (try/except/else)
            db.session.add(device_interfaces_type)

            # Commit previous actions on database
            db.session.commit()

            print('\n{}'.format(
                str(color.prRed('*****--------------------<<<<<<<<<< BEGIN >>>>>>>>>>--------------------*****')))
            )
            print("Oops!", sys.exc_info()[0], " in ", hostname.upper(), "occurred.")
            for erro in sys.exc_info():
                print(erro)
            print(
                type(e).__name__,  # Type of Error
                __file__,  # File Path
                e.__traceback__.tb_lineno  # Line Error
            )
            print('{}'.format(
                str(color.prRed('*****--------------------<<<<<<<<<< *END* >>>>>>>>>>--------------------*****\n')))
            )

            # For indicate error en exceution
            # return redirect(url_for('about'))

        else:

            # Commit previous actions on database
            db.session.commit()
            
            # For clear form after submit
            return redirect(url_for('cache_register'))     
              
    # Default return statement
    return render_template('cache_register.html', form=form)


@app.route('/cache_update_register', methods=['GET', 'POST'])
@login_required
def cache_update_register():
    form = UpdateElement()

    if form.validate_on_submit():

        # Validating Form
        if not form.hostname.data:
            flash('You need to select at least one Hostname !')
            return redirect(url_for('cache_update_register'))

        ##########
        # Retrieving Database Cache From UpdateElement Form
        # form.hostname.data.hostname in filter because QuerySelectField return the object of NetworkDevice
        network_device = NetworkDevice.query.filter_by(hostname=form.hostname.data.hostname).first()

        ##########
        # Object From Models Tables DeviceInterfacesType (device_interfaces_type table)
        device_interfaces_type = DeviceInterfacesType.query.filter_by(network_device_id=network_device.id).first()                           
        ###
        
        # Retrieving Form Data Fields
        hostname = network_device.hostname
        net_side = network_device.network_side
        tacacs_user = form.tacacs_user.data
        tacacs_pass = form.tacacs_pass.data

        # Device Dict For Later Connection
        device = {
            'device_type': network_device.device_type,
            'host': hostname,
            'username': tacacs_user,
            'password': tacacs_pass,
            'ssh_config_file': ''
        }

        # Populating ssh_config_file
        if net_side == 'Vivo I':
            device['ssh_config_file'] = 'vivo1'
        else:
            device['ssh_config_file'] = 'vivo2'


        try:
            # Instantiate Objects From Class For Retrieve Information
            host = NetworkElement(device)
            interfaces = host.check_qtde_interfaces_slots()
            interfaces_status = host.check_status_ports()
            interfaces_total = host.check_qtde_total_interfaces()

            # Populating Database Table NetworkDevice(network_device) Params            
            network_device.hardware_model = host.check_hardware_model()['1']
            network_device.serial_number = host.check_serial_number()
            network_device.firmware_version = host.check_firmware_version()
            network_device.network_side = net_side
            network_device.device_type = host.connection.device_type
            network_device.last_check = True            
            network_device.last_check_date = datetime.now()

            # Add device in database for network_device table, commit in ELSE block (try/except/else)
            db.session.add(network_device)       
            ##########


            ##########
            # Object From Models Tables DeviceInterfacesType (device_interfaces_type table)
            device_interfaces_type = DeviceInterfacesType.query.filter_by(network_device_id=network_device.id).first()                           
            ###

            # Populating Database Table DeviceInterfacesType(device_interfaces_type) Params
            device_interfaces_type.total_ports_10_100gb = interfaces_total
            # Initializing Variables For 'NoneType' To 'int', and actual value to be 0 + interfaces['xxx']
            device_interfaces_type.ports_10gb = 0
            device_interfaces_type.ports_100gb = 0
            device_interfaces_type.ports_10gb_free = 0
            device_interfaces_type.ports_100gb_free = 0

            if len(interfaces['qtde_interfaces_10']) > 0:
                for value in interfaces['qtde_interfaces_10'].values():
                    device_interfaces_type.ports_10gb += value

            if len(interfaces['qtde_interfaces_100']) > 0:
                for value in interfaces['qtde_interfaces_100'].values():
                    device_interfaces_type.ports_100gb += value

            # Free Ports Section

            if interfaces_status['ports_10gb_free'] > 0:
                device_interfaces_type.ports_10gb_free += interfaces_status['ports_10gb_free']

            if interfaces_status['ports_100gb_free'] > 0:
                device_interfaces_type.ports_100gb_free += interfaces_status['ports_100gb_free']

            ###
            device_interfaces_type.ports_in_use = interfaces_status['ports_in_use']
            device_interfaces_type.ports_down = interfaces_status['ports_down']
            device_interfaces_type.ports_admin_down = interfaces_status['ports_admin_down']      
            device_interfaces_type.oper_status_1gb = interfaces_status['oper_status_1gb']
            device_interfaces_type.oper_status_10gb = interfaces_status['oper_status_10gb']
            device_interfaces_type.oper_status_100gb = interfaces_status['oper_status_100gb']
            ###

            # Calculating ports capacity, total, 10GB and 100GB
            # Capacity Total
            capacity = (interfaces_status['ports_in_use'] / interfaces_total) * 100
            capacity = float("{:.2f}".format(capacity))

            # Capacity 10GB
            capacity_10gb = 0
            try:
                if device_interfaces_type.ports_10gb > 0:
                    capacity_10gb = (
                        (
                            device_interfaces_type.oper_status_10gb + device_interfaces_type.oper_status_1gb
                        ) / device_interfaces_type.ports_10gb) * 100
                else:
                    capacity_10gb = 100

                capacity_10gb = float("{:.2f}".format(capacity_10gb))

            except Exception as e:
                capacity_10gb = 'Exception'
                print('\n{}'.format(
                    '*****--------------------<<<<<<<<<< BEGIN >>>>>>>>>>--------------------*****')
                )
                print(
                    type(e).__name__,  # Type of Error
                    __file__,  # File Path
                    e.__traceback__.tb_lineno  # Line Error
                )
                print('{}'.format(
                    '*****--------------------<<<<<<<<<< *END* >>>>>>>>>>--------------------*****\n')
                )
            # Capacity 100GB
            capacity_100gb = 0
            try:
                if network_device.vendor == 'BROCADE':
                    if '6940' in network_device.hardware_model:
                        capacity_100gb = (device_interfaces_type.oper_status_100gb / 4) * 100
                    else:  # 6740 hasn't 100GB interfaces, your capacity is fulfilled with 100%
                        capacity_100gb = 100

                else:
                    if device_interfaces_type.ports_100gb > 0:
                        capacity_100gb = (device_interfaces_type.oper_status_100gb / device_interfaces_type.ports_100gb) * 100
                    else:
                        capacity_100gb = 100

                capacity_100gb = float("{:.2f}".format(capacity_100gb))

            except Exception as e:
                capacity_100gb = 'Exception'
                print('\n{}'.format(
                    '*****--------------------<<<<<<<<<< BEGIN >>>>>>>>>>--------------------*****')
                )
                print(
                    type(e).__name__,  # Type of Error
                    __file__,  # File Path
                    e.__traceback__.tb_lineno  # Line Error
                )
                print('{}'.format(
                    '*****--------------------<<<<<<<<<< *END* >>>>>>>>>>--------------------*****\n')
                )

            device_interfaces_type.ports_capacity_10gb = capacity_10gb
            device_interfaces_type.ports_capacity_100gb = capacity_100gb
            device_interfaces_type.ports_capacity_total = capacity
            device_interfaces_type.last_check = True
            device_interfaces_type.last_check_date = datetime.now()
            # network_device.inserted_at_date = db.Column(db.DateTime(), index=True, default=datetime.utcnow)

            # Add device in database for network_device table, commit in ELSE block (try/except/else)
            # db.session.add_all((network_device, device_interfaces_type))
            db.session.add(device_interfaces_type)
            ##########

            ######
            # Object From Models Tables (network_device for catch id, id of network_device is foreign key of device_interfaces_traffic)
            device_interfaces_traffic = DeviceInterfacesTraffic.query.filter_by(network_device_id=network_device.id).all()      
            interface_traffic_to_create_check = []
            for port in device_interfaces_traffic:
                interface_traffic_to_create_check.append(port.interface)      
            # db.session.delete(InterfaceTraffic.query.filter_by(network_device_id=cache_to_update.id).all())
            # db.session.delete(Reader.query.get(753))

            # Objects From Class NetworkElement For Retrieve Information
            traffic_on_interfaces = host.check_interface_traffic()

            # Updating Database Params
            for port in device_interfaces_traffic:

                # Update if exists in database, device_interfaces_traffic (port.interface)
                # and exists in new collect on traffic_on_interfaces
                if port.interface in traffic_on_interfaces.keys():
                    port.network_device_id = network_device.id
                    # port.interface = traffic_on_interfaces[port.interface]
                    port.traffic_in = traffic_on_interfaces[port.interface][0]
                    port.traffic_out = traffic_on_interfaces[port.interface][1]
                    port.description = traffic_on_interfaces[port.interface][2]
                    port.last_check = True       
                    port.last_check_date = datetime.now()             
                    db.session.add(port)   

                # Delete if exists in database, device_interfaces_traffic (port.interface)
                # and no exists in new collect on traffic_on_interfaces
                elif port.interface not in traffic_on_interfaces.keys():   
                    db.session.delete(DeviceInterfacesTraffic.query.filter_by(
                        network_device_id=network_device.id, 
                        interface=port.interface
                        ).first()
                    )

                # Create if not exists in database, device_interfaces_traffic (port.interface)
                # and exists in new collect on traffic_on_interfaces                        
                else:                                        

                    # Populating Database Params
                    for interface, traffic in traffic_on_interfaces.items():
                        if interface not in interface_traffic_to_create_check:
                            # Object From Models Tables (interface_traffic table)
                            # Needs to be instanciate each every loop
                            interface_traffic = DeviceInterfacesTraffic()
                            interface_traffic.network_device_id = network_device.id
                            interface_traffic.interface = interface
                            interface_traffic.traffic_in = traffic[0]
                            interface_traffic.traffic_out = traffic[1]
                            interface_traffic.description = traffic[2]
                            interface_traffic.last_check = True
                            interface_traffic.last_check_date = datetime.now() 
                            db.session.add(interface_traffic)
                            # db.session.add_all([interface_traffic])   
                            #   
                        else:
                            continue                   

        except Exception as e:


            # Rollback previous actions database
            db.session.rollback()

            # Populating Database Params
            network_device.last_check = False
            network_device.last_check_date = datetime.now()            

            # Add device in database for network_device table, commit in ELSE block (try/except/else)
            db.session.add(network_device)

            # Populating Database Table device_interfaces_type Params
            device_interfaces_type.last_check = False
            device_interfaces_type.last_check_date = datetime.now()

            # Add device in database for device_interfaces_type table, commit in ELSE block (try/except/else)
            db.session.add(device_interfaces_type)

            # Commit previous actions on database
            db.session.commit()

            print('\n{}'.format(
                str(color.prRed('*****--------------------<<<<<<<<<< BEGIN >>>>>>>>>>--------------------*****')))
            )
            print("Oops!", sys.exc_info()[0], " in ", hostname.upper(), "occurred.")
            for erro in sys.exc_info():
                print(erro)
            print(
                type(e).__name__,  # Type of Error
                __file__,  # File Path
                e.__traceback__.tb_lineno  # Line Error
            )
            print('{}'.format(
                str(color.prRed('*****--------------------<<<<<<<<<< *END* >>>>>>>>>>--------------------*****\n')))
            )

            # For indicate error en exceution
            # return redirect(url_for('about'))

        else:

            # Commit previous actions on database
            db.session.commit()
            
            # For clear form after submit
            return redirect(url_for('cache_update_register'))

        # For clear form after submit
        return redirect(url_for('cache_update_register'))

    # Default return statement
    return render_template(
        'cache_update_register.html',
        form=form
    )


@app.route('/cache_update_massive', methods=['GET', 'POST'])
@login_required
def cache_update_massive():
    form = MassiveUpdateElement()

    if form.validate_on_submit():

        # Retrieving Database Cache From UpdateElement Form
        # form.hostname.data.hostname in filter because QuerySelectField return the object of NetworkDevice
        caches_to_update = NetworkDevice.query.all()

        # Looping Trough Database
        for network_device in caches_to_update:

            # Retrieving Form Data Fields
            hostname = network_device.hostname
            net_side = network_device.network_side
            tacacs_user = form.tacacs_user.data
            tacacs_pass = form.tacacs_pass.data

            # Device Dict For Later Connection
            device = {
                'device_type': network_device.device_type,
                'host': hostname,
                'username': tacacs_user,
                'password': tacacs_pass,
                'ssh_config_file': ''
            }

            # Populating ssh_config_file
            if net_side == 'Vivo I':
                device['ssh_config_file'] = 'vivo1'
            else:
                device['ssh_config_file'] = 'vivo2'


            try:

                # Instantiate Objects From Class For Retrieve Information
                host = NetworkElement(device)
                interfaces = host.check_qtde_interfaces_slots()
                interfaces_status = host.check_status_ports()
                interfaces_total = host.check_qtde_total_interfaces()

                # Populating Database Table NetworkDevice(network_device) Params            
                network_device.hardware_model = host.check_hardware_model()['1']
                network_device.serial_number = host.check_serial_number()
                network_device.firmware_version = host.check_firmware_version()
                network_device.network_side = net_side
                network_device.device_type = host.connection.device_type
                network_device.last_check = True            
                network_device.last_check_date = datetime.now()

                # Add device in database for network_device table, commit in ELSE block (try/except/else)
                db.session.add(network_device)       
                ##########


                ##########
                # Object From Models Tables DeviceInterfacesType (device_interfaces_type table)
                device_interfaces_type = DeviceInterfacesType.query.filter_by(network_device_id=network_device.id).first()                           
                ###

                # Populating Database Table DeviceInterfacesType(device_interfaces_type) Params
                device_interfaces_type.total_ports_10_100gb = interfaces_total
                # Initializing Variables For 'NoneType' To 'int', and actual value to be 0 + interfaces['xxx']
                device_interfaces_type.ports_10gb = 0
                device_interfaces_type.ports_100gb = 0
                device_interfaces_type.ports_10gb_free = 0
                device_interfaces_type.ports_100gb_free = 0

                if len(interfaces['qtde_interfaces_10']) > 0:
                    for value in interfaces['qtde_interfaces_10'].values():
                        device_interfaces_type.ports_10gb += value

                if len(interfaces['qtde_interfaces_100']) > 0:
                    for value in interfaces['qtde_interfaces_100'].values():
                        device_interfaces_type.ports_100gb += value

                # Free Ports Section

                if interfaces_status['ports_10gb_free'] > 0:
                    device_interfaces_type.ports_10gb_free += interfaces_status['ports_10gb_free']

                if interfaces_status['ports_100gb_free'] > 0:
                    device_interfaces_type.ports_100gb_free += interfaces_status['ports_100gb_free']

                ###
                device_interfaces_type.ports_in_use = interfaces_status['ports_in_use']
                device_interfaces_type.ports_down = interfaces_status['ports_down']
                device_interfaces_type.ports_admin_down = interfaces_status['ports_admin_down']      
                device_interfaces_type.oper_status_1gb = interfaces_status['oper_status_1gb']
                device_interfaces_type.oper_status_10gb = interfaces_status['oper_status_10gb']
                device_interfaces_type.oper_status_100gb = interfaces_status['oper_status_100gb']
                ###

                # Calculating ports capacity, total, 10GB and 100GB
                # Capacity Total
                capacity = (interfaces_status['ports_in_use'] / interfaces_total) * 100
                capacity = float("{:.2f}".format(capacity))

                # Capacity 10GB
                capacity_10gb = 0
                try:
                    if device_interfaces_type.ports_10gb > 0:
                        capacity_10gb = (
                            (
                                device_interfaces_type.oper_status_10gb + device_interfaces_type.oper_status_1gb
                            ) / device_interfaces_type.ports_10gb) * 100
                    else:
                        capacity_10gb = 100

                    capacity_10gb = float("{:.2f}".format(capacity_10gb))

                except Exception as e:
                    capacity_10gb = 'Exception'
                    print('\n{}'.format(
                        '*****--------------------<<<<<<<<<< BEGIN >>>>>>>>>>--------------------*****')
                    )
                    print(
                        type(e).__name__,  # Type of Error
                        __file__,  # File Path
                        e.__traceback__.tb_lineno  # Line Error
                    )
                    print('{}'.format(
                        '*****--------------------<<<<<<<<<< *END* >>>>>>>>>>--------------------*****\n')
                    )
                # Capacity 100GB
                capacity_100gb = 0
                try:
                    if network_device.vendor == 'BROCADE':
                        if '6940' in network_device.hardware_model:
                            capacity_100gb = (device_interfaces_type.oper_status_100gb / 4) * 100
                        else:  # 6740 hasn't 100GB interfaces, your capacity is fulfilled with 100%
                            capacity_100gb = 100

                    else:
                        if device_interfaces_type.ports_100gb > 0:
                            capacity_100gb = (device_interfaces_type.oper_status_100gb / device_interfaces_type.ports_100gb) * 100
                        else:
                            capacity_100gb = 100

                    capacity_100gb = float("{:.2f}".format(capacity_100gb))

                except Exception as e:
                    capacity_100gb = 'Exception'
                    print('\n{}'.format(
                        '*****--------------------<<<<<<<<<< BEGIN >>>>>>>>>>--------------------*****')
                    )
                    print(
                        type(e).__name__,  # Type of Error
                        __file__,  # File Path
                        e.__traceback__.tb_lineno  # Line Error
                    )
                    print('{}'.format(
                        '*****--------------------<<<<<<<<<< *END* >>>>>>>>>>--------------------*****\n')
                    )

                device_interfaces_type.ports_capacity_10gb = capacity_10gb
                device_interfaces_type.ports_capacity_100gb = capacity_100gb
                device_interfaces_type.ports_capacity_total = capacity
                device_interfaces_type.last_check = True
                device_interfaces_type.last_check_date = datetime.now()
                # network_device.inserted_at_date = db.Column(db.DateTime(), index=True, default=datetime.utcnow)

                # Add device in database for network_device table, commit in ELSE block (try/except/else)
                # db.session.add_all((network_device, device_interfaces_type))
                db.session.add(device_interfaces_type)
                ##########

                ######
                # Object From Models Tables (network_device for catch id, id of network_device is foreign key of device_interfaces_traffic)
                device_interfaces_traffic = DeviceInterfacesTraffic.query.filter_by(network_device_id=network_device.id).all()      
                interface_traffic_to_create_check = []
                for port in device_interfaces_traffic:
                    interface_traffic_to_create_check.append(port.interface)      
                # db.session.delete(InterfaceTraffic.query.filter_by(network_device_id=cache_to_update.id).all())
                # db.session.delete(Reader.query.get(753))

                # Objects From Class NetworkElement For Retrieve Information
                traffic_on_interfaces = host.check_interface_traffic()

                # Updating Database Params
                for port in device_interfaces_traffic:

                    # Update if exists in database, device_interfaces_traffic (port.interface)
                    # and exists in new collect on traffic_on_interfaces
                    if port.interface in traffic_on_interfaces.keys():
                        port.network_device_id = network_device.id
                        # port.interface = traffic_on_interfaces[port.interface]
                        port.traffic_in = traffic_on_interfaces[port.interface][0]
                        port.traffic_out = traffic_on_interfaces[port.interface][1]
                        port.description = traffic_on_interfaces[port.interface][2]
                        port.last_check = True       
                        port.last_check_date = datetime.now()             
                        db.session.add(port)   

                    # Delete if exists in database, device_interfaces_traffic (port.interface)
                    # and no exists in new collect on traffic_on_interfaces
                    elif port.interface not in traffic_on_interfaces.keys():   
                        db.session.delete(DeviceInterfacesTraffic.query.filter_by(
                            network_device_id=network_device.id, 
                            interface=port.interface
                            ).first()
                        )

                    # Create if not exists in database, device_interfaces_traffic (port.interface)
                    # and exists in new collect on traffic_on_interfaces                        
                    else:                                        

                        # Populating Database Params
                        for interface, traffic in traffic_on_interfaces.items():
                            if interface not in interface_traffic_to_create_check:
                                # Object From Models Tables (interface_traffic table)
                                # Needs to be instanciate each every loop
                                interface_traffic = DeviceInterfacesTraffic()
                                interface_traffic.network_device_id = network_device.id
                                interface_traffic.interface = interface
                                interface_traffic.traffic_in = traffic[0]
                                interface_traffic.traffic_out = traffic[1]
                                interface_traffic.description = traffic[2]
                                interface_traffic.last_check = True
                                interface_traffic.last_check_date = datetime.now() 
                                db.session.add(interface_traffic)
                                # db.session.add_all([interface_traffic])   
                                #   
                            else:
                                continue                    

            except Exception as e:

                # Rollback previous actions database
                db.session.rollback()

                # Populating Database Table network_device Params
                network_device.last_check = False
                network_device.last_check_date = datetime.now()
                
                # Add device in database for network_device table, commit in ELSE block (try/except/else)
                db.session.add(network_device)

                # Populating Database Table device_interfaces_type Params
                device_interfaces_type.last_check = False
                device_interfaces_type.last_check_date = datetime.now()

                # Add device in database for device_interfaces_type table, commit in ELSE block (try/except/else)
                db.session.add(device_interfaces_type)

                # Commit previous actions on database
                db.session.commit()


                print('\n{}'.format(
                    str(color.prRed('*****--------------------<<<<<<<<<< BEGIN >>>>>>>>>>--------------------*****')))
                )
                print("Oops!", sys.exc_info()[0], " in ", hostname.upper(), "occurred.")
                for erro in sys.exc_info():
                    print(erro)
                print(
                    type(e).__name__,  # Type of Error
                    __file__,  # File Path
                    e.__traceback__.tb_lineno  # Line Error
                )
                print('{}'.format(
                    str(color.prRed('*****--------------------<<<<<<<<<< *END* >>>>>>>>>>--------------------*****\n')))
                )

                # For indicate error en exceution
                # return redirect(url_for('about'))

            else:

                # Commit previous actions on database
                db.session.commit()
                
        # For clear form after submit
        return redirect(url_for('cache_update_massive'))

    # Default return statement
    return render_template(
        'cache_update_massive.html',
        form=form,
    )


@app.route('/caches_list')
@login_required
def caches_list():

    # Fetching all caches from database
    network_devices = NetworkDevice.query.order_by(desc('hostname')).all()
    device_interfaces_type = DeviceInterfacesType.query.all()

    # Return/render network_devices, device_interfaces_type
    return render_template(
        'caches_list.html',
        template_network_device=network_devices,
        template_device_interfaces_type=device_interfaces_type,
    )


@app.route('/caches_ports_occupation')
@login_required
def caches_ports_occupation():

    # Fetching all caches from database
    network_devices = NetworkDevice.query.order_by(asc('hostname')).all()
    device_interfaces_type = DeviceInterfacesType.query.all()

    # Return/render network_devices, device_interfaces_type
    return render_template(
        'caches_ports_occupation.html',
        template_network_devices=network_devices,
        template_device_interfaces_type=device_interfaces_type,
    )


@app.route('/caches_ports_traffic')
@login_required
def caches_ports_traffic():

    # Fetching all caches from database
    caches = NetworkDevice.query.order_by(asc('hostname')).all()
    interfaces = DeviceInterfacesTraffic.query.all()

    # Return/render caches_ports_occupation
    return render_template(
        'caches_ports_traffic.html',
        template_caches=caches,
        template_interfaces=interfaces,
    )


@app.route('/hardware_specs')
@login_required
def hardware_specs():

    # Fetching all caches from database
    caches_unique_models = NetworkDevice.query.with_entities(NetworkDevice.hardware_model).distinct().all()

    # Return/render caches_ports_occupation
    return render_template(
        'hardware_specs.html',
        template_caches_unique_models=caches_unique_models,
    )


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePassword()
    user = User.query.filter_by(username=current_user.username).first()
    if form.validate_on_submit():
        if not user.check_password(form.password.data):
            flash("Actual password don't match !")
            return redirect(url_for('change_password'))
        if form.new_password.data != form.confirm_new_password.data:
            flash("New and confirm password fields doesn't match !")
            return redirect(url_for('change_password'))
        user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password successfully changed !')
        time.sleep(3)
        return redirect(url_for('profile'))
    return render_template(
        'change_password.html',
        template_profile=current_user,
        form=form
    )


@app.route('/profile')
@login_required
def profile():
    return render_template(
        'profile.html',
        template_profile=current_user
    )


@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', error=error), 404


# Add a decorator here to handle unauthorized users:
@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


@app.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    form = AddElement()
    if form.validate_on_submit():
        hostname = form.hostname.data
        management_ip = form.management_ip.data
        vendor = form.vendor.data
        net_side = form.net_side.data
        return render_template(
            'test.html',
            form=form,
            hostname=hostname,
            management_ip=management_ip,
            vendor=vendor,
            net_side=net_side
        )
    return render_template('test.html', form=form)
