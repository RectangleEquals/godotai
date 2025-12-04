// register_types.cpp
// GDExtension registration implementation for GDAI

#include "register_types.hpp"

#include <godot_cpp/classes/engine.hpp>
#include <godot_cpp/core/defs.hpp>
#include <godot_cpp/godot.hpp>
#include <godot_cpp/variant/utility_functions.hpp>

#include "godotai.hpp"

using namespace godot;

void initialize_gdai_module(ModuleInitializationLevel p_level) {
    if (p_level != MODULE_INITIALIZATION_LEVEL_EDITOR) {
        return;
    }

    // TODO: Register GDAI classes here
    // Example: ClassDB::register_class<GDAIPlugin>();
    // IMPORTANT: Only editor classes should be registered here
    // This plugin should NOT be active in exported games
    ClassDB::register_class<GodotAI>();
    
    // For now, just log that we've initialized
    UtilityFunctions::print("GDAI: Module initialized (minimal stub)");
}

void uninitialize_gdai_module(ModuleInitializationLevel p_level) {
    if (p_level != MODULE_INITIALIZATION_LEVEL_EDITOR) {
        return;
    }

    // TODO: Cleanup if needed
}

extern "C" {
    // Initialization entry point
    GDExtensionBool GDE_EXPORT gdai_library_init(
        GDExtensionInterfaceGetProcAddress p_get_proc_address,
        GDExtensionClassLibraryPtr p_library,
        GDExtensionInitialization *r_initialization
    ) {
        GDExtensionBinding::InitObject init_obj(p_get_proc_address, p_library, r_initialization);

        init_obj.register_initializer(initialize_gdai_module);
        init_obj.register_terminator(uninitialize_gdai_module);
        init_obj.set_minimum_library_initialization_level(MODULE_INITIALIZATION_LEVEL_EDITOR);

        return init_obj.init();
    }
}