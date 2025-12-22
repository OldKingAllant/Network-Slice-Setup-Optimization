systemctl stop systemd-resolved
systemctl disable systemd-resolved
rm /etc/resolv.conf
echo "nameserver 8.8.8.8" | tee /etc/resolv.conf