---
tags:
 - old-wiki
 - published
title: Create bootable USB from .iso file
description: Create bootable USB from .iso file
layout: mylayout.njk
author: Philipp
date: 2021-03-26
---
### Plug in your flash drive
### Search for you flash drive using `lsblk`  
```
> lsblk  
NAME                               MAJ:MIN RM   SIZE RO TYPE  MOUNTPOINT  
sda                                8:0            0       XG  0 disk  
├─sda1                             8:1            0       XM  0 part  
├─...
...
sdb                                8:16           1       YG  0 disk <---- this  
├─sdb1                             8:17           1       YG  0 part  
└─sdb2                             8:18           1       YM  0 part  
```

### Download .iso-file
from known source also get the SHA1/hash to verify the file (I will use `manjaro-gnome-21.0-210318-linux510.iso` as an example)
### verify the file using
```bash
> echo "[SHA1] *[image-file-name]" | shasum -a 256 --check
```
as an example  
```bash
> echo "297eb08f08a3821323c15456ce5e7ddf6ed3edf4 *manjaro-gnome-21.0-210318-linux510.iso" | shasum -a 256 --check  
manjaro-gnome-21.0-210318-linux510.iso: OK
```
### copy .iso-file to flash drive  
```bash
> dd if=manjaro-gnome-21.0-210318-linux510.iso of=/dev/sdb bs=1M status=progress
```

Done

