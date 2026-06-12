#include "utils.hpp"
#include <TargetConditionals.h>

#if TARGET_OS_IOS
    #include <UIKit/UIKit.h>
#else
    #include <Cocoa/Cocoa.h>
#endif

WindowHandle::WindowHandle(std::uintptr_t inQtHandle) {
    if (!inQtHandle) {
        nativeHandle = nullptr;
        return;
    }

    @autoreleasepool {
#if TARGET_OS_IOS
        UIView* view = (__bridge UIView*)reinterpret_cast<void*>(inQtHandle);
        UIWindow* window = [view window];
        nativeHandle = (__bridge sf::WindowHandle)window;
#else
        NSView* view = (__bridge NSView*)reinterpret_cast<void*>(inQtHandle);
        NSWindow* window = [view window];
        nativeHandle = (__bridge sf::WindowHandle)window;
#endif
    }
}
