#include "A_utils.hpp"
#include <Cocoa/Cocoa.h>

sf::WindowHandle handleToSFMLHandle_mac(uintptr_t inQtHandle)
{
    if (!inQtHandle)
        return nullptr;

    @autoreleasepool {
        NSView* view = (__bridge NSView*)reinterpret_cast<void*>(inQtHandle);
        NSWindow* window = [view window];
        return (__bridge sf::WindowHandle)window;
    }
}
