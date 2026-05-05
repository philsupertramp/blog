---
tags:
 - note
 - published
 - devops
 - travel
title: "Docker-Train: How to use Docker in Deutsche Bahn's WIFIonICE"
layout: mylayout.njk
author: Philipp
description: Using Docker in the DB trains WIFIonICE gives travelers headaches. Here we will explain how to manage and successfully connect to DB's WIFI.
date: 2026-05-05
---

{% note "This is more or less a translated version of <a href=\"https://www.erikdonner.dev/2024/11/01/wlan-im-ice-mit-linux-und-docker/\">Erik Donner's blog post</a> from 2024." %}

Many of us Software Developers know it, we embark on a longer train ride with our beloved Deutsche Bahn, so we plan to use the time more efficiently.
Because we're lazy and because many of us switched from VMs to Docker, we have the Docker daemon running in the background.

Especially those with DevOps background know that it's an impossible task to constantly type

```shell
systemctl start docker
```
or whatever system manager you prefer.

![by CommitStrip https://www.commitstrip.com/en/2017/02/28/definitely-not-lazy/]({{ '/_includes/assets/2026-05-05/Strip-La-flemme-de-retaper-650-finalenglsih-1.gif' | url }})

This introduces issues when trying to connect to WIFIonICE in trains of Deutsche Bahn, while the deaomon is running.

In this post we'll describe how to resolve this on your Linux machine.

## The Problem

Reason for this issue with WIFIonICE in combination with Docker is the fact that the default installation of Docker is using the same IP range that is also used by WIFIonICE.
We can verify that using 

```shell
> ip addr

1: lo: ...
    ... 
2: enp12s0: ...
    ...
3: wlp0s20f3: ...
    ...
5: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default 
    link/ether ... brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
    inet6 ... scope link proto kernel_ll 
       valid_lft forever preferred_lft forever
```

The default network that is running when the Docker daemon runs is `docker0`.
Alternatively, you can start typing `ip addr show dev docker` then hit the `<TAB>` key to only get the description of the desired network.

The IP addresses `172.17.0.1/16` overlap with the ones provided by WIFIonICE.

## The Solution
The fix is fairly simple, we "only" need to configure Docker to use a different range of IP addresses for its networks.

To do so, we create the file `/etc/docker/daemon.json` with the following content

```json
{
  "default-address-pools": [{ "base": "10.10.0.0/16", "size": 24 }]
}
```
The range `10.10.0.0/16` allows Docker to allocate 65536 addresses. You can use whatever range you feel like, or that works in your setup.

Look for CIDR calculators, like the one from [rohde-schwarz.com](https://www.rohde-schwarz.com/us/solutions/networks-and-cybersecurity/secure-application-gateway/cidr-calculator_256249.html) in case you want to tinker around with it.

In case this sparks some interest and you'd like to learn more about managing IP ranges, check out my friends project called tipam at [kiyutink/tipam](https://github.com/kiyutink/tipam).
It allows you to manage IP range claims, with a lot of quality of life features.

And last but not least, if you want to reset your configuration to the default pools provided with the installation, you can use the following
```json
{
  "default-address-pools": [
    { "base": "172.17.0.0/16", "size": 16 },
    { "base": "172.18.0.0/16", "size": 16 },
    { "base": "172.19.0.0/16", "size": 16 },
    { "base": "172.20.0.0/14", "size": 16 },
    { "base": "172.24.0.0/14", "size": 16 },
    { "base": "172.28.0.0/14", "size": 16 },
    { "base": "192.168.0.0/16", "size": 20 }
  ]
}
```
This is the default by the time of writing this note, but verify this through the docs!

## Wrap-Up
This concludes the configuration, the last step is to ensure that everything is actually using the desired IP range(s).

To do so, we need to
1. stop all running containers
2. destroy the running networks 
3. restart the daemon process.

```shell
# 1. stop all running containers
> docker stop $(docker ps -q)
# 2. remove running networks
> docker network prune
```

We can verify that no more networks are up and running via
```shell
> docker network ls
```

and then finally restart the daemon with the system manager of your choice
```
> systemctl restart docker
```

With this we're all set and can enjoy the WIFI!

---

Sources:
- [Erik Donner](https://www.erikdonner.dev/2024/11/01/wlan-im-ice-mit-linux-und-docker/)
- [Docker Docs](https://docs.docker.com/engine/network/#subnet-allocation)
