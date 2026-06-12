#include "utils.hpp"
#include <type_traits>

namespace {
template <typename Handle>
Handle integerToWindowHandle(std::uintptr_t nativeHandle) {
    if constexpr (std::is_pointer_v<Handle>) {
        return reinterpret_cast<Handle>(nativeHandle);
    } else {
        return static_cast<Handle>(nativeHandle);
    }
}

template <typename Handle>
std::uintptr_t windowHandleToInteger(Handle nativeHandle) {
    if constexpr (std::is_pointer_v<Handle>) {
        return reinterpret_cast<std::uintptr_t>(nativeHandle);
    } else {
        return static_cast<std::uintptr_t>(nativeHandle);
    }
}
}

#ifndef __APPLE__
WindowHandle::WindowHandle(std::uintptr_t nativeHandle) {
    this->nativeHandle = integerToWindowHandle<sf::WindowHandle>(nativeHandle);
}
#endif

WindowHandle::WindowHandle(sf::WindowHandle nativeHandle, int) : nativeHandle(nativeHandle) {
}

WindowHandle WindowHandle::fromNative(sf::WindowHandle nativeHandle) {
    return WindowHandle(nativeHandle, 0);
}

sf::WindowHandle WindowHandle::getNativeHandle() const {
    return nativeHandle;
}

std::uintptr_t WindowHandle::toInteger() const {
    return windowHandleToInteger(nativeHandle);
}

WindowHandle::operator sf::WindowHandle() const {
    return nativeHandle;
}
