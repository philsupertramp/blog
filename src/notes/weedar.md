---
tags:
 - note
 - published
title: "Weedar: my first embedded systems project"
layout: mylayout.njk
author: Philipp
description:
date: 2025-08-21
---

Last night a friend of mine dropped off his most recent harvest, a modest
amount of wet weed.

We both started this year with one month difference, and I wanted to build a "smart dry-box"
anyways, so I told him to pass it on to me for some time.

This allows me to gather some data points and build a solution until my plant is done.

Somehow I expect a bigger yield than him.

Now here's the thing, the current boss fight! :)

// add image

## The idea
I have several RaspberryPi's and an Arduino Uno with several sensors laying around, that I want to use to build something useful.

Hence, I figured I will build a "smart" ventilation system, with sensors and some other things!

Here's the plan
1. We need to gather data:
  1. Humidity
  2. Temperature
2. add ventilator
3. Analyze data after adding the ventilator
4. Improve ventilation if needed
5. Reiterate from 3.

I will use in the beginning an Arduino Uno and not collect any data points, rather just act on current values.
Later, I want to connect a RaspberryPi and read from the Arduino's buffer, to store the data.

Unfortunately, over night my whole flat started to smell very strong, hence in the best case we're even able to 
do something against that!

I've currently added an air filter into the box, but due to lack of ventilation it doesn't really do anything.

## Day 1
Today I've set up the Arduino Uno on my laptop.

For that I installed
- arduino-cli
- screen
- neovim extension: https://github.com/stevearc/vim-arduino



The "Hello World"
```cpp
void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.println("Hello World!");
  delay(1000);
}
```


The first signals
```cpp
#include <dht11.h>
#define DHT11PIN 4

dht11 DHT11;

void  setup()
{
  Serial.begin(9600);
}
void loop()
{
  Serial.println();

  int chk = DHT11.read(DHT11PIN);

  Serial.print("Humidity (%): ");
  Serial.println((float)DHT11.humidity, 2);

  Serial.print("Temperature  (C): ");
  Serial.println((float)DHT11.temperature, 2);

  delay(2000);
}

```
