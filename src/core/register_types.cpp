#ifndef GODOTAI_REGISTER_TYPES_HPP
#define GODOTAI_REGISTER_TYPES_HPP

#include <godot_cpp/core/class_db.hpp>

using namespace godot;

void initialize_godotai_module(ModuleInitializationLevel p_level);
void uninitialize_godotai_module(ModuleInitializationLevel p_level);

#endif // GODOTAI_REGISTER_TYPES_HPP