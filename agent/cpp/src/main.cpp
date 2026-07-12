#include <chrono>
#include <iostream>
#include <string>
#include <thread>

#include "agent.hpp"

int main(int argc, char** argv) {
  std::string gateway = "http://localhost:8000/events";
  std::string host = "pc-01";
  bool loop = false;

  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--gateway" && i + 1 < argc) {
      gateway = argv[++i];
    } else if (arg == "--host" && i + 1 < argc) {
      host = argv[++i];
    } else if (arg == "--loop") {
      loop = true;
    }
  }

  Agent agent(host, gateway, std::chrono::seconds(10));
  do {
    agent.run_once();
    if (loop) {
      std::this_thread::sleep_for(std::chrono::seconds(10));
    }
  } while (loop);

  return 0;
}
// Project version: SentinelX V1.6
