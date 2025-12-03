cmake_minimum_required(VERSION 3.13)

# ============================================================================
# GodotAI - AI-Powered Editor Extension for Godot
# ============================================================================
# This CMake build system leverages godot-cpp's CMake infrastructure to build
# the GodotAI GDExtension with all its dependencies.
# ============================================================================

project(
    GodotAI
    VERSION 0.1.0
    DESCRIPTION "AI-powered editor extension for Godot"
    LANGUAGES CXX
)

# Prevent in-source builds
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_BINARY_DIR)
    message(FATAL_ERROR "In-source builds are not allowed. Please create a separate build directory.")
endif()

# ============================================================================
# Build Options
# ============================================================================

set(GODOTAI_BUILD_TYPE "template_release" CACHE STRING
    "Build type: template_debug, template_release, or editor")
set_property(CACHE GODOTAI_BUILD_TYPE PROPERTY STRINGS
    "template_debug;template_release;editor")

set(GODOTAI_PRECISION "single" CACHE STRING
    "Floating-point precision: single or double")
set_property(CACHE GODOTAI_PRECISION PROPERTY STRINGS "single;double")

option(GODOTAI_USE_HOT_RELOAD
    "Enable hot reload support for development" ON)

option(GODOTAI_ENABLE_TESTING
    "Enable test targets" OFF)

option(GODOTAI_DEV_BUILD
    "Enable developer build with extra debugging" OFF)

# ============================================================================
# Platform Detection
# ============================================================================

if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    set(GODOTAI_PLATFORM "windows")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set(GODOTAI_PLATFORM "linux")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    set(GODOTAI_PLATFORM "macos")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Android")
    set(GODOTAI_PLATFORM "android")
elseif(CMAKE_SYSTEM_NAME STREQUAL "iOS")
    set(GODOTAI_PLATFORM "ios")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Emscripten")
    set(GODOTAI_PLATFORM "web")
else()
    message(FATAL_ERROR "Unsupported platform: ${CMAKE_SYSTEM_NAME}")
endif()

message(STATUS "GodotAI Platform: ${GODOTAI_PLATFORM}")
message(STATUS "GodotAI Build Type: ${GODOTAI_BUILD_TYPE}")
message(STATUS "GodotAI Precision: ${GODOTAI_PRECISION}")

# ============================================================================
# godot-cpp Configuration
# ============================================================================

# Configure godot-cpp before adding it
set(GODOTCPP_TARGET ${GODOTAI_BUILD_TYPE} CACHE STRING "" FORCE)
set(GODOTCPP_PRECISION ${GODOTAI_PRECISION} CACHE STRING "" FORCE)
set(GODOTCPP_USE_HOT_RELOAD ${GODOTAI_USE_HOT_RELOAD} CACHE BOOL "" FORCE)
set(GODOTCPP_DEV_BUILD ${GODOTAI_DEV_BUILD} CACHE BOOL "" FORCE)
set(GODOTCPP_SYSTEM_HEADERS ON CACHE BOOL "" FORCE)
set(GODOTCPP_WARNING_AS_ERROR OFF CACHE BOOL "" FORCE)

# Add godot-cpp as a subdirectory
add_subdirectory(third_party/godot-cpp EXCLUDE_FROM_ALL)

# Get the generated suffix from godot-cpp for consistency
get_target_property(GODOTCPP_SUFFIX godot-cpp GODOTCPP_SUFFIX)

# ============================================================================
# Third-Party Dependencies
# ============================================================================

