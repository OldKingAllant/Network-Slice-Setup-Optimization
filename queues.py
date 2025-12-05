from mininet.node import OVSSwitch
from mininet.link import Intf
import json

from typing import List, Dict, Tuple

import logging
import requests

def load_queues(qos_file: str, switches: List[Tuple[str, OVSSwitch]], controller_ip: str, controller_port: str, default_bw: float = 1e6, default_delay=5):
    with open(qos_file) as qos_fd:
        print(f'Load queue: file {qos_file} opened')
        try:
            qos_temp: list[Dict[str, str]] = json.load(qos_fd)
        except:
            print('Load queue: json load failed')
            return False 
    try:
        qos: list[Dict[str, float]] = []

        bw_strings = ['kb', 'mb', 'gb']
        bw_mult = [1e3, 1e6, 1e9]
        delay_strings = ['ms']
        delay_mult = [1]

        def try_parsing(name: str, args: Dict[str, str], mults: List[float], strings: List[str], default: float):
            value = default
            if name in args:
                value = args[name]
                if not isinstance(value, str):
                    return value
                for mult, string in zip(mults, strings):
                    if string in value:
                        value = value.replace(string, "")
                        used_mult = mult 
                        value = float(value) * used_mult
                value = float(value)
            return value
                        
        for index, queue in enumerate(qos_temp):
            queue_min_bw = try_parsing("min_bw", queue, bw_mult, bw_strings, default_bw)
            queue_max_bw = try_parsing("max_bw", queue, bw_mult, bw_strings, default_bw)
            
            queue_min_delay = try_parsing("min_delay", queue, delay_mult, delay_strings, default_delay)
            queue_max_delay = try_parsing("max_delay", queue, delay_mult, delay_strings, default_delay)
            
            qos.append({"min_bw": queue_min_bw, "max_bw": queue_max_bw, "min_delay": queue_min_delay, "max_delay": queue_max_delay})
        
        for name, switch in switches:
            print(f'Load queue: switch {switch.dpid}')
            interfaces: list[Intf] = switch.intfList()
            print(f'Load queue: switch has {len(interfaces)} interfaces')
            for intf in interfaces:
                bw = try_parsing("bw", intf.params, bw_mult, bw_strings, default_bw)
                delay = try_parsing("delay", intf.params, delay_mult, delay_strings, default_delay)

                print(f'bw: {bw}, delay: {delay}')
                vsctl_cmd = [f'set port {name}', 'qos=@newqos -- --id=@newqos create qos', f'type=linux-htb other-config:max-rate={bw}']
                queues = ['queues=']
                for queue_num in range(len(qos)):
                    queues.append(f'{queue_num}=@q{queue_num}')
                    if queue_num < len(qos) - 1:
                        queues.append(',')
                vsctl_cmd.append(''.join(queues))
                """
                --   --id=@q0   create   Queue   other-config:min-rate=100000000
                other-config:max-rate=100000000 \

                -- --id=@q1 create Queue other-config:min-rate=500000000
                """
                        
                for index, queue in enumerate(qos):
                    queue_min_bw = queue["min_bw"]
                    queue_max_bw = queue["max_bw"]

                    if queue_min_bw > bw or queue_max_bw > bw:
                        print(f'Load queue: qos {index} expects bw bigger than the link')
                        return False
                    
                    queue_min_delay = queue["min_delay"]
                    queue_max_delay = queue["max_delay"]
                    
                    if queue_min_delay < delay or queue_max_delay < delay:
                        print(f'Load queue: qos {index} expects delay smaller than the link')
                        return False
                    vsctl_cmd.append(f'-- --id=@q{index} create queue other-config:min-rate={queue_min_bw} other-config:max-rate={queue_max_bw}')
                vsctl_cmd_complete = ' '.join(vsctl_cmd)
                print(f"vsctl command: {vsctl_cmd_complete}")
                print(switch.vsctl(vsctl_cmd_complete))
    except:
        logging.exception("Exception occurred while parsing qos")
        return False
    print(qos)

    requests.post(f'http://{controller_ip}:{controller_port}/api/v0/qos', 
                  headers={'ContentType': 'application/json'},
                  json=qos)
    return True
