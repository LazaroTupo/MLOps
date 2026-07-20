from faker import Faker

import random

from datetime import datetime

fake = Faker()


PROTOCOLS = [

    "TCP",

    "UDP",

    "ICMP"

]

COMMON_PORTS = [

    21,

    22,

    23,

    25,

    53,

    80,

    110,

    135,

    139,

    443,

    445,

    3389

]


def random_ip():

    return fake.ipv4_private()


def generate_base():

    return {

        "timestamp": datetime.now(),

        "source_ip": random_ip(),

        "destination_ip": random_ip(),

        "protocol": random.choice(PROTOCOLS),

        "destination_port": random.choice(COMMON_PORTS),

        "duration": round(random.uniform(0.05,4.5),3),

        "packet_size": random.randint(64,1500),

        "connections": random.randint(1,5),

        "scenario":"normal"

    }


def generate_normal():

    event = generate_base()

    event["scenario"]="normal"

    return event


def generate_port_scan():

    event = generate_base()

    event["scenario"]="port_scan"

    event["packet_size"]=64

    event["connections"]=1

    event["duration"]=0.02

    event["destination_port"]=random.choice(COMMON_PORTS)

    return event


def generate_dos():

    event = generate_base()

    event["scenario"]="dos"

    event["connections"]=random.randint(500,1500)

    event["packet_size"]=random.randint(64,120)

    event["duration"]=0.01

    return event


def generate_bruteforce():

    event = generate_base()

    event["scenario"]="brute_force"

    event["destination_port"]=22

    event["connections"]=random.randint(20,100)

    event["duration"]=0.10

    return event


def generate_recon():

    event = generate_base()

    event["scenario"]="reconnaissance"

    event["connections"]=random.randint(5,20)

    event["packet_size"]=random.randint(64,150)

    return event


def generate_event(scenario):

    scenario=scenario.lower()

    if scenario=="normal":

        return generate_normal()

    elif scenario=="port_scan":

        return generate_port_scan()

    elif scenario=="dos":

        return generate_dos()

    elif scenario=="brute_force":

        return generate_bruteforce()

    elif scenario=="reconnaissance":

        return generate_recon()

    else:

        return generate_normal()