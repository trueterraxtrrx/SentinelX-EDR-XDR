#include "collectors.hpp"

#include <chrono>
#include <utility>

namespace {
std::int64_t now_epoch() {
  return std::chrono::duration_cast<std::chrono::seconds>(
      std::chrono::system_clock::now().time_since_epoch())
      .count();
}
}

Collectors::Collectors(std::string host) : host_(std::move(host)) {}

std::vector<Event> Collectors::poll() {
  const auto ts = now_epoch();
  return {
      {ts, host_, "heartbeat", {{"os", "unknown"}, {"ip", "127.0.0.1"}}},
      {ts, host_, "process_create", {{"pid", "4120"}, {"ppid", "984"}, {"name", "powershell.exe"}, {"cmd", "powershell.exe -enc SQBFAFgA"}}},
      {ts, host_, "network_connect", {{"pid", "4120"}, {"dst", "203.0.113.10:443"}, {"direction", "outbound"}}},
      {ts, host_, "tamper_check", {{"status", "ok"}, {"self_hash", "demo"}}},
  };
}
// Project version: SentinelX V1.6

