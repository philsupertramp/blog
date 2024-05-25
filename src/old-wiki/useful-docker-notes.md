---
tags:
 - old-wiki
 - published
title: Useful notes for container orchestration using docker
description: Useful notes for container orchestration using docker
layout: mylayout.njk
author: Philipp
date: 2022-09-25
---

### Use a alpine based image, it's just smaller! Except you need ubuntu, then use ubuntu.

#### Alpine
- Base image `alpine:latest`

#### Ubuntu
- Base image `ubuntu:latest`

#### Python
- Base image `python:3.8-alpine`

##### **graphviz library**

build requirements:  

 	apk add pkgconfig graphviz graphviz-dev gcc musl-dev


## Don't run as `root`!

run container as current user

	docker -u "$(id -u):$(id -g)" ...
