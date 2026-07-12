#pragma once

#include <filesystem>
#include <vector>

#include "event.hpp"

class OfflineQueue {
 public:
  explicit OfflineQueue(std::filesystem::path path);
  void append(const std::vector<Event>& events) const;
  std::vector<Event> drain() const;

 private:
  std::filesystem::path path_;
};
// Project version: SentinelX V1.6

