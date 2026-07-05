---
tags:
 - post
 - published
 - reinforcement-learning
title: "A RL Agent for World of Warcraft"
layout: mylayout.njk
author: Philipp
description: In this post I will attempt to write a reinforcement-learning agent for WoW
published: 2026-05-12
---

First I built a tiny prototype that reads player coordinates and more information out of RAM and
it's goal is to reach a given point on the map.

For this I positioned my character in the Burning Stepps and placed a temporary NPC
a _few_ feet.

After about two hours of letting the bot run using the `WASD` keys it reached it goal within a reasonable
amount of steps.

But this wasn't enough, I wanted more and experiment with a lot of things.

So my first stepping stone was "How can I get input into my window, without disrupting my host system?".
Introducing "Virtual Displays".

## Virtual Displays
It's kind of like an additional, or many, monitors for your setup and once you have the dependencies installed,
it's actually quite simple to set up.

I'm running `i3-wm` on Linux, this uses the `X11` window system. Others might use wayland by now, but we'll use the
x11 dependencies here, specifically `Xvfb` the x virtual frame buffer.
As its name suggests it's a command line tool to run virtual frame buffers, and [frame buffers](https://en.wikipedia.org/wiki/Framebuffer) are the memory
buffers we render onto our displays in GUIs.

{{ note | "It's important to mention now that <strong>:0</strong> is the address for our attached window server, DO NOT OVERRIDE IT!"}}

You can launch any number of virtual framebuffers using
```shell
> Xvfb :101 -screen 0 800x600x24 &
```
This for instances launches a `800x600` big window with 24 colors and detaches the process.

With another tool called ` ` we can open up a temporary port on our host machine to watch this virtual framebuffer

```shell
> x11vnc -display 101 -bg -nopw -listen localhost -xkb
```

With this setup, we can then launch a client inside this virtual display
```
> env DISPLAY=101 WINEARCH=win64 vglrun -d egl wine "$WOW_DIR/Wow.exe" -opengl > /dev/null 2>&1 &
```

Now of course this would be amazing if this worked out of the box, but due to the fact that I own an NVIDIA
GPU this required endless loops of trying different configuration and tooling.

Unfortunately, throughout the process I completely destroyed my work machines X11 config.
But fortunately, I managed to recover everything through TTY-2 with a shock and a sweaty t-shirt.

With that being done, I updated the agents code base to perform commands inside its own `DISPLAY`.  
Booted up the agent...  
And nothing worked - as expected.

_Running multiple agents is still not supported._

## The features
Originally, I thought I can fetch all the required features from the game client, until I wanted to send
it to it's first task, which is waypoint following.

The issue is that we can get all information that the player sees and we can compute other things from that information to enrich the feature space
that we can extract from the game client.

But one of the hardest things is to build proper pathing, without using A* or other algorithms.

