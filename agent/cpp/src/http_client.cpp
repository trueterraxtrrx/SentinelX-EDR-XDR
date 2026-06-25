#include "http_client.hpp"

#include <iostream>
#include <sstream>

HttpClient::HttpClient(std::string gateway_url) : gateway_url_(std::move(gateway_url)) {}

bool HttpClient::post_events(const std::vector<Event>& events) const {
  std::ostringstream body;
  body << "{\"events\":[";
  for (std::size_t i = 0; i < events.size(); ++i) {
    if (i > 0) {
      body << ",";
    }
    body << to_json(events[i]);
  }
  body << "]}";

  // MVP transport stub. Production build should link libcurl or platform TLS APIs
  // and enable mutual TLS with per-agent client certificates.
  std::cout << "POST " << gateway_url_ << "\n" << body.str() << "\n";
  return true;
}
