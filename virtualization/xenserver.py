# --encoding: utf-8--
from run import global_xenserver_conn
from logger import logger
from pprint import pprint
from common.api import XenAPI


def get_control_domain(host):
    """
    得到XenServer主机的控制域VM
    @host: XenServer主机
    """
    session = global_xenserver_conn.get(host, None)
    if session != None:
        all_vm = session.xenapi.VM.get_all()
        for vm_ref in all_vm:
            record = session.xenapi.VM.get_record(vm_ref)
            if record['is_control_domain']:
                return vm_ref


def get_vm_info_by_uuid(host, vm_uuid):
    """
    得到单台VM的详细
    @host: XenServer主机
    @vm_uuid: VM的UUID
    """
    for ip, session in global_xenserver_conn.items():
        if ip == host:
            vms = session.xenapi.VM.get_all()
            for vm in vms:
                record = session.xenapi.VM.get_record(vm)
                if not record['is_a_template'] and not record['is_control_domain']:
                    if record['uuid'] == vm_uuid:
                        return record


def get_vm_info(host, vm_ref):
    """
    得到单台VM的简略信息
    @host: XenServer主机
    @vm_ref: VM的reference
    """
    vm_info = {}
    session = global_xenserver_conn.get(host, None)
    if session != None:
        vm_record = session.xenapi.VM.get_record("OpaqueRef:" + vm_ref)
        vm_info['name_label'] = vm_record['name_label']
        vm_info['power_state'] = vm_record['power_state']
        return vm_info


def get_host_info(session, host_record, verbose=True):
    '''
    得到单台xenserver的信息
    @session: 连接到xenserver的session
    @host_record: 每条xenserver的记录
    @verbose: 是否启用详细模式
    '''
    temp_record = {}
    record = session.xenapi.host.get_record(host_record)
    if verbose:
        control_domain_vm_ref = get_control_domain(record['address']).split(":")[1]
        temp_record['control_domain_vm_ref'] = control_domain_vm_ref
    temp_record['uuid'] = record['uuid']
    temp_record['hostname'] = record['hostname']
    temp_record['address'] = record['address']
    temp_record['cpu_count'] = record['cpu_info']['cpu_count']
    temp_record['cpu_modelname'] = record['cpu_info']['modelname']
    temp_record['version'] = record['software_version']['product_version']
    
    # get memory parameters in metrics field
    metrics = record['metrics']
    metrics_record = session.xenapi.host_metrics.get_record(metrics)
    temp_record['memory_total'] = int(metrics_record['memory_total']) / (1024**2)
    temp_record['memory_free'] = int(metrics_record['memory_free']) / (1024**2)
    
    if verbose == True:
        # get all PBDs
        temp_record['PBDs'] = []
        pbds = record['PBDs']
        j = 1
        for pbd in pbds:
            temp_pbd = {}
            pbd_record = session.xenapi.PBD.get_record(pbd)
            sr = pbd_record['SR']
            sr_record = session.xenapi.SR.get_record(sr)
            temp_pbd['pbd_attached'] = pbd_record['currently_attached']
            temp_pbd['pbd_device_config'] = str(pbd_record['device_config'])
            temp_pbd['sr_name'] = sr_record['name_label']
            temp_pbd['sr_size'] = "%.2f" % (float(sr_record['physical_size']) / float(1024**3))
            temp_pbd['sr_allocation'] = "%.2f" % (float(sr_record['virtual_allocation']) / float(1024**3))
            temp_pbd['sr_utilisation'] = "%.2f" % (float(sr_record['physical_utilisation']) / float(1024**3))
            temp_pbd['sr_type'] = sr_record['type']
            temp_pbd['id'] = j
            j += 1
            temp_record['PBDs'].append(temp_pbd)
        
        # get all PIFs
        temp_record['PIFs'] = []
        pifs = record['PIFs']
        k = 1
        for IF in pifs:
            temp_pif = {}
            IF_record = session.xenapi.PIF.get_record(IF)
            temp_pif['ip_config_mode'] = IF_record['ip_configuration_mode']
            temp_pif['is_physical'] = IF_record['physical']
            temp_pif['device'] = IF_record['device']
            temp_pif['is_management'] = IF_record['management']
            temp_pif['IP'] = IF_record['IP']
            temp_pif['netmask'] = IF_record['netmask']
            temp_pif['MAC'] = IF_record['MAC']
            temp_pif['VLAN'] = IF_record['VLAN']
            temp_pif['id'] = k
            k += 1
            temp_record['PIFs'].append(temp_pif)
        
    return temp_record


def get_xenserver_host(xenhost):
    '''
    获取单台xenserver的相信信息
    @xenhost: xenserver的IP
    '''
    for ip, session in global_xenserver_conn.items():
        hosts = session.xenapi.host.get_all()
        for host_record in hosts:
                record = session.xenapi.host.get_record(host_record)
                if record['address'] == xenhost:
                    temp_host = get_host_info(session, host_record, verbose=True)
                    return temp_host


def get_xenserver_host_all():
    '''
    获取所有xenserver的简略信息
    '''
    final_hosts = []
    for ip, session in global_xenserver_conn.items():
        temp = {}
        hosts = session.xenapi.host.get_all()
        temp[ip] = []
        i = 1
        for host in hosts:
            temp_host = get_host_info(session, host, verbose=False)
            temp_host['id' ]  = i
            i += 1
            temp[ip].append(temp_host)
            
        final_hosts.append(temp)
        
    return final_hosts


def get_xenserver_vm_all(host):
    '''
    获取单台xenserver的所有虚拟机
    @host xenserver的IP地址
    '''
    final_vms_record = []
    for ip, session in global_xenserver_conn.items():
        if ip == host:
            vms = session.xenapi.VM.get_all()
            i = 1
            for vm in vms:
                record = session.xenapi.VM.get_record(vm)
                if not record['is_a_template'] and not record['is_control_domain']:
                    temp_record = {}
                    temp_record['uuid'] = record['uuid']
                    temp_record['vcpu_max'] = record['VCPUs_max']
                    temp_record['memory_static_max'] = int(record['memory_static_max']) / (1024**2)
                    temp_record['name_label'] = record['name_label']
                    temp_record['power_state'] = record['power_state']
                    vm_ref = vm.split(":")[1]
                    temp_record['vm_ref' ] = vm_ref
                    
                    #get network information
                    guest_metrics = record['guest_metrics']
                    if guest_metrics != "OpaqueRef:NULL":
                        guest_metrics_record = session.xenapi.VM_guest_metrics.get_record(guest_metrics)
                        temp_record['networks'] = guest_metrics_record['networks']
                    else:
                        temp_record['networks'] = {}
                    temp_record['id'] = i
                    i += 1
                    
                    final_vms_record.append(temp_record)
    
    return final_vms_record
