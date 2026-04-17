#pragma once

#include "SFML/System.hpp"
#include <vector>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

sf::String toSFString(const std::string& str);

std::string toUTF8String(const sf::String& str);

std::vector<sf::String> toVectorSFString(const std::vector<std::string>& stringVec);

std::vector<std::string> toVectorUTF8String(const std::vector<sf::String>& sfStringVec);

std::vector<std::vector<sf::String>> toVectorVectorSFString(const std::vector<std::vector<std::string>>& stringVecVec);

std::vector<std::vector<std::string>> toVectorVectorUTF8String(const std::vector<std::vector<sf::String>>& sfStringVecVec);

template <typename Class>
void def_string_property(py::class_<Class> &cls, const char *name, sf::String Class::*field, const std::string& docstring = "");

template <typename Class, typename Field>
void def_string_property_readonly(py::class_<Class> &cls, const char *name, Field field, const std::string& docstring = "");

template <typename Class>
void def_vector_string_property(py::class_<Class> &cls, const char *name, std::vector<sf::String> Class::*field, const std::string& docstring = "");

template <typename Class, typename Field>
void def_vector_string_property_readonly(py::class_<Class> &cls, const char *name, Field field, const std::string& docstring = "");

template <typename Class>
void def_vector_vector_string_property(py::class_<Class> &cls, const char *name, std::vector<std::vector<sf::String>> Class::*field, const std::string& docstring = "") ;

template <typename Class, typename Field>
void def_vector_vector_string_property_readonly(py::class_<Class> &cls, const char *name, Field field, const std::string& docstring = "");

#include "string_utils.inl"
