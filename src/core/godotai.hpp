#ifndef GODOTAI_HPP
#define GODOTAI_HPP

#include <godot_cpp/classes/editor_plugin.hpp>

namespace godot {

/**
 * GodotAI - Main EditorPlugin for AI-powered project management
 * 
 * This plugin provides AI assistance through Claude Desktop via MCP,
 * enabling file operations, git integration, and project management.
 */
class GodotAI : public EditorPlugin {
    GDCLASS(GodotAI, EditorPlugin)

private:
    // Will add: HTTPServer, ProjectState, etc. in later phases
    static GodotAI* singleton_instance;
    bool server_running = false;
    int server_port = 8765;

protected:
    static void _bind_methods();

public:
    GodotAI();
    ~GodotAI();

    // EditorPlugin overrides
    void _enter_tree() override;
    void _exit_tree() override;
    
    static GodotAI* get_singleton();

    // Server control (stub for now)
    void start_server(int port = 8765);
    void stop_server();
    bool is_server_running() const;
};

} // namespace godot

#endif // GODOTAI_HPP