#pragma once

#include <cstdint>
#include <map>
#include <sstream>
#include <string>

struct Event {
  std::int64_t ts;
  std::string host;
  std::string type;
  std::map<std::string, std::string> data;
};

inline std::string json_escape(const std::string& input) {
  std::ostringstream out;
  for (char ch : input) {
    switch (ch) {
      case '"': out << "\\\""; break;
      case '\\': out << "\\\\"; break;
      case '\n': out << "\\n"; break;
      case '\r': out << "\\r"; break;
      case '\t': out << "\\t"; break;
      default: out << ch; break;
    }
  }
  return out.str();
}

inline std::string to_json(const Event& event) {
  std::ostringstream out;
  out << "{\"ts\":" << event.ts
      << ",\"host\":\"" << json_escape(event.host)
      << "\",\"event\":\"" << json_escape(event.type)
      << "\",\"data\":{";
  bool first = true;
  for (const auto& [key, value] : event.data) {
    if (!first) {
      out << ",";
    }
    first = false;
    out << "\"" << json_escape(key) << "\":\"" << json_escape(value) << "\"";
  }
  out << "}}";
  return out.str();
}
// Project version: SentinelX V1.6








