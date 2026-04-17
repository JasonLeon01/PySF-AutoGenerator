#include "string_utils.hpp"

sf::String toSFString(const std::string& str) {
    return sf::String::fromUtf8(str.begin(), str.end());
}

std::string toUTF8String(const sf::String& str) {
    auto utf8Bytes = str.toUtf8();
    return std::string(utf8Bytes.begin(), utf8Bytes.end());
}

std::vector<sf::String> toVectorSFString(const std::vector<std::string>& stringVec) {
    std::vector<sf::String> sfStringVec;
    for (const auto& str : stringVec) {
        sfStringVec.push_back(toSFString(str));
    }
    return sfStringVec;
}

std::vector<std::string> toVectorUTF8String(const std::vector<sf::String>& sfStringVec) {
    std::vector<std::string> utf8Vec;
    for (const auto& str : sfStringVec) {
        utf8Vec.push_back(toUTF8String(str));
    }
    return utf8Vec;
}

std::vector<std::vector<sf::String>> toVectorVectorSFString(const std::vector<std::vector<std::string>>& stringVecVec) {
    std::vector<std::vector<sf::String>> sfStringVecVec;
    for (const auto& strVec : stringVecVec) {
        sfStringVecVec.push_back(toVectorSFString(strVec));
    }
    return sfStringVecVec;
}

std::vector<std::vector<std::string>> toVectorVectorUTF8String(const std::vector<std::vector<sf::String>>& sfStringVecVec) {
    std::vector<std::vector<std::string>> utf8VecVec;
    for (const auto& strVec : sfStringVecVec) {
        utf8VecVec.push_back(toVectorUTF8String(strVec));
    }
    return utf8VecVec;
}
