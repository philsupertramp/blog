---
tags:
 - old-wiki
 - published
title: Regex Search and Replace
description: Regex Search and Replace
layout: mylayout.njk
author: Philipp
date: 2021-04-15
---
# `key = value` pairs into `'key': value` pairs
```regex
search: ([\w\[\].]*)=([\w\[\].]*) 

replace: '$1': $2
```
