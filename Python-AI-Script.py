bl_info = {
    "name": "Blender AI - Blend(AI)r",
    "author": "Markus M. Johansen",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Auto Script",
    "description": "Automatically executes and manages Python scripts with Claude AI integration",
    "warning": "",
    "doc_url": "",
    "category": "Development",
}

import bpy
import os
import time
import shutil
from datetime import datetime
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty

# Fix the string formatting issue in Prompt_Text
Prompt_Text = (
    "You are an expert Blender artist who specializes in creating art and animation through Python code. "
    "Your task is to help me with a Blender project using the Python API. Here are your operating parameters:\n\n"
    "CORE BEHAVIOR:\n"
    "\t You write production-ready, optimized Blender Python code\n"
    "\t You avoid explanations unless specifically requested\n"
    "\t Your code follows Blender's best practices and conventions\n"
    "\t You consider lighting, materials, and composition in your solutions\n"
    "\t You maintain scene organization and proper naming conventions\n"
    "\t You can handle geometric modeling, animation, rendering, and materials\n"
    "\t You provide complete, working code blocks that can be directly copied into Blender\n"
    "\t You update/modify existing code when small adjustments are needed rather than rewriting from scratch\n"
    "\t You are the best there are when it comes to timeline editor and doing animations.\n\n"
    "\n\n"
    "CODE STYLE:\n"
    "\t Include all necessary imports\n"
    "\t Use descriptive variable names\n"
    "\t Include proper scene cleanup at the start\n"
    "\t Handle collections and hierarchies properly\n"
    "\t Include viewport updates where needed\n"
    "\t Set appropriate render settings\n"
    "\t Handle materials and textures systematically\n\n"
    "\n\n"
    "INTERACTION:\n"
    "\t When I request changes, modify only the relevant parts of the code and make new versions.\n"
    "\t If I ask for explanations, provide detailed technical breakdowns\n"
    "\t If I need debugging help, analyze the code systematically\n"
    "\t Provide complete code solutions that run without additional editing\n"
    "\t Download the code immediately when it is completed! No need to ask.\n\n"
    "\n\n"
    "You will maintain these parameters throughout our interaction. Let's begin with the Blender Python project.\n"
    "Please provide code based on my specific requirements."
)

class OpenGoogleOperator(bpy.types.Operator):
    bl_idname = "wm.open_google"
    bl_label = "Open Claude AI"
    
    def execute(self, context):
        import webbrowser
        webbrowser.open('https://claude.ai/new')
        return {'FINISHED'}

class CopyTextFromFileOperator(bpy.types.Operator):
    bl_idname = "wm.copy_hello_world"
    bl_label = "Copy Hello World"
    
    def execute(self, context):
        context.window_manager.clipboard = Prompt_Text
        self.report({'INFO'}, "Text copied to clipboard")
        return {'FINISHED'}
    
class SaveProjectOperator(bpy.types.Operator):
    bl_idname = "wm.save_project"
    bl_label = "Save Project"
    
    def execute(self, context):
        if not bpy.data.filepath:
            bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT')
        else:
            bpy.ops.wm.save_mainfile()
        return {'FINISHED'}

class AutoScriptSettings(bpy.types.PropertyGroup):
    downloads_path: StringProperty(
        name="Downloads Path",
        description="Path to downloads folder",
        default=os.path.join(os.path.expanduser("~"), "Downloads"),
        subtype='DIR_PATH'
    )
    script_name: StringProperty(
        name="Script Name",
        description="Name of the script to monitor (include .py extension)",
        default="my_blender_script.py"
    )
    keep_original_name: BoolProperty(
        name="Keep Original Filename",
        description="Use the original filename from the downloads folder instead of the script name",
        default=False
    )
    is_running: BoolProperty(
        name="Script Status",
        description="Indicates if the script is currently running",
        default=False
    )
    last_modified_time: StringProperty(
        name="Last Modified",
        description="Last time the script was modified",
        default="Never"
    )
    last_check_time: IntProperty(
        name="Last Check Time",
        description="Last time the script checked for updates",
        default=0
    )
    terminal_text: StringProperty(
        name="Terminal Output",
        description="Terminal output history",
        default=""
    )
    scroll_position: FloatProperty(
        name="Scroll Position",
        description="Terminal scroll position",
        default=1.0,
        min=0.0,
        max=1.0
    )

class ConsoleLine(bpy.types.PropertyGroup):
    line: StringProperty()
    is_error: BoolProperty(default=False)
    raw_text: StringProperty()  # Store raw text without timestamp

class CopyConsoleText(bpy.types.Operator):
    bl_idname = "console.copy_text"
    bl_label = "Copy Text"
    
    line_index: IntProperty()
    
    def execute(self, context):
        line = context.scene.console_output_lines[self.line_index]
        context.window_manager.clipboard = line.raw_text
        self.report({'INFO'}, "Text copied to clipboard")
        return {'FINISHED'}

