#include "agent.hpp"

#include <iostream>

Agent::Agent(std::string host, std::string gateway_url, std::chrono::seconds interval)
    : collectors_(std::move(host)),
      client_(std::move(gateway_url)),
      queue_("sentinelx-offline-queue.jsonl") {
  (void)interval;
}

void Agent::run_once() {
  auto events = collectors_.poll();
  if (!client_.post_events(events)) {
    queue_.append(events);
    std::cerr << "gateway unavailable, queued " << events.size() << " events\n";
  }
}
