cmake_minimum_required(VERSION 3.8...3.27)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
project ("pysf")
set(SFML_DIR ${CMAKE_SOURCE_DIR}/SFML)
set(PYBIND11_DIR ${CMAKE_SOURCE_DIR}/pybind11)
find_package(Python3 3.10.0 EXACT REQUIRED COMPONENTS Interpreter Development)
if(NOT Python3_FOUND)
    message(FATAL_ERROR "Python 3.10.0 not found")
endif()
get_filename_component(PYTHON_DIR "${Python3_EXECUTABLE}" DIRECTORY)
message(STATUS "Python Dir: ${PYTHON_DIR}")
message(STATUS "Python include dirs: ${Python3_INCLUDE_DIRS}")
message(STATUS "Python libraries: ${Python3_LIBRARIES}")
add_subdirectory(${SFML_DIR})
if (CMAKE_SYSTEM_NAME STREQUAL "Windows")
    if (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        include_directories(${SFML_DIR}/include)
        link_directories(${PYTHON_DIR}/libs)
    endif()
    set(TARGET_SUFFIX ".pyd")
elseif (CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    set(FETCHCONTENT_QUIET OFF)
    set(TARGET_SUFFIX ".so")
else()
    message(FATAL_ERROR "Unsupported platform: ${CMAKE_SYSTEM_NAME}")
endif()
add_subdirectory(${PYBIND11_DIR})
include_directories(${PYTHON_DIR}/include)
include_directories(${CMAKE_SOURCE_DIR}/include)
include_directories(${CMAKE_SOURCE_DIR}/output/include)
set(CMAKE_BUILD_TYPE Release)
if (CMAKE_SYSTEM_NAME STREQUAL "Windows" AND MSVC)
    set(CMAKE_CXX_FLAGS_RELEASE "/O2 /DNDEBUG")
else()
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -s -flto")
endif()
add_library(pysf SHARED
    "src/A_utils.cpp"
    "src/B_bind_Vector.cpp"
    "src/C_bind_Rect.cpp"
    "src/D_bind_Matrix.cpp"
    "output/src/Graphics/bind_CoordinateType.cpp"
    "output/src/Graphics/bind_BlendMode.cpp"
    "output/src/Window/bind_Sensor.cpp"
    "output/src/Audio/bind_SoundChannel.cpp"
    "output/src/Audio/bind_PlaybackDevice.cpp"
    "output/src/System/bind_Angle.cpp"
    "output/src/Graphics/bind_PrimitiveType.cpp"
    "output/src/Window/bind_ContextSettings.cpp"
    "output/src/System/bind_String.cpp"
    "output/src/Graphics/bind_Color.cpp"
    "output/src/System/bind_InputStream.cpp"
    "output/src/Network/bind_Packet.cpp"
    "output/src/Window/bind_WindowHandle.cpp"
    "output/src/Window/bind_WindowEnums.cpp"
    "output/src/Network/bind_Socket.cpp"
    "output/src/Graphics/bind_StencilMode.cpp"
    "output/src/System/bind_Time.cpp"
    "output/src/Audio/bind_SoundRecorder.cpp"
    "output/src/Audio/bind_SoundFileReader.cpp"
    "output/src/Audio/bind_SoundFileWriter.cpp"
    "output/src/Graphics/bind_Transform.cpp"
    "output/src/Window/bind_Cursor.cpp"
    "output/src/Window/bind_Context.cpp"
    "output/src/Audio/bind_SoundSource.cpp"
    "output/src/Graphics/bind_Glyph.cpp"
    "output/src/Window/bind_VideoMode.cpp"
    "output/src/Audio/bind_Listener.cpp"
    "output/src/Window/bind_Touch.cpp"
    "output/src/Window/bind_Mouse.cpp"
    "output/src/Window/bind_Joystick.cpp"
    "output/src/Window/bind_Clipboard.cpp"
    "output/src/Window/bind_Keyboard.cpp"
    "output/src/Graphics/bind_Shader.cpp"
    "output/src/Graphics/bind_Image.cpp"
    "output/src/Graphics/bind_Vertex.cpp"
    "output/src/System/bind_MemoryInputStream.cpp"
    "output/src/System/bind_FileInputStream.cpp"
    "output/src/Audio/bind_SoundBuffer.cpp"
    "output/src/System/bind_Sleep.cpp"
    "output/src/System/bind_Clock.cpp"
    "output/src/Network/bind_SocketSelector.cpp"
    "output/src/Network/bind_IpAddress.cpp"
    "output/src/Audio/bind_InputSoundFile.cpp"
    "output/src/Audio/bind_OutputSoundFile.cpp"
    "output/src/Graphics/bind_Transformable.cpp"
    "output/src/Graphics/bind_View.cpp"
    "output/src/Graphics/bind_RenderStates.cpp"
    "output/src/Audio/bind_SoundStream.cpp"
    "output/src/Audio/bind_Sound.cpp"
    "output/src/Window/bind_Event.cpp"
    "output/src/Graphics/bind_Texture.cpp"
    "output/src/Audio/bind_SoundBufferRecorder.cpp"
    "output/src/Network/bind_UdpSocket.cpp"
    "output/src/Network/bind_TcpSocket.cpp"
    "output/src/Network/bind_TcpListener.cpp"
    "output/src/Graphics/bind_RenderTarget.cpp"
    "output/src/Graphics/bind_Drawable.cpp"
    "output/src/Audio/bind_Music.cpp"
    "output/src/Window/bind_WindowBase.cpp"
    "output/src/Graphics/bind_Font.cpp"
    "output/src/Network/bind_Ftp.cpp"
    "output/src/Network/bind_Http.cpp"
    "output/src/Graphics/bind_RenderTexture.cpp"
    "output/src/Graphics/bind_VertexArray.cpp"
    "output/src/Graphics/bind_VertexBuffer.cpp"
    "output/src/Graphics/bind_Sprite.cpp"
    "output/src/Window/bind_Window.cpp"
    "output/src/Graphics/bind_Shape.cpp"
    "output/src/Graphics/bind_Text.cpp"
    "output/src/Graphics/bind_RenderWindow.cpp"
    "output/src/Graphics/bind_CircleShape.cpp"
    "output/src/Graphics/bind_ConvexShape.cpp"
    "output/src/Graphics/bind_RectangleShape.cpp"
    "output/main.cpp"
)
set_target_properties(pysf PROPERTIES
    PREFIX ""
    SUFFIX ${TARGET_SUFFIX}
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)
if(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    set_target_properties(pysf PROPERTIES
        INSTALL_RPATH "@loader_path"
        BUILD_WITH_INSTALL_RPATH TRUE
        MACOSX_RPATH TRUE
    )
endif()
target_link_libraries(pysf PRIVATE
    sfml-system
    sfml-window
    sfml-graphics
    sfml-audio
    sfml-network
    Python3::Python
    pybind11::module
)
if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    if (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        target_link_libraries(pysf PRIVATE
            -Wl,-rpath=${PYTHON_DIR}/libs
        )
        add_custom_command(TARGET pysf POST_BUILD
            COMMAND ${CMAKE_STRIP} --strip-all $<TARGET_FILE:pysf>
        )
    endif()
elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    add_custom_command(TARGET pysf POST_BUILD
        COMMAND ${CMAKE_STRIP} -x $<TARGET_FILE:pysf>
    )
endif()
