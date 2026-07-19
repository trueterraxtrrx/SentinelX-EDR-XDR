#include "queue.hpp"

#include <cstdio>
#include <fstream>
#include <optional>
#include <string>
#include <utility>

OfflineQueue::OfflineQueue(std::filesystem::path path) : path_(std::move(path)) {}

void OfflineQueue::append(const std::vector<Event>& events) const {
  std::ofstream out(path_, std::ios::app);
  for (const auto& event : events) {
    out << to_json(event) << "\n";
  }
}

namespace {
std::string unescape_json_string(const std::string& input) {
  std::string output;
  output.reserve(input.size());
  bool escaped = false;
  for (char ch : input) {
    if (escaped) {
      switch (ch) {
        case 'n': output.push_back('\n'); break;
        case 'r': output.push_back('\r'); break;
        case 't': output.push_back('\t'); break;
        default: output.push_back(ch); break;
      }
      escaped = false;
    } else if (ch == '\\') {
      escaped = true;
    } else {
      output.push_back(ch);
    }
  }
  return output;
}

std::optional<std::string> read_json_string(const std::string& json, const std::string& key, std::size_t from = 0) {
  const std::string marker = "\"" + key + "\":\"";
  const std::size_t start = json.find(marker, from);
  if (start == std::string::npos) {
    return std::nullopt;
  }

  std::size_t pos = start + marker.size();
  std::string value;
  bool escaped = false;
  for (; pos < json.size(); ++pos) {
    const char ch = json[pos];
    if (escaped) {
      value.push_back('\\');
      value.push_back(ch);
      escaped = false;
      continue;
    }
    if (ch == '\\') {
      escaped = true;
      continue;
    }
    if (ch == '"') {
      return unescape_json_string(value);
    }
    value.push_back(ch);
  }
  return std::nullopt;
}

std::optional<std::int64_t> read_json_int64(const std::string& json, const std::string& key) {
  const std::string marker = "\"" + key + "\":";
  const std::size_t start = json.find(marker);
  if (start == std::string::npos) {
    return std::nullopt;
  }

  std::size_t pos = start + marker.size();
  std::string digits;
  while (pos < json.size() && (json[pos] == '-' || (json[pos] >= '0' && json[pos] <= '9'))) {
    digits.push_back(json[pos]);
    ++pos;
  }
  if (digits.empty()) {
    return std::nullopt;
  }
  return std::stoll(digits);
}

std::map<std::string, std::string> read_data_object(const std::string& json) {
  std::map<std::string, std::string> data;
  const std::string marker = "\"data\":{";
  std::size_t pos = json.find(marker);
  if (pos == std::string::npos) {
    return data;
  }
  pos += marker.size();

  while (pos < json.size() && json[pos] != '}') {
    if (json[pos] == ',') {
      ++pos;
      continue;
    }
    if (json[pos] != '"') {
      break;
    }
    const std::size_t key_start = pos + 1;
    const std::size_t key_end = json.find("\":\"", key_start);
    if (key_end == std::string::npos) {
      break;
    }
    const std::string key = unescape_json_string(json.substr(key_start, key_end - key_start));
    pos = key_end + 3;

    std::string value;
    bool escaped = false;
    for (; pos < json.size(); ++pos) {
      const char ch = json[pos];
      if (escaped) {
        value.push_back('\\');
        value.push_back(ch);
        escaped = false;
        continue;
      }
      if (ch == '\\') {
        escaped = true;
        continue;
      }
      if (ch == '"') {
        ++pos;
        break;
      }
      value.push_back(ch);
    }
    data[key] = unescape_json_string(value);
  }
  return data;
}

std::optional<Event> parse_event_line(const std::string& line) {
  const auto ts = read_json_int64(line, "ts");
  const auto host = read_json_string(line, "host");
  const auto type = read_json_string(line, "event");
  if (!ts || !host || !type) {
    return std::nullopt;
  }
  return Event{*ts, *host, *type, read_data_object(line)};
}
}

std::vector<Event> OfflineQueue::drain() const {
  std::vector<Event> events;
  std::ifstream in(path_);
  if (!in) {
    return events;
  }

  std::string line;
  while (std::getline(in, line)) {
    if (auto event = parse_event_line(line)) {
      events.push_back(*event);
    }
  }
  in.close();
  std::remove(path_.string().c_str());
  return events;
}
// Project version: SentinelX V1.6







