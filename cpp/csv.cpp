#include "csv.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>

std::vector<std::string> split_csv_line(const std::string& line) {
    std::vector<std::string> out;
    std::string cur;
    bool in_quotes = false;
    for (size_t i = 0; i < line.size(); ++i) {
        char c = line[i];
        if (c == '"') {
            in_quotes = !in_quotes;
        } else if (c == ',' && !in_quotes) {
            out.push_back(cur);
            cur.clear();
        } else {
            cur.push_back(c);
        }
    }
    out.push_back(cur);
    return out;
}

std::vector<std::unordered_map<std::string, std::string>> read_csv_dicts(const std::string& path) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("cannot open " + path);

    std::string line;
    if (!std::getline(f, line)) return {};

    auto header = split_csv_line(line);
    std::vector<std::unordered_map<std::string, std::string>> rows;

    while (std::getline(f, line)) {
        if (line.empty()) continue;
        auto fields = split_csv_line(line);
        std::unordered_map<std::string, std::string> row;
        for (size_t i = 0; i < header.size() && i < fields.size(); ++i) 
            row[header[i]] = fields[i];
        rows.push_back(std::move(row));
    }
    return rows;
}

double to_double(const std::string& s, double fallback) {
    try { return std::stod(s); } catch (...) { return fallback; }
}

int to_int(const std::string& s, int fallback) {
    try { return std::stoi(s); } catch (...) { return fallback; }
}
