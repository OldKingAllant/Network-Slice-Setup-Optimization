#!/usr/bin/env python3

import random
import threading
import time

from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel


def scalable_topology(K=3, T=20, auto_recover=True):
    """
    Topologia spine–leaf con ridondanza:
    - K spine
    - 2*K leaf
    - K host per leaf
    - ogni leaf è collegato a tutti gli spine
    - ogni T sec cade un link leaf<->spine casuale
    """

    net = Mininet(controller=Controller, link=TCLink)
    net.addController("c0")

    # ----- SPINE -----
    spine_switches = []
    for i in range(K):
        spine = net.addSwitch(f"s_spine_{i+1}")
        spine_switches.append(spine)

    # ----- LEAF -----
    leaf_switches = []
    for i in range(2 * K):
        leaf = net.addSwitch(f"s_leaf_{i+1}")
        leaf_switches.append(leaf)

        # collega ogni leaf a TUTTI gli spine
        for spine in spine_switches:
            net.addLink(spine, leaf, bw=100, delay="5ms")

        # aggiungi host
        for h in range(K):
            host = net.addHost(f"h{len(net.hosts) + 1}")
            net.addLink(host, leaf, bw=50)

    net.start()

    # Funzione interna per eventi ambientali (down/up link casuali)
    def environmental_events():
        while True:
            time.sleep(T)
            leaf = random.choice(leaf_switches)
            spine = random.choice(spine_switches)

            print(f"\n*** EVENTO: disabilito link {spine.name} <-> {leaf.name}\n")
            net.configLinkStatus(spine.name, leaf.name, "down")

            # verifica stato link dopo down
            link = net.linksBetween(spine, leaf)[0]
            print(f"Stato link dopo down: {link.intf1.status()} - {link.intf2.status()}")

            if auto_recover:
                time.sleep(T)
                print(f"\n*** RECOVERY: riattivo link {spine.name} <-> {leaf.name}\n")
                net.configLinkStatus(spine.name, leaf.name, "up")

                # verifica stato link dopo up
                print(f"Stato link dopo up: {link.intf1.status()} - {link.intf2.status()}")

    # Avvia thread per eventi ambientali
    event_thread = threading.Thread(target=environmental_events, daemon=True)
    event_thread.start()

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    scalable_topology(K=3, T=15, auto_recover=True)
