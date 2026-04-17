#include "utils.hpp"

sf::WindowHandle handleToSFMLHandle(uintptr_t inQtHandle) {
#ifdef __APPLE__
    return handleToSFMLHandle_mac(inQtHandle);
#else
    return reinterpret_cast<sf::WindowHandle>(inQtHandle);
#endif
}