# libgit2 - Git operations library
set(LIBGIT2_LIB_DIR "${CMAKE_SOURCE_DIR}/build_ext_libs")
set(LIBGIT2_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/third_party/libgit2/include")

if(EXISTS "${LIBGIT2_INCLUDE_DIR}")
    message(STATUS "Found libgit2 include directory")
    
    # Find the library file
    if(WIN32)
        set(LIBGIT2_LIB_NAME "git2.lib")
    else()
        set(LIBGIT2_LIB_NAME "libgit2.a")
    endif()
    
    if(EXISTS "${LIBGIT2_LIB_DIR}/${LIBGIT2_LIB_NAME}")
        message(STATUS "Found libgit2 library: ${LIBGIT2_LIB_DIR}/${LIBGIT2_LIB_NAME}")
        set(GODOTAI_HAS_LIBGIT2 ON)
    else()
        message(WARNING "libgit2 library not found. Run: python setup.py -> build-libgit2")
        set(GODOTAI_HAS_LIBGIT2 OFF)
    endif()
else()
    message(WARNING "libgit2 not initialized. Run: python setup.py -> init")
    set(GODOTAI_HAS_LIBGIT2 OFF)
endif()

# libhv - HTTP client/server library
set(LIBHV_LIB_DIR "${CMAKE_SOURCE_DIR}/build_ext_libs")
set(LIBHV_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/third_party/libhv/include")

if(EXISTS "${LIBHV_INCLUDE_DIR}")
    message(STATUS "Found libhv include directory")
    
    # Find the library file
    if(WIN32)
        set(LIBHV_LIB_NAME "hv_static.lib")
    else()
        set(LIBHV_LIB_NAME "libhv_static.a")
    endif()
    
    if(EXISTS "${LIBHV_LIB_DIR}/${LIBHV_LIB_NAME}")
        message(STATUS "Found libhv library: ${LIBHV_LIB_DIR}/${LIBHV_LIB_NAME}")
        set(GODOTAI_HAS_LIBHV ON)
    else()
        message(WARNING "libhv library not found. Run: python setup.py -> build-libhv")
        set(GODOTAI_HAS_LIBHV OFF)
    endif()
else()
    message(WARNING "libhv not initialized. Run: python setup.py -> init")
    set(GODOTAI_HAS_LIBHV OFF)
endif()

# ============================================================================
# GodotAI Source Files
# ============================================================================

file(GLOB_RECURSE GODOTAI_SOURCES
    CONFIGURE_DEPENDS
    "${CMAKE_SOURCE_DIR}/src/*.cpp"
)

# Exclude test files unless testing is enabled
if(NOT GODOTAI_ENABLE_TESTING)
    list(FILTER GODOTAI_SOURCES EXCLUDE REGEX ".*test.*\\.cpp$")
endif()

# ============================================================================
# GodotAI Library Target
# ============================================================================

add_library(${PROJECT_NAME} SHARED ${GODOTAI_SOURCES})

# Set C++ standard (must be at least C++17 for godot-cpp)
set_target_properties(${PROJECT_NAME} PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    POSITION_INDEPENDENT_CODE ON
)

# Output naming to match godot-cpp convention
set_target_properties(${PROJECT_NAME} PROPERTIES
    PREFIX "lib"
    OUTPUT_NAME "godotai${GODOTCPP_SUFFIX}"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Include directories
target_include_directories(${PROJECT_NAME}
    PRIVATE
        "${CMAKE_SOURCE_DIR}/src"
)

# Link godot-cpp
target_link_libraries(${PROJECT_NAME}
    PRIVATE
        godot::cpp
)

# ============================================================================
# Conditional Dependency Linking
# ============================================================================

if(GODOTAI_HAS_LIBGIT2)
    target_include_directories(${PROJECT_NAME}
        PRIVATE
            "${LIBGIT2_INCLUDE_DIR}"
    )
    
    target_link_libraries(${PROJECT_NAME}
        PRIVATE
            "${LIBGIT2_LIB_DIR}/${LIBGIT2_LIB_NAME}"
    )
    
    target_compile_definitions(${PROJECT_NAME}
        PRIVATE
            GODOTAI_HAS_LIBGIT2
    )
    
    message(STATUS "Enabled libgit2 integration")
endif()

if(GODOTAI_HAS_LIBHV)
    target_include_directories(${PROJECT_NAME}
        PRIVATE
            "${LIBHV_INCLUDE_DIR}"
    )
    
    target_link_libraries(${PROJECT_NAME}
        PRIVATE
            "${LIBHV_LIB_DIR}/${LIBHV_LIB_NAME}"
    )
    
    target_compile_definitions(${PROJECT_NAME}
        PRIVATE
            GODOTAI_HAS_LIBHV
    )
    
    message(STATUS "Enabled libhv integration")
endif()

# ============================================================================
# Platform-Specific Configuration
# ============================================================================

if(WIN32)
    # Windows-specific libraries
    target_link_libraries(${PROJECT_NAME}
        PRIVATE
            ws2_32  # Winsock for networking
            winhttp # HTTP client (if needed)
    )
    
    # Export all symbols for GDExtension
    set_target_properties(${PROJECT_NAME} PROPERTIES
        WINDOWS_EXPORT_ALL_SYMBOLS ON
    )
    
elseif(UNIX AND NOT APPLE)
    # Linux-specific libraries
    target_link_libraries(${PROJECT_NAME}
        PRIVATE
            pthread
            dl
    )
    
elseif(APPLE)
    # macOS-specific configuration
    set_target_properties(${PROJECT_NAME} PROPERTIES
        MACOSX_RPATH ON
        BUILD_WITH_INSTALL_RPATH ON
        INSTALL_NAME_DIR "@rpath"
    )
endif()

# ============================================================================
# Compiler Warnings
# ============================================================================

if(MSVC)
    target_compile_options(${PROJECT_NAME} PRIVATE
        /W4           # Warning level 4
        /WX-          # Don't treat warnings as errors (can enable later)
        /permissive-  # Standards conformance
    )
else()
    target_compile_options(${PROJECT_NAME} PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        -Wno-unused-parameter
    )
endif()

# ============================================================================
# Installation
# ============================================================================

# Install the library to plugin/bin directory for Godot
install(TARGETS ${PROJECT_NAME}
    LIBRARY DESTINATION "${CMAKE_SOURCE_DIR}/plugin/bin"
    RUNTIME DESTINATION "${CMAKE_SOURCE_DIR}/plugin/bin"
)

# ============================================================================
# Build Summary
# ============================================================================

message(STATUS "")
message(STATUS "=== GodotAI Build Configuration ===")
message(STATUS "Platform: ${GODOTAI_PLATFORM}")
message(STATUS "Build Type: ${GODOTAI_BUILD_TYPE}")
message(STATUS "Precision: ${GODOTAI_PRECISION}")
message(STATUS "Hot Reload: ${GODOTAI_USE_HOT_RELOAD}")
message(STATUS "Dev Build: ${GODOTAI_DEV_BUILD}")
message(STATUS "libgit2: ${GODOTAI_HAS_LIBGIT2}")
message(STATUS "libhv: ${GODOTAI_HAS_LIBHV}")
message(STATUS "Output: libgodotai${GODOTCPP_SUFFIX}")
message(STATUS "===================================")
message(STATUS "")