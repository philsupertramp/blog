---
tags:
 - old-wiki
 - published
title: Arch linux maintenance
description: Arch linux maintenance tips and tricks
layout: mylayout.njk
author: Philipp
date: 2022-09-25
---

### General
1. Run `pacman -Syyu` every once in a while
2. follow it's output line by line to notice changes
3. system upgrade results in black screen -> run `nvidia-modeprobe` or check your grafics-drivers
4. upgrade mirror list using `pacman-mirrors`

### Disable on-board speaker
uncomment or add this line in `/etc/inputrc` or `~/.inputrc`: 
```shell
set bell-style none
```

### Lookup for laptop battery
```shell
acpi -V
```

### Rebooted system and no network available?

Jeez, they broke the kernel again, check which module you need
either `r8169` or `r8168` and activate the needed using

```bash
sudo modprobe [r8169|r8168]
```

### Trouble with your touchpad after hybernation/sleep?
A bash-script to help:
```bash
 	#!/usr/bin/bash

	sudo modprobe -r psmouse # deactivate kernel module
	sudo modprobe psmouse    # reactivate kernel module
```

### Main repo signature issue:
```shell
	> pacman -Syyu
	# results in
	error: GPGME error: No data
	error: GPGME error: No data
	error: GPGME error: No data
	error: GPGME error: No data
	:: Synchronising package databases...
	 core                                                          165,5 KiB  2,02 MiB/s 00:00 [####################################################] 100%
	 core.sig                                                      114,0   B  0,00   B/s 00:00 [####################################################] 100%
	error: GPGME error: No data
	error: failed to update core (invalid or corrupted database (PGP signature))
	 extra                                                        1968,1 KiB  5,34 MiB/s 00:00 [####################################################] 100%
	 extra.sig                                                     114,0   B  0,00   B/s 00:00 [####################################################] 100%
	error: GPGME error: No data
	error: failed to update extra (invalid or corrupted database (PGP signature))
	 community                                                       6,6 MiB  5,84 MiB/s 00:01 [####################################################] 100%
	 community.sig                                                 114,0   B  0,00   B/s 00:00 [####################################################] 100%
	error: GPGME error: No data
	error: failed to update community (invalid or corrupted database (PGP signature))
	 multilib                                                      180,5 KiB  5,88 MiB/s 00:00 [####################################################] 100%
	 multilib.sig                                                  114,0   B  0,00   B/s 00:00 [####################################################] 100%
	error: GPGME error: No data
	error: failed to update multilib (invalid or corrupted database (PGP signature))
	error: failed to synchronize all databases
```
Solution:
Update your mirrorlist!

```shell
	> sudo pacman -S archlinux-keyring
```

### Lenovo Thinkpad x240 bt headset
Ran into trouble again setting up my Bose BT Headset.

1. Try connecting using `bluetoothctl` from `bluez-utils`
2. if pairing works but connecting doesn't check `journalctl` output
3. if profile is unavailable you forgot to install `pulseaudio-bluetooth`

### bt not working after reboot
Sometimes a kernel module is not loaded on reboot. Try loading module `btusb`

```shell
	modprove btusb
```
restart bluetooth service
```shell
	systemctl restart bluetooth
```
connect to device using `bluetoothctl`

**note**: don't forget  `agent on; power on;`
