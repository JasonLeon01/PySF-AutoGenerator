#pragma once

#include "SFML/System.hpp"
#include "SFML/Window.hpp"
#include "SFML/Graphics.hpp"
#include "SFML/Audio.hpp"
#include "SFML/Network.hpp"
#include "string_utils.hpp"
#include "wrap_utils.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <vector>
#include <filesystem>

#ifdef _WIN32
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
#endif

namespace py = pybind11;

class WindowHandle {
public:
    explicit WindowHandle(std::uintptr_t nativeHandle);

    static WindowHandle fromNative(sf::WindowHandle nativeHandle);

    sf::WindowHandle getNativeHandle() const;
    std::uintptr_t toInteger() const;

    operator sf::WindowHandle() const;

private:
    explicit WindowHandle(sf::WindowHandle nativeHandle, int);

    sf::WindowHandle nativeHandle;
};

template <typename T>
void add_copy_support(py::class_<T>& cls);

template<typename T>
void hash_combine(std::size_t& seed, const T& val);

#include "utils.inl"
