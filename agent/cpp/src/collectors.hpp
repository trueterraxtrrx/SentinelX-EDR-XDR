#pragma once

#include <string>
#include <vector>

#include "event.hpp"

class Collectors {
 public:
  explicit Collectors(std::string host);
  std::vector<Event> poll();

 private:
  std::string host_;
};
// Project version: SentinelX V1.3
