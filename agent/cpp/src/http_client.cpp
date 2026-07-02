#include "http_client.hpp"

#include <iostream>
#include <sstream>
#include <utility>

#ifdef _WIN32
#ifndef UNICODE
#define UNICODE
#endif
#include <windows.h>
#include <winhttp.h>
#endif

HttpClient::HttpClient(std::string gateway_url) : gateway_url_(std::move(gateway_url)) {}

#ifdef _WIN32
namespace {
std::wstring widen(const std::string& value) {
  if (value.empty()) {
    return {};
  }
  const int size = MultiByteToWideChar(CP_UTF8, 0, value.data(), static_cast<int>(value.size()), nullptr, 0);
  std::wstring result(size, L'\0');
  MultiByteToWideChar(CP_UTF8, 0, value.data(), static_cast<int>(value.size()), result.data(), size);
  return result;
}

struct ParsedUrl {
  std::wstring host;
  std::wstring path;
  INTERNET_PORT port;
  bool tls;
};

bool parse_url(const std::string& url, ParsedUrl& parsed) {
  std::wstring wide_url = widen(url);
  URL_COMPONENTS parts{};
  parts.dwStructSize = sizeof(parts);
  parts.dwSchemeLength = static_cast<DWORD>(-1);
  parts.dwHostNameLength = static_cast<DWORD>(-1);
  parts.dwUrlPathLength = static_cast<DWORD>(-1);
  parts.dwExtraInfoLength = static_cast<DWORD>(-1);

  if (!WinHttpCrackUrl(wide_url.c_str(), static_cast<DWORD>(wide_url.size()), 0, &parts)) {
    return false;
  }

  parsed.host.assign(parts.lpszHostName, parts.dwHostNameLength);
  parsed.path.assign(parts.lpszUrlPath, parts.dwUrlPathLength);
  if (parts.dwExtraInfoLength > 0) {
    parsed.path.append(parts.lpszExtraInfo, parts.dwExtraInfoLength);
  }
  if (parsed.path.empty()) {
    parsed.path = L"/";
  }
  parsed.port = parts.nPort;
  parsed.tls = parts.nScheme == INTERNET_SCHEME_HTTPS;
  return !parsed.host.empty();
}
}
#endif

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

#ifdef _WIN32
  ParsedUrl url{};
  if (!parse_url(gateway_url_, url)) {
    std::cerr << "invalid gateway url: " << gateway_url_ << "\n";
    return false;
  }

  HINTERNET session = WinHttpOpen(
      L"SentinelX-Agent/0.1",
      WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
      WINHTTP_NO_PROXY_NAME,
      WINHTTP_NO_PROXY_BYPASS,
      0);
  if (!session) {
    return false;
  }

  HINTERNET connect = WinHttpConnect(session, url.host.c_str(), url.port, 0);
  if (!connect) {
    WinHttpCloseHandle(session);
    return false;
  }

  const DWORD flags = url.tls ? WINHTTP_FLAG_SECURE : 0;
  HINTERNET request = WinHttpOpenRequest(
      connect,
      L"POST",
      url.path.c_str(),
      nullptr,
      WINHTTP_NO_REFERER,
      WINHTTP_DEFAULT_ACCEPT_TYPES,
      flags);
  if (!request) {
    WinHttpCloseHandle(connect);
    WinHttpCloseHandle(session);
    return false;
  }

  const std::string payload = body.str();
  const wchar_t headers[] = L"Content-Type: application/json\r\n";
  const BOOL sent = WinHttpSendRequest(
      request,
      headers,
      static_cast<DWORD>(-1L),
      const_cast<char*>(payload.data()),
      static_cast<DWORD>(payload.size()),
      static_cast<DWORD>(payload.size()),
      0);
  const BOOL received = sent ? WinHttpReceiveResponse(request, nullptr) : FALSE;

  DWORD status = 0;
  DWORD status_size = sizeof(status);
  if (received) {
    WinHttpQueryHeaders(
        request,
        WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
        WINHTTP_HEADER_NAME_BY_INDEX,
        &status,
        &status_size,
        WINHTTP_NO_HEADER_INDEX);
  }

  WinHttpCloseHandle(request);
  WinHttpCloseHandle(connect);
  WinHttpCloseHandle(session);
  return received && status >= 200 && status < 300;
#else
  std::cout << "POST " << gateway_url_ << "\n" << body.str() << "\n";
  return true;
#endif
}
// Project version: SentinelX V1.2
