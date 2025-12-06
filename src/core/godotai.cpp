#include "godotai.hpp"
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/utility_functions.hpp>

using namespace godot;

GodotAI *GodotAI::singleton_instance = nullptr;

void GodotAI::_bind_methods() {
    // Bind methods for GDScript access
    ClassDB::bind_static_method("GodotAI", D_METHOD("get"), &GodotAI::get_singleton);
    ClassDB::bind_method(D_METHOD("start_server", "port"), &GodotAI::start_server, DEFVAL(8765));
    ClassDB::bind_method(D_METHOD("stop_server"), &GodotAI::stop_server);
    ClassDB::bind_method(D_METHOD("is_server_running"), &GodotAI::is_server_running);
}

GodotAI::GodotAI() {
    // Constructor
    UtilityFunctions::print("GodotAI: Constructor called");
}

GodotAI::~GodotAI() {
    // Destructor
    UtilityFunctions::print("GodotAI: Destructor called");
}

void GodotAI::_enter_tree() {
    // Called when the plugin is activated
    UtilityFunctions::print("GodotAI: Plugin loaded and activated");
    
    // Auto-start server (stub for now)
    start_server(server_port);
}

void GodotAI::_exit_tree() {
    // Called when the plugin is deactivated
    stop_server();
    UtilityFunctions::print("GodotAI: Plugin deactivated");
}

GodotAI *godot::GodotAI::get_singleton()
{
    if (singleton_instance == nullptr)
        singleton_instance = memnew(GodotAI);
    
    return singleton_instance;
}

void GodotAI::start_server(int port) {
    if (server_running) {
        UtilityFunctions::print("GodotAI: Server already running");
        return;
    }
    
    server_port = port;
    server_running = true;
    
    // TODO: Actually start HTTP server in Phase 5
    UtilityFunctions::print("GodotAI: Server started (stub) on port ", port);
}

void GodotAI::stop_server() {
    if (!server_running) {
        return;
    }
    
    // TODO: Actually stop HTTP server in Phase 4
    server_running = false;
    UtilityFunctions::print("GodotAI: Server stopped");
}

bool GodotAI::is_server_running() const {
    return server_running;
}