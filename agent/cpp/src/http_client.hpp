#pragma once

#include <string>
#include <vector>

#include "event.hpp"

class HttpClient {
 public:
  explicit HttpClient(std::string gateway_url);
  bool post_events(const std::vector<Event>& events) const;

 private:
  std::string gateway_url_;
};
// Project version: SentinelX V1.6







