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
