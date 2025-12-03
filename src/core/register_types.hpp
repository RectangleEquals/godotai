#ifndef GODOTAI_REGISTER_TYPES_HPP
#define GODOTAI_REGISTER_TYPES_HPP

#include <godot_cpp/core/class_db.hpp>

void initialize_godotai_module(godot::ModuleInitializationLevel p_level);
void uninitialize_godotai_module(godot::ModuleInitializationLevel p_level);

#endif // GODOTAI_REGISTER_TYPES_HPP