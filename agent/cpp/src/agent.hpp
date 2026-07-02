#pragma once

#include <chrono>
#include <string>

#include "collectors.hpp"
#include "http_client.hpp"
#include "queue.hpp"

class Agent {
 public:
  Agent(std::string host, std::string gateway_url, std::chrono::seconds interval);
  void run_once();

 private:
  Collectors collectors_;
  HttpClient client_;
  OfflineQueue queue_;
};
// Project version: SentinelX V1.2
