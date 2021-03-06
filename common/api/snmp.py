#!/usr/bin/env python
#!--encoding:utf-8--

from pysnmp.smi import builder, view, error
from pysnmp.entity.rfc3413.oneliner import cmdgen

from logger import logger


def get_all_interface(host, community):
    """
    获取某主机上的所有端口
    """
    all_interfaces = []
    gen = cmdgen.CommandGenerator()
    
    if_descr_oid = cmdgen.MibVariable('IF-MIB', 'ifDescr')
    
    # 获取所有的端口描述
    error_indication, error_status, error_index, var_binds = gen.nextCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((host, 161)),
        if_descr_oid,
    )
    
    interface = None
    if not error_indication:
        for var in var_binds:
            for i in var:
                temp = {}
                key = i[0].asTuple()
                value = i[1]
                temp['index'] = key[-1]
                temp['name'] = str(value)
                all_interfaces.append(temp)

    if_status_oid = cmdgen.MibVariable('IF-MIB', 'ifOperStatus')
    
    # 获取所有的端口状态
    error_indication, error_status, error_index, var_binds = gen.nextCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((host, 161)),
        if_status_oid,
    )
    
    all_interfaces_status = {}
    if not error_indication:
        for var in var_binds:
            for i in var:
                key = i[0].asTuple()
                value = i[1]
                all_interfaces_status[key[-1]] = int(value)
    
    for interface in all_interfaces:
        if interface['index'] in all_interfaces_status:
            interface['status'] = all_interfaces_status[interface['index']]
    
    return all_interfaces


def get_int_status(host, community, interface_name=None, interface_index=None):
    """
    根据端口名称或端口index获取端口的速度和状态
    """
    gen = cmdgen.CommandGenerator()
    
    if interface_name and not interface_index:
        if_descr_oid = cmdgen.MibVariable('IF-MIB', 'ifDescr')
        
        error_indication, error_status, error_index, var_binds = gen.nextCmd(
            cmdgen.CommunityData(community),
            cmdgen.UdpTransportTarget((host, 161)),
            if_descr_oid,
        )
        
        interface = None
        if not error_indication:
            for var in var_binds:
                for i in var:
                    key = i[0]
                    value = i[1]
                    if value == interface_name:
                        interface = key
                        break
                    
        if not interface:
            logger.error("can not get interface for [%s %s %s]" % (host, community, interface_index))
            return None
        
        interface_oid_tuple = interface.asTuple()
        interface_index = interface_oid_tuple[-1]
    
    if interface_index and not interface_name:
        if_descr_oid = cmdgen.MibVariable('IF-MIB', 'ifDescr', interface_index)
        
        error_indication, error_status, error_index, var_binds = gen.getCmd(
            cmdgen.CommunityData(community),
            cmdgen.UdpTransportTarget((host, 161)),
            if_descr_oid,
        )
        interface_name = None
        if not error_indication:
            for var in var_binds:
                    interface_name = var[1]
    
    if_oid_speed = cmdgen.MibVariable('IF-MIB', 'ifSpeed', interface_index)
    if_oid_status = cmdgen.MibVariable('IF-MIB', 'ifOperStatus', interface_index)
    
    error_indication, error_status, error_index, var_binds = gen.getCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((host, 161)),
        if_oid_speed,
    )
    speed = None
    if not error_indication:
        for var in var_binds:
                speed = var[1]

    if not speed:
        logger.error("can not get speed for [%s %s %s]" % (host, community, interface_index))
        return None
    
    error_indication, error_status, error_index, var_binds = gen.getCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((host, 161)),
        if_oid_status,
    )
    status = None
    if not error_indication:
        for var in var_binds:
                status = var[1]

    if not status:
        logger.error("can not get status for [%s %s %s]" % (host, community, interface_index))
        return None
    
    return speed, status, interface_name, interface_index

    
if __name__ == '__main__':
    print get_all_interface("192.2.3.237", "111spsp111")
    print get_int_status("192.2.3.237", "111spsp111", interface_name="GigabitEthernet1/0/37")
    print get_int_status("192.2.3.237", "111spsp111", interface_index=10137)