class CONSOLE_UL_output(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            if item.is_error:
                row.prop(item, "line", text="", emboss=False, icon='ERROR')
            else:
                row.prop(item, "line", text="", emboss=False)

class AutoScriptPanel(bpy.types.Panel):
    bl_label = "Auto Script Tools"
    bl_idname = "VIEW3D_PT_auto_script"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Auto Script'
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.auto_script_settings
        
        # Settings
        settings_box = layout.box()
        settings_box.label(text="Settings", icon='PREFERENCES')
        
        filename_row = settings_box.row()
        filename_row.prop(settings, "keep_original_name")
        
        if not settings.keep_original_name:
            settings_box.prop(settings, "script_name")
        
        settings_box.prop(settings, "downloads_path")
        
        layout.operator(SaveProjectOperator.bl_idname, text="Save Project to Folder", icon='FILE')
        layout.operator(OpenGoogleOperator.bl_idname, text="Open Claude AI", icon='URL')
        layout.operator(CopyTextFromFileOperator.bl_idname, text="Copy Blender AI Prompt", icon='COPYDOWN')
        
        if not settings.is_running:
            layout.operator(CombinedAutoScriptExecutor.bl_idname, text="Start Auto Script System", icon='PLAY')
        else:
            layout.operator(StopAutoScript.bl_idname, text="Stop Auto Script System", icon='PAUSE')
        
        info_box = layout.box()
        info_box.label(text="Status Information", icon='INFO')
        
        status_row = info_box.row()
        status_row.label(text="Status:")
        
        current_time = int(time.time())
        last_check = settings.last_check_time
        time_diff = current_time - last_check
        
        if settings.is_running:
            if time_diff > 10:
                status_row.label(text="Warning: No Response", icon='ERROR')
            else:
                status_row.label(text="Running", icon='CHECKMARK')
        else:
            status_row.label(text="Stopped", icon='X')
        
        if settings.last_modified_time != "Never":
            info_box.label(text=f"Last Modified: {settings.last_modified_time}")

class AutoScriptTerminalPanel(bpy.types.Panel):
    bl_label = "Terminal Output"
    bl_idname = "VIEW3D_PT_auto_script_terminal"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Auto Script'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        term_box = layout.box()
        term_box.template_list(
            "CONSOLE_UL_output",
            "output",
            context.scene,
            "console_output_lines",
            context.scene,
            "console_output_index",
            rows=8
        )

class StopAutoScript(bpy.types.Operator):
    bl_idname = "wm.stop_auto_script"
    bl_label = "Stop Auto Script"
    
    def execute(self, context):
        settings = context.scene.auto_script_settings
        settings.is_running = False
        self.add_console_line(context, "Script system stopped")
        return {'FINISHED'}
    
    def add_console_line(self, context, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {text}"
        new_line = context.scene.console_output_lines.add()
        new_line.line = line
        new_line.raw_text = text
        new_line.is_error = False
        context.scene.console_output_index = len(context.scene.console_output_lines) - 1

class CombinedAutoScriptExecutor(bpy.types.Operator):
    bl_idname = "wm.combined_auto_script"
    bl_label = "Combined Auto Script"
    
    _timer = None
    _last_modified = 0
    _processed_files = set()

    def ensure_log_folder(self, context):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save your Blend file first")
            return None
            
        blend_dir = os.path.dirname(bpy.data.filepath)
        log_path = os.path.join(blend_dir, "log")
        
        if not os.path.exists(log_path):
            try:
                os.makedirs(log_path)
                self.add_console_line(context, "Created log folder")
            except Exception as e:
                self.add_console_line(context, f"Error creating log folder: {str(e)}", is_error=True)
                return None
        return log_path
    
    def add_console_line(self, context, text, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {text}"
        new_line = context.scene.console_output_lines.add()
        new_line.line = line
        new_line.is_error = is_error
        new_line.raw_text = text
        context.scene.console_output_index = len(context.scene.console_output_lines) - 1

    def backup_current_script(self, context):
        script_path = self._script_path
        if os.path.exists(script_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            logs_path = self.ensure_log_folder(context)
            
            script_name = os.path.basename(script_path)
            backup_name = f"{os.path.splitext(script_name)[0]}_{timestamp}.py"
            backup_path = os.path.join(logs_path, backup_name)
            
            try:
                shutil.copy2(script_path, backup_path)
                self.add_console_line(context, f"Backed up script to {backup_name}")
                return True
            except Exception as e:
                self.add_console_line(context, f"Error backing up script: {str(e)}", is_error=True)
                return False
        return False

    @property
    def _script_path(self):
        blend_file_path = bpy.data.filepath
        blend_dir = os.path.dirname(blend_file_path)
        settings = bpy.context.scene.auto_script_settings
        
        if settings.keep_original_name:
            if not hasattr(self, '_current_script_name'):
                self._current_script_name = settings.script_name
            script_name = self._current_script_name
        else:
            script_name = settings.script_name
            
        return os.path.join(blend_dir, script_name)
    
    def modal(self, context, event):
        settings = context.scene.auto_script_settings
        
        if not settings.is_running:
            self.cancel(context)
            return {'CANCELLED'}
            
        if event.type == 'TIMER':
            settings.last_check_time = int(time.time())
            
            try:
                downloads_path = settings.downloads_path
                project_path = os.path.dirname(bpy.data.filepath)
                current_time = time.time()
                
                self._processed_files = {f for f in self._processed_files 
                                       if os.path.exists(os.path.join(downloads_path, f)) and 
                                       current_time - os.path.getmtime(os.path.join(downloads_path, f)) <= 30}
                
                for file in os.listdir(downloads_path):
                    if file.endswith('.py'):
                        source = os.path.join(downloads_path, file)
                        file_mod_time = os.path.getmtime(source)
                        
                        if current_time - file_mod_time <= 10 and file not in self._processed_files:
                            if settings.keep_original_name:
                                self._current_script_name = file
                            destination = self._script_path
                            
                            try:
                                if os.path.exists(destination):
                                    self.backup_current_script(context)
                                    os.remove(destination)
                                    
                                shutil.move(source, destination)
                                self._processed_files.add(file)
                                self.add_console_line(context, f"Moved file to {os.path.basename(destination)}")
                            except Exception as e:
                                self.add_console_line(context, f"Error moving file: {str(e)}", is_error=True)
                
                # Script executor part
                if os.path.exists(self._script_path):
                    current_modified = os.path.getmtime(self._script_path)
                    
                    if current_modified > self._last_modified:
                        self._last_modified = current_modified
                        settings.last_modified_time = datetime.fromtimestamp(current_modified).strftime("%Y-%m-%d %H:%M:%S")
                        self.add_console_line(context, f"Executing updated script {os.path.basename(self._script_path)}")
                        
                        try:
                            bpy.ops.object.select_all(action='SELECT')
                            bpy.ops.object.delete()
                            
                            namespace = {}
                            with open(self._script_path, 'r') as file:
                                exec(compile(file.read(), self._script_path, 'exec'), namespace)
                            self.add_console_line(context, "Script executed successfully")
                        except Exception as e:
                            self.add_console_line(context, str(e), is_error=True)
                            
            except Exception as e:
                self.add_console_line(context, str(e), is_error=True)
        
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save your Blend file first")
            return {'CANCELLED'}

        # Check and create log folder before starting
        log_path = self.ensure_log_folder(context)
        if not log_path:
            return {'CANCELLED'}
            
        settings = context.scene.auto_script_settings
        settings.is_running = True
        settings.last_check_time = int(time.time())
        
        # Clear console output
        context.scene.console_output_lines.clear()
            
        if os.path.exists(self._script_path):
            self._last_modified = os.path.getmtime(self._script_path)
            settings.last_modified_time = datetime.fromtimestamp(self._last_modified).strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.add_console_line(context, f"Warning: Script file not found at {self._script_path}", is_error=True)
            
        wm = context.window_manager
        self._timer = wm.event_timer_add(1, window=context.window)
        wm.modal_handler_add(self)
        
        self.add_console_line(context, "Auto script system started")
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

def register():
    bpy.utils.register_class(OpenGoogleOperator)
    bpy.utils.register_class(CopyTextFromFileOperator)
    bpy.utils.register_class(SaveProjectOperator)
    
    bpy.utils.register_class(ConsoleLine)
    bpy.utils.register_class(CONSOLE_UL_output)
    bpy.utils.register_class(AutoScriptSettings)
    bpy.utils.register_class(AutoScriptPanel)
    bpy.utils.register_class(AutoScriptTerminalPanel)
    bpy.utils.register_class(CombinedAutoScriptExecutor)
    bpy.utils.register_class(StopAutoScript)
    bpy.utils.register_class(CopyConsoleText)
    
    bpy.types.Scene.auto_script_settings = bpy.props.PointerProperty(type=AutoScriptSettings)
    bpy.types.Scene.console_output_lines = bpy.props.CollectionProperty(type=ConsoleLine)
    bpy.types.Scene.console_output_index = bpy.props.IntProperty()

def unregister():
    bpy.utils.unregister_class(OpenGoogleOperator)
    bpy.utils.unregister_class(CopyTextFromFileOperator)
    bpy.utils.unregister_class(SaveProjectOperator)
    
    bpy.utils.unregister_class(CopyConsoleText)
    bpy.utils.unregister_class(StopAutoScript)
    bpy.utils.unregister_class(CombinedAutoScriptExecutor)
    bpy.utils.unregister_class(AutoScriptTerminalPanel)
    bpy.utils.unregister_class(AutoScriptPanel)
    bpy.utils.unregister_class(AutoScriptSettings)
    bpy.utils.unregister_class(CONSOLE_UL_output)
    bpy.utils.unregister_class(ConsoleLine)
    
    del bpy.types.Scene.console_output_index
    del bpy.types.Scene.console_output_lines
    del bpy.types.Scene.auto_script_settings

if __name__ == "__main__":
    register()