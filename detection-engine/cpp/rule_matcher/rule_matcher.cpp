#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>

namespace {

constexpr std::size_t MAX_FIELD_BYTES = 1024 * 1024;

std::string lower_copy(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return value;
}

bool contains_any(const std::string& haystack, const std::string& needles) {
    if (needles.empty() || needles == "-") {
        return true;
    }
    std::size_t start = 0;
    while (start <= needles.size()) {
        const auto end = needles.find('\x1f', start);
        const auto token = needles.substr(start, end == std::string::npos ? std::string::npos : end - start);
        if (!token.empty() && haystack.find(lower_copy(token)) != std::string::npos) {
            return true;
        }
        if (end == std::string::npos) break;
        start = end + 1;
    }
    return false;
}

}  // namespace

int main(int argc, char**) {
    if (argc != 1) return 2;
    std::string rule_event;
    std::string event_name;
    std::string expected_process_raw;
    std::string actual_process_raw;
    std::string needles;
    std::string hay_raw;
    if (!std::getline(std::cin, rule_event) ||
        !std::getline(std::cin, event_name) ||
        !std::getline(std::cin, expected_process_raw) ||
        !std::getline(std::cin, actual_process_raw) ||
        !std::getline(std::cin, needles) ||
        !std::getline(std::cin, hay_raw)) {
        return 2;
    }
    if (rule_event.size() > MAX_FIELD_BYTES ||
        event_name.size() > MAX_FIELD_BYTES ||
        expected_process_raw.size() > MAX_FIELD_BYTES ||
        actual_process_raw.size() > MAX_FIELD_BYTES ||
        needles.size() > MAX_FIELD_BYTES ||
        hay_raw.size() > MAX_FIELD_BYTES) {
        return 3;
    }
    const std::string expected_process = lower_copy(expected_process_raw);
    const std::string actual_process = lower_copy(actual_process_raw);
    const std::string hay = lower_copy(hay_raw);

    if (rule_event != "-" && !rule_event.empty() && rule_event != event_name) {
        std::cout << "0\n";
        return 0;
    }
    if (expected_process != "-" && !expected_process.empty() && expected_process != actual_process) {
        std::cout << "0\n";
        return 0;
    }
    if (!contains_any(hay, needles)) {
        std::cout << "0\n";
        return 0;
    }
    std::string pair;
    while (std::getline(std::cin, pair)) {
        if (pair.size() > MAX_FIELD_BYTES) return 3;
        const auto sep = pair.find('\x1f');
        if (sep != std::string::npos && lower_copy(pair.substr(0, sep)) != lower_copy(pair.substr(sep + 1))) {
            std::cout << "0\n";
            return 0;
        }
    }
    std::cout << "1\n";
    return 0;
}
// Project version: SentinelX V1.6

