#!/bin/bash

# Cleanup
echo "Cleaning up old containers and DNS records..."
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

# Remove old DNS records
rm -rf config/dns_config/zones/*

# Run topology
echo "Running topology..."
SCENARIO=${1:-default}
if ! command -v python3.9 >/dev/null 2>&1
then
    sudo python3 ./topology.py $SCENARIO
else
    sudo python3.9 ./topology.py $SCENARIO
fi

# Cleanup
echo "Execution finished, cleaning up..."
sudo mn -c
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

# Remove old DNS records
rm -rf config/dns_config/zones/*

echo "Cleanup complete"