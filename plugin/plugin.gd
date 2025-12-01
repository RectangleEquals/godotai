@tool
extends EditorPlugin

# Reference to the C++ GodotAI singleton
var godotai: EditorPlugin = null

func _enter_tree():
	# The C++ EditorPlugin will be automatically loaded
	# We can access it through the plugin system if needed
	print("GodotAI: GDScript plugin wrapper loaded")
	
	# Note: The actual EditorPlugin is the C++ GodotAI class
	# This GDScript file is just the plugin.cfg entry point

func _exit_tree():
	print("GodotAI: GDScript plugin wrapper unloaded")