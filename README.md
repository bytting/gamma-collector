# gamma-collector

Detector controller running on Raspberry Pi (archlinuxarm), controlling a gamma detector and a GPS device.

Acquisitions and position are merged, saved to sqlite database and transferred over a UDP connection to Gamma Analyzer.

This software is part of a drone project at Norwegian Radiation Protection Authority (NRPA)

### Status
   Development

### Dependencies
1. Python 2
2. Python Twisted
3. Canberra Osprey SDK V1.0.1 (Proprietary)
4. gpsd

### Installing

The directory config_files contains four config files that can be used to configure devices and enable auto login.
Some of these files contain system specific directories, user names and symbolic links to python binaries, 
so make sure to modify them accordingly.

1. override.conf

   Copy this file to ``/etc/systemd/system/getty@tty1.service.d/override.conf`` to enable auto login.

2. numsys.rules

   Copy this file to ``/etc/udev/rules.d/numsys.rules`` to configure device names

3. numsys.service

   Copy this file to ``$(HOME)/.config/systemd/user/numsys.service`` and enable it using systemctl:  
   `$ systemctl --user enable numsys.service`

   This should start gammad.py when logging in.

4. gpsd

	Copy this file to ``/etc/gpsd`` to configure the gps.

The Osprey SDK contains a "DataTypes" directory with the python modules used to manage a Canberra Osprey detector.
For the osprey plugin to work, copy this directory to the parent directory of the gamma-collector source, 
so that plugin_osprey.py will find it as "../DataTypes"
The Osprey API is also expected to be available at IP address 10.0.1.4.

Given a successful configuration, gammad.py will be listening on UDP port 9999 after booting up the system.

Sessions will be stored locally under the directory ``$(HOME)/gc``

Note that the python scripts gammad.py and gammac.py contains Shebang references to python2,
this may need to be changed when running on other systems than ArchlinuxARM.