To overcome this, I wrote a small extension for the server engine we will be using for this project.
The engine we use is called [TrinityCore](https://github.com/TrinityCore/TrinityCore). It allows custom scripts and has a path finding
engine "Nav Mesh" under the hood already.

The custom script is fairly simple. It uses the two header only dependencies `nlohmann::json` and `httplib.h` and gets compiled with the
server source.

```cpp
#include "ScriptMgr.h"
#include "MapManager.h"
#include "MMapFactory.h"
#include "MMapManager.h"
#include "Log.h"                  // Required for TC_LOG macros
#include <G3D/Vector3.h>          
#include "DetourNavMesh.h"        
#include "DetourNavMeshQuery.h"   
#include "./httplib.h"
#include "./json.hpp"
#include <thread>
#include <vector>

using json = nlohmann::json;

class NavMeshAPI : public WorldScript {
public:
    NavMeshAPI() : WorldScript("NavMeshAPI") {
        TC_LOG_INFO("server", "NavMeshAPI: Constructor called!");
    }

    void OnStartup() override {
        TC_LOG_INFO("server", "NavMesh API: OnStartup() called!");
        std::thread t(&NavMeshAPI::RunHTTPServer, this);
        t.detach();
        TC_LOG_INFO("server", "NavMesh API: HTTP server thread spawned");
    }

private:
    void RunHTTPServer() {
        try {
            httplib::Server svr;

            svr.Post("/api/pathfind", [this](const httplib::Request& req, httplib::Response& res) {
                try {
                    auto body = json::parse(req.body);
                    uint32 mapId = body["mapId"];
                    float startX = body["startX"], startY = body["startY"], startZ = body["startZ"];
                    float endX = body["endX"], endY = body["endY"], endZ = body["endZ"];
                    TC_LOG_INFO("server", "NavMesh API Received Request -> Map ID: {}, X: {:.1f}, Y: {:.1f}", mapId, startX, startY);
                    Map* map = sMapMgr->FindMap(mapId, 0);
                    if (!map) {
                        res.status = 400;
                        res.set_content(R"({"error": "Map not loaded"})", "application/json");
                        return;
                    }

                    MMAP::MMapManager* mmapManager = MMAP::MMapFactory::createOrGetMMapManager();
                    if (!mmapManager) {
                        res.status = 500;
                        res.set_content(R"({"error": "NavMesh system offline"})", "application/json");
                        return;
                    }

                    const dtNavMeshQuery* navQuery = mmapManager->GetNavMeshQuery(mapId, 0);
                    if (!navQuery) {
                        res.status = 500;
                        res.set_content(R"({"error": "NavMesh for map not loaded"})", "application/json");
                        return;
                    }

                    dtQueryFilter filter;
                    filter.setIncludeFlags(0xFFFF); 
                    filter.setExcludeFlags(0);

                    // 1. Swap WoW (X, Y, Z) into Detour (Y, Z, X)
                    float startPoint[3] = { startY, startZ, startX };
                    float endPoint[3] = { endY, endZ, endX };
                    
                    // 2. Extents must also match Detour's axes! 
                    // Detour[1] is now the vertical axis. We give it 20 yards of vertical leniency.
                    float extents[3] = { 10.0f, 20.0f, 10.0f }; 

                    dtPolyRef startRef = 0;
                    dtPolyRef endRef = 0;
                    float nearestStart[3];
                    float nearestEnd[3];

                    navQuery->findNearestPoly(startPoint, extents, &filter, &startRef, nearestStart);
                    navQuery->findNearestPoly(endPoint, extents, &filter, &endRef, nearestEnd);

                    if (startRef == 0) {
                        TC_LOG_ERROR("server", "NavMesh Debug: Could not find START polygon near X:{:.1f} Y:{:.1f} Z:{:.1f}", startX, startY, startZ);
                    }
                    if (endRef == 0) {
                        TC_LOG_ERROR("server", "NavMesh Debug: Could not find END polygon near X:{:.1f} Y:{:.1f} Z:{:.1f}", endX, endY, endZ);
                    }
                    json pathJson = json::array();
                    bool success = false;

                    if (startRef && endRef) {
                        dtPolyRef pathPolys[256];
                        int pathCount = 0;
                        
                        dtStatus status = navQuery->findPath(startRef, endRef, startPoint, endPoint, &filter, pathPolys, &pathCount, 256);
                        if (startRef != 0 && endRef != 0 && pathCount == 0) {
                            TC_LOG_ERROR("server", "NavMesh Debug: Both polygons found, but path generation failed! Distance too far or path blocked.");
                        }

                        
                        if (dtStatusSucceed(status) && pathCount > 0) {
                            float straightPath[256 * 3];
                            unsigned char straightPathFlags[256];
                            dtPolyRef straightPathPolys[256];
                            int straightPathCount = 0;

                            navQuery->findStraightPath(startPoint, endPoint, pathPolys, pathCount, 
                                                       straightPath, straightPathFlags, straightPathPolys, 
                                                       &straightPathCount, 256, 0);

                            success = true;
                            // 3. Swap Detour (Y, Z, X) back to WoW (X, Y, Z) for the JSON response
                            for (int i = 0; i < straightPathCount; ++i) {
                                pathJson.push_back(json{
                                    {"x", straightPath[i * 3 + 2]}, // Detour's [2] is WoW's X
                                    {"y", straightPath[i * 3 + 0]}, // Detour's [0] is WoW's Y
                                    {"z", straightPath[i * 3 + 1]}  // Detour's [1] is WoW's Z
                                });
                            }
                        }
                    }

                    json response;
                    response["success"] = success;
                    response["path"] = pathJson;
                    res.set_content(response.dump(), "application/json");

                } catch (const std::exception& e) {
                    res.status = 500;
                    res.set_content(fmt::format(R"({{"error": "{}"}})", e.what()), "application/json");
                }
            });

            if (!svr.listen("0.0.0.0", 8080)) {
                TC_LOG_ERROR("server", "NavMesh API: Failed to bind to port 8080");
            }
        } catch (const std::exception& e) {
            // fmt arguments can be passed directly to the TC_LOG macros
            TC_LOG_ERROR("server", "NavMesh API Error: {}", e.what());
        }
    }
};

void AddSC_navmeshapi() {
    new NavMeshAPI();
}
```

You place it inside `./src/server/scripts/Custom` along the dependency files and the already existing `custom_script_loader.cpp`.
Then edit `custom_script_loader.cpp` and replace its content with the following
```cpp
#include "ScriptMgr.h"
#include "Log.h"

void AddSC_navmeshapi();

void AddCustomScripts() {
    TC_LOG_INFO("server", "CUSTOM_SCRIPT_LOADER: Starting...");
    AddSC_navmeshapi();
    TC_LOG_INFO("server", "CUSTOM_SCRIPT_LOADER: NavMeshAPI server configured...");
}

```

Once this is done you can build the TrinityCore source and will see the running server once you start up the `worldserver` executable.

I wrapped all of this into a `Dockerfile`
```docker
# ==========================================
# STAGE 1: Builder
# ==========================================
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git cmake make gcc g++ clang \
    libssl-dev libbz2-dev libreadline-dev libncurses-dev \
    libboost-all-dev default-libmysqlclient-dev

# Clone TrinityCore 
WORKDIR /usr/src
RUN git clone -b 3.3.5 --depth 1 https://github.com/TrinityCore/TrinityCore.git

# Inject Custom Scripts
# TrinityCore's CMake automatically detects and compiles files in this directory
COPY custom_scripts/ /usr/src/TrinityCore/src/server/scripts/Custom/

# Configure and Build
WORKDIR /usr/src/TrinityCore/build
RUN cmake ../ \
    -DCMAKE_INSTALL_PREFIX=/opt/trinitycore \
    -DTOOLS=0 \
    -DSCRIPTS=static \
    -DWITH_WARNINGS=0

RUN make -j $(nproc) install

RUN cp -r /usr/src/TrinityCore/sql /opt/trinitycore/sql

# ==========================================
# STAGE 2: Runtime Environment
# ==========================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive


# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libssl3 libbz2-1.0 libreadline8 libncurses6 \
    libboost-all-dev \
    default-mysql-client libmysqlclient21 \
    curl xml2 \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled binaries and essential files from builder
COPY --from=builder /opt/trinitycore /opt/trinitycore
COPY --from=builder /usr/src/TrinityCore/sql /usr/src/TrinityCore/sql

# Set up working directory for the server
WORKDIR /opt/trinitycore/bin
ADD https://raw.githubusercontent.com/neechbear/tcadmin/master/tcadmin "/opt/trinitycore/bin/tcadmin"

RUN chmod -v 0755 /opt/trinitycore/bin/*

ENV PATH=$PATH:/opt/trinitycore/bin

# We will override the command in docker-compose.yml
CMD ["./worldserver"]
```

It installs some dependencies for easier integration later.
Of course this ended up in a `docker-compose.yaml` file, because I don't want to run the `mysql` service
on my machine, nor like dumping my whole system with the data produced. Also we can just remove all of it
once we are tired of the project.

Well, long story short here's the compose file
```yaml
services:
  mysql:
    image: mysql:8.0
    container_name: tc_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: trinity # Change this
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql
      # Optional: Mount SQL init scripts if you need to auto-populate the TDB
      - ./sql/docker-entrypoint-initdb.d/:/docker-entrypoint-initdb.d

  bnetserver:
    build: 
      context: .
      dockerfile: Dockerfile
    image: custom-trinitycore:latest
    container_name: tc_bnet
    command: ["./authserver"]
    depends_on:
      - mysql
    links:
      - mysql
    ports:
      - "3724:3724"
    volumes:
      - ./config/authserver.conf/authserver.conf:/opt/trinitycore/etc/authserver.conf
    restart: unless-stopped

  worldserver:
    image: custom-trinitycore:latest
    container_name: tc_world
    command: ["./worldserver"]
    depends_on:
      - mysql
    links:
      - mysql
    ports:
      - "8085:8085"
      # Expose your custom NavMesh API port! (Assuming you bind to 8080 in your C++)
      - "8080:8080" 

      - "8086:8086"
      - "8087:8087"
      - "8088:8088"
      - "8089:8089"
      - "3443:3443"
      - "7878:7878"
    volumes:
      - ./config/worldserver.conf/worldserver.conf:/opt/trinitycore/etc/worldserver.conf
      - ./data:/opt/trinitycore/data:ro
      - ./bin/TDB_full_world_335.25101_2025_10_21.sql:/opt/trinitycore/bin/TDB_full_world_335.25101_2025_10_21.sql:ro
      - logs_data:/opt/trinitycore/logs
    restart: unless-stopped
    # Allocate a pseudo-TTY for server console access
    stdin_open: true
    tty: true
    environment:
      TCDBHOST: mysql
      TCSOAPUSER: trinity
      TCSOAPPASS: trinity


volumes:
  db_data:
  logs_data:
```

Once you start this bad boy up, you need to add a few accounts mostly `trinity:trinity` for both the `mysql` client and the 
wow client.

And don't forget to set the admin level for the game account to `3`.

## The Environment
RL agents get trained in so called "Environments", basically sandboxes.
These environment implementations provide a way how to perform a step in the underlying environment as well as a mechanic
how to reset the environment to a controlled state.

This allows the agents to repeadetly 

