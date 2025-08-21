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

And from the hardware side I gathered
- 1x Arduino UNO 
- 1x DHT11 sensor (Temperature and Humidity)
- 1x USB cable for Arduino
- 1x small breadboard to connect components
- 3x wires

On the initial setup of the Arduino I needed to install required firmware/drivers
```
# arduino-cli core install ...
```
once that finished we can start working on our project.

First I created an empty directory `weedar` and initialized git in it.

Ready for take-off!

First things first, the "Hello World".

For that we create a file `weedar.ino` with the contents
```cpp
void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600); // refresh rate in ms
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.println("Hello World!"); // push string to buffer
  delay(1000); // wait for some time (1000 ms)
}
```
after adding the file we can compile it using
```
# arduino-cli ...
```

Great! We have our hello world compiled, now we just need to push it onto the Arduino.

For that we first connect the Arduino.
Usually it's detected and connected right away, you can verify that with
```
arduino-cli devices list
```
You should see your device there.

We push our code using
```
# arduino-cli 
```

Don't worry, later we might even build a make file to get rid of all of this manual work =D

To read from the Arduino we simply can do a
```
> cat /dev/xxx
```
which opens up a stream and will for ever read.
```
Hello World!

Hello World!
...
```

Be warned, interrupts cause data loss.


Next, I wanted to read temperature and humidity from the DHT11. Which was surprisingly easy.

I looked up the manual for the Olegoo Arduino UNO Starter Kit, followed the wiring diagram and copied the code to read from the sensor and write to the buffer.

Here's an alternate version of that
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

Before we can compile that, we need to install the library that gives us `dht11.h` with the command

```
# arduino-cli 
```

Then 
- compile
- sync

and finally reading the buffer
```
> cat /dev/xxx
Humidity (%): 23.0
Temperature (C): 22.3

Humidity (%): 23.0
Temperature (C): 22.3
...
```

That covers all for today.

Tomorrow, I will update the commands and add some pictures as well as connect the ventilator and a small debugging display.
