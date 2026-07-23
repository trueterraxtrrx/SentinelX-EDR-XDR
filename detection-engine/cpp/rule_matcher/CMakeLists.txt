cmake_minimum_required(VERSION 3.16)
project(sentinelx_rule_matcher LANGUAGES CXX)

add_executable(sentinelx-rule-matcher rule_matcher.cpp)
target_compile_features(sentinelx-rule-matcher PRIVATE cxx_std_17)
# Project version: SentinelX V1.6









