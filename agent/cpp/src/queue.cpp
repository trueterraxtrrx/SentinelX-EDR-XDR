#include "queue.hpp"

#include <fstream>
#include <utility>

OfflineQueue::OfflineQueue(std::filesystem::path path) : path_(std::move(path)) {}

void OfflineQueue::append(const std::vector<Event>& events) const {
  std::ofstream out(path_, std::ios::app);
  for (const auto& event : events) {
    out << to_json(event) << "\n";
  }
}

std::vector<Event> OfflineQueue::drain() const {
  // JSON parsing is intentionally omitted in this tiny C++17 skeleton.
  // Real agent builds should use a vetted JSON library and atomic rename.
  std::ofstream truncate(path_, std::ios::trunc);
  return {};
}
