# burn
Daemon running on Raspberry Pi (archlinuxarm), controlling a Canberra Osprey gamma detector and a G-Star IV GPS device.

Acquisitions and measurements are merged, saved to disk and optionally transferred over a TCP connection to the controlling application, crash.

This software is part of a drone project at Norwegian Radiation Protection Authority (NRPA)

### Status
   Development

### Dependencies
1. Python 2
2. Canberra Osprey SDK V1.0.1
3. gpsd

### Installing

The directory config_files contains three systemd service files that should be used to enable auto login 
and configuration of the detector and the GPS device. These files contain system specific directories, 
user names and symlinks to python binaries, so make sure to modify them accordingly.

1. override.conf

   Copy this file to /etc/systemd/system/getty@tty1.service.d/override.conf to enable auto login.

2. drone-setup-system.service

   Copy this file to /etc/systemd/system/drone-setup-system.service and enable it using systemctl:  
   `sudo systemctl enable drone-setup-system.service`

3. drone-setup-local.service

   Copy this file to $(HOME)/.config/systemd/user/drone-setup-local.service and enable it with systemctl:  
   `systemctl --user enable drone-setup-local.service`
