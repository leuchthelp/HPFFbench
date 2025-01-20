import psutil
import platform
import datetime
import logging
import argparse
import multiprocessing
import threading
import schedule
import time

def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor
        

def get_plattform():
    log_message(f"=== System Information ===")
    uname = platform.uname()
    log_message(f"System: {uname.system}")
    log_message(f"Node Name: {uname.node}")
    log_message(f"Release: {uname.release}")
    log_message(f"Version: {uname.version}")
    log_message(f"Machine: {uname.machine}")
    log_message(f"Processor: {uname.processor}")
    
    
def get_cpu():
    # let's print CPU information
    log_message(f"=== CPU Info ===")
    # number of cores
    log_message(f"Physical cores: {psutil.cpu_count(logical=False)}")
    log_message(f"Total cores: {psutil.cpu_count(logical=True)}")
    # CPU frequencies
    cpufreq = psutil.cpu_freq()
    log_message(f"Max Frequency: {cpufreq.max:.2f}Mhz")
    log_message(f"Min Frequency: {cpufreq.min:.2f}Mhz")
    log_message(f"Current Frequency: {cpufreq.current:.2f}Mhz")
    # CPU usage
    log_message("CPU Usage Per Core:")
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
        log_message(f"Core {i}: {percentage}%")
    log_message(f"Total CPU Usage: {psutil.cpu_percent()}%")
    
    
def get_mem():
    # Memory Information
    log_message(f"=== Memory Information ===")
    # get the memory details
    svmem = psutil.virtual_memory()
    log_message(f"Total: {get_size(svmem.total)}")
    log_message(f"Available: {get_size(svmem.available)}")
    log_message(f"Used: {get_size(svmem.used)}")
    log_message(f"Percentage: {svmem.percent}%")
    log_message("=== SWAP ===")
    # get the swap memory details (if exists)
    swap = psutil.swap_memory()
    log_message(f"Total: {get_size(swap.total)}")
    log_message(f"Free: {get_size(swap.free)}")
    log_message(f"Used: {get_size(swap.used)}")
    log_message(f"Percentage: {swap.percent}%")
    
    
def get_disk_usage():
    # Disk Information
    log_message(f"=== Disk Information ===")
    log_message(f"Partitions and Usage:")
    # get all disk partitions
    partitions = psutil.disk_partitions()
    for partition in partitions:
        log_message(f"=== Device: {partition.device} ===")
        log_message(f"  Mountpoint: {partition.mountpoint}")
        log_message(f"  File system type: {partition.fstype}")
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            # this can be catched due to the disk that
            # isn't ready
            continue
        log_message(f"  Total Size: {get_size(partition_usage.total)}")
        log_message(f"  Used: {get_size(partition_usage.used)}")
        log_message(f"  Free: {get_size(partition_usage.free)}")
        log_message(f"  Percentage: {partition_usage.percent}%")
    # get IO statistics since boot
    disk_io = psutil.disk_io_counters()
    log_message(f"Total read: {get_size(disk_io.read_bytes)}")
    log_message(f"Total write: {get_size(disk_io.write_bytes)}")
    
    
def get_network():
    # Network information
    log_message(f"=== Network Information ===")
    # get all network interfaces (virtual and physical)
    if_addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in if_addrs.items():
        for address in interface_addresses:
            log_message(f"=== Interface: {interface_name} ===")
            if str(address.family) == 'AddressFamily.AF_INET':
                log_message(f"  IP Address: {address.address}")
                log_message(f"  Netmask: {address.netmask}")
                log_message(f"  Broadcast IP: {address.broadcast}")
            elif str(address.family) == 'AddressFamily.AF_PACKET':
                log_message(f"  MAC Address: {address.address}")
                log_message(f"  Netmask: {address.netmask}")
                log_message(f"  Broadcast MAC: {address.broadcast}")
    # get IO statistics since boot
    net_io = psutil.net_io_counters()
    log_message(f"Total Bytes Sent: {get_size(net_io.bytes_sent)}")
    log_message(f"Total Bytes Received: {get_size(net_io.bytes_recv)}")
    
def log_message(message):
    # Configure logging
    logging.debug(message)
    
def run_health_checks():
    log_message(f"Monitoring the system...")
    log_message(f"Running system health checks...")

    get_cpu()
    get_mem()
    get_disk_usage()
    get_network()

    log_message(f"Health checks completed.")
    


def run_logging(filepath):
    logging.basicConfig(filename=filepath, level=logging.DEBUG,
                       format='%(asctime)s - %(message)s')
    
    schedule.every(1).seconds.do(run_health_checks)
    
    while True:
        
        schedule.run_pending()
        time.sleep(1)
    
