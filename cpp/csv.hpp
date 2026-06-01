#pragma once
#include <string>
#include <vector>
#include <unordered_map>

std::vector<std::string> split_csv_line(const std::string& line);
std::vector<std::unordered_map<std::string, std::string>> read_csv_dicts(const std::string& path);

double to_double(const std::string& s, double fallback = 0.0);
int to_int(const std::string& s, int fallback = 0);
