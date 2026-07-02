cmake_minimum_required(VERSION 3.16)
project(sentinelx_agent LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(sentinelx-agent
  src/main.cpp
  src/agent.cpp
  src/http_client.cpp
  src/queue.cpp
  src/collectors.cpp
)

target_include_directories(sentinelx-agent PRIVATE src)

if(WIN32)
  target_link_libraries(sentinelx-agent PRIVATE winhttp)
endif()
# Project version: SentinelX V1.2
