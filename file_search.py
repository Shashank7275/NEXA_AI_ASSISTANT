import os
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import glob
import re
from pathlib import Path
import threading
from datetime import datetime
from livekit.agents import function_tool

class JarvisFileSearch:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window
        
    def search_files(self, search_term, search_path=None, search_type="both", max_results=20):
        """
        Search for files/folders matching the search term
        """
        if not search_path:
            search_path = os.path.expanduser("~")  # Start from user home
        
        search_path = os.path.abspath(search_path)
        results = []
        
        try:
            # Convert search term to regex pattern for flexible matching
            pattern = re.compile(re.escape(search_term), re.IGNORECASE)
            
            # Walk through directory tree
            for root_dir, dirs, files in os.walk(search_path):
                # Search folders
                if search_type in ["both", "folders"]:
                    for folder in dirs:
                        if pattern.search(folder):
                            full_path = os.path.join(root_dir, folder)
                            results.append({
                                'name': folder,
                                'path': full_path,
                                'type': 'folder',
                                'size': '',
                                'modified': datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M')
                            })
                            if len(results) >= max_results:
                                return results
                
                # Search files
                if search_type in ["both", "files"]:
                    for file in files:
                        if pattern.search(file):
                            full_path = os.path.join(root_dir, file)
                            try:
                                size = self.format_file_size(os.path.getsize(full_path))
                                mod_time = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M')
                            except:
                                size, mod_time = '', ''
                                
                            results.append({
                                'name': file,
                                'path': full_path,
                                'type': 'file',
                                'size': size,
                                'modified': mod_time
                            })
                            if len(results) >= max_results:
                                return results
                            
        except PermissionError:
            pass  # Skip protected folders
        
        return results
    
    def format_file_size(self, bytes_size):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
    
    def open_item(self, full_path):
        """Open file/folder in Windows Explorer or default app"""
        try:
            if os.path.isdir(full_path):
                # Open folder in Explorer and select it
                subprocess.Popen(f'explorer /select,"{full_path}"')
            else:
                # Open file with default application
                os.startfile(full_path)
            return True
        except Exception as e:
            print(f"Error opening {full_path}: {e}")
            return False
    
    def show_results_dialog(self, results, search_term):
        """Display search results in a nice dialog"""
        if not results:
            messagebox.showinfo("Jarvis Search", f"No results found for '{search_term}'")
            return
        
        dialog = tk.Toplevel()
        dialog.title(f"Jarvis Search Results - '{search_term}' ({len(results)} found)")
        dialog.geometry("800x500")
        dialog.resizable(True, True)
        
        # Create listbox with scrollbar
        listbox = tk.Listbox(dialog, font=('Consolas', 10))
        scrollbar = tk.Scrollbar(dialog)
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Populate listbox
        for i, result in enumerate(results):
            display_text = f"[{result['type'].upper()}] {result['name']}"
            if result['size']:
                display_text += f" ({result['size']})"
            if result['modified']:
                display_text += f" - {result['modified']}"
            listbox.insert(tk.END, display_text)
        
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                item_path = results[index]['path']
                if self.open_item(item_path):
                    dialog.destroy()
        
        def on_enter_key(event):
            on_double_click(event)
        
        listbox.bind('<Double-Button-1>', on_double_click)
        listbox.bind('<Return>', on_enter_key)
        listbox.focus()
        listbox.select_set(0)  # Select first item
        
        # Instructions label
        instructions = tk.Label(dialog, text="Double-click or press Enter to open | ESC to close", 
                               font=('Arial', 9), fg='gray')
        instructions.pack(side=tk.BOTTOM, pady=5)
        
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.transient(self.root)
        dialog.grab_set()
    
    def quick_search(self, search_term):
        """Main search function - call this from your Jarvis"""
        print(f"🔍 Jarvis searching for: {search_term}")
        
        # Search in multiple common locations
        search_locations = [
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.join(os.path.expanduser("~"), "Documents"),
            os.path.expanduser("~"),
        ]
        
        all_results = []
        for location in search_locations:
            if os.path.exists(location):
                results = self.search_files(search_term, location)
                all_results.extend(results)
        
        # Remove duplicates and sort
        unique_results = []
        seen_paths = set()
        for result in all_results:
            if result['path'] not in seen_paths:
                unique_results.append(result)
                seen_paths.add(result['path'])
        
        unique_results.sort(key=lambda x: x['name'].lower())
        
        if unique_results:
            self.show_results_dialog(unique_results, search_term)
        else:
            messagebox.showinfo("Jarvis", f"No matches found for '{search_term}'")
        
        return len(unique_results)

@function_tool
async def jarvis_file_search_command(search_term: str) -> str:
    searcher = JarvisFileSearch()
    print(f"🔍 Jarvis searching for: {search_term}")
    
    search_locations = [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "Documents"),
        os.path.expanduser("~"),
    ]
    
    all_results = []
    for location in search_locations:
        if os.path.exists(location):
            results = searcher.search_files(search_term, location, max_results=5)
            all_results.extend(results)
            if len(all_results) >= 5:
                break
    
    unique_results = []
    seen_paths = set()
    for result in all_results:
        if result["path"] not in seen_paths:
            unique_results.append(result)
            seen_paths.add(result["path"])
    
    if not unique_results:
        return f"No matches found for '{search_term}'"
    
    unique_results.sort(key=lambda x: x["name"].lower())
    best = unique_results[0]
    opened = searcher.open_item(best["path"])
    if opened:
        return f"Opened {best['type']} '{best['name']}' at {best['path']}"
    return f"Found {len(unique_results)} matches but could not open '{best['name']}'"

# Example usage and testing
if __name__ == "__main__":
    searcher = JarvisFileSearch()
    
    # Test the search
    print("Testing Jarvis File Search...")
    count = searcher.quick_search("python")
    print(f"Search complete! Found {count} results.")
