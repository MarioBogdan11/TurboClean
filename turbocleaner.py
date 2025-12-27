import customtkinter as ctk
import os
import shutil
import threading
import time
import sys
import subprocess
import winreg
import ctypes
import psutil
from datetime import datetime, timedelta
from tkinter import messagebox
from PIL import Image

# Configuration
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")  
# Constants
BRAND_COLOR = "#FF2E38"
BG_COLOR = "#F4F5F7"
SIDEBAR_COLOR = "#FFFFFF"
TEXT_COLOR = "#333333"
CARD_COLOR = "#FFFFFF"

class TurboCleanApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TurboClean")
        self.geometry("1100x700")
        self.configure(fg_color=BG_COLOR)
        
        # Asset directories and map (images optional, emojis used as fallback)
        self.asset_dirs = [
            os.path.join(os.path.dirname(__file__), "assets"),
            os.path.join(os.path.dirname(__file__), "Assets")
        ]
        self.asset_map = {
            "logo": ["logo.png", "logo.jpg", "logo.webp"],
            "scan_shield": ["scan.png", "shield.png", "shield-emoji.png"],
            "disk": ["disk.png", "drive.png", "hdd.png"],
            "clean_sparkle": ["sparkle.png", "clean.png", "sparkles.png"],
            "trash": ["trash.png", "bin.png", "delete.png"],
            "quick_clean_drive": ["clean_drive.png", "drive_clean.png"],
            "quick_ping_test": ["ping.png", "network.png", "wifi.png"],
            "quick_hardware_info": ["hardware.png", "info.png", "system.png"],
            "program_box": ["box.png", "package.png"],
            "program_old": ["old.png", "deprecated.png"]
        }
        
        # Data
        self.scan_results = {"junk": 0, "old": 0, "issues": 0, "size": 0}
        self.clean_targets = []
        self.programs_list = []

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_frames()
        
        # Start on Scan page
        self.show_frame("scan")

    def _find_asset_path(self, candidates):
        for folder in self.asset_dirs:
            for name in candidates:
                p = os.path.join(folder, name)
                if os.path.exists(p):
                    return p
        return None

    def _load_ctk_image(self, path, size):
        try:
            pil_image = Image.open(path)
            return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)
        except Exception:
            return None

    def get_image(self, key, size):
        candidates = self.asset_map.get(key, [])
        if not candidates:
            return None
        path = self._find_asset_path(candidates)
        if not path:
            return None
        return self._load_ctk_image(path, size)

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=SIDEBAR_COLOR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        # Logo
        logo_img = self.get_image("logo", (30, 30))
        if logo_img:
            self.logo_label = ctk.CTkLabel(self.sidebar, text=" TurboClean", image=logo_img, compound="left", font=("Segoe UI", 20, "bold"), text_color=TEXT_COLOR)
            self.logo_image = logo_img
        else:
            self.logo_label = ctk.CTkLabel(self.sidebar, text="⚡ TurboClean", font=("Segoe UI", 20, "bold"), text_color=TEXT_COLOR)
            
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 40), sticky="w")

        # Navigation Buttons
        self.nav_buttons = {}
        buttons = [
            ("Scan", "scan_shield", "scan", "🔍"), # Updated icon_key and added fallback emoji
            ("Clean", "clean_sparkle", "clean", "✨"),
            ("Boost", "logo", "boost", "⚡"), 
            ("Programs", "program_box", "programs", "📦") # Added fallback emoji
        ]

        for i, (text, icon_key, name, fallback_emoji) in enumerate(buttons):
            image = self.get_image(icon_key, (20, 20)) # Smaller size for sidebar icons
            
            # Use image if available, otherwise use emoji and set compound to "left"
            if image:
                button_text = f"  {text}"
                compound_type = "left"
            else:
                button_text = f"  {fallback_emoji}  {text}"
                compound_type = "left"

            btn = ctk.CTkButton(
                self.sidebar, 
                text=button_text,
                anchor="w",
                fg_color="transparent", 
                text_color=TEXT_COLOR,
                hover_color="#F0F0F0",
                font=("Segoe UI", 14),
                height=40,
                image=image,
                compound=compound_type, 
                command=lambda n=name: self.show_frame(n)
            )
            btn.grid(row=i+1, column=0, padx=10, pady=5, sticky="ew")
            self.nav_buttons[name] = btn

        # Version
        self.version_label = ctk.CTkLabel(self.sidebar, text="Version 2.0.1", text_color="gray", font=("Segoe UI", 10))
        self.version_label.grid(row=6, column=0, padx=20, pady=20, sticky="w")

    def setup_frames(self):
        self.frames = {}
        
        # Create all frames
        self.frames["scan"] = ScanFrame(self)
        self.frames["clean"] = CleanFrame(self)
        self.frames["boost"] = BoostFrame(self)
        self.frames["programs"] = ProgramsFrame(self)

        for frame in self.frames.values():
            frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_frame(self, name):
        # Hide all
        for frame in self.frames.values():
            frame.grid_remove()
        
        # Show selected
        self.frames[name].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Update sidebar button styles
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                btn.configure(fg_color="#FFE5E5", text_color=BRAND_COLOR)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_COLOR)

class ScanFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Header
        self.title = ctk.CTkLabel(self, text="System Scan", font=("Segoe UI", 24, "bold"), text_color=TEXT_COLOR)
        self.title.pack(anchor="w", pady=(0, 5))
        
        self.subtitle = ctk.CTkLabel(self, text="Analyzing your system for optimization opportunities", font=("Segoe UI", 12), text_color="gray")
        self.subtitle.pack(anchor="w", pady=(0, 20))

        # Status Card
        self.status_card = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=10)
        self.status_card.pack(fill="x", pady=(0, 20), ipady=10)
        
        shield_img = self.master.get_image("scan_shield", (30, 30))
        if shield_img:
            self.status_icon = ctk.CTkLabel(self.status_card, text="", image=shield_img)
        else:
            self.status_icon = ctk.CTkLabel(self.status_card, text="🛡️", font=("Segoe UI", 30))
        self.status_icon.pack(side="left", padx=20)
        
        self.status_text_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        self.status_text_frame.pack(side="left", fill="y")
        
        self.status_label = ctk.CTkLabel(self.status_text_frame, text="Ready to Scan", font=("Segoe UI", 16, "bold"), text_color=TEXT_COLOR)
        self.status_label.pack(anchor="w")
        self.status_sub = ctk.CTkLabel(self.status_text_frame, text="Ready to scan", font=("Segoe UI", 12), text_color="gray")
        self.status_sub.pack(anchor="w")

        self.progress_label = ctk.CTkLabel(self.status_card, text="0%", font=("Segoe UI", 24, "bold"), text_color=BRAND_COLOR)
        self.progress_label.pack(side="right", padx=30)

        # Progress Bar
        self.progressbar = ctk.CTkProgressBar(self.status_card, progress_color=BRAND_COLOR, height=10)
        self.progressbar.set(0)
        self.progressbar.pack(side="bottom", fill="x", padx=20, pady=15)

        # Info Cards Grid
        self.grid_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        self.grid_frame.pack(fill="x", padx=20, pady=10)
        
        self.create_info_card(self.grid_frame, 0, "Junk Files", "junk_val")
        self.create_info_card(self.grid_frame, 1, "Old Files", "old_val")
        self.create_info_card(self.grid_frame, 2, "Issues Found", "issues_val")

        # Action Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=10)
        
        self.scan_btn = ctk.CTkButton(self.btn_frame, text="Scan Now", fg_color=BRAND_COLOR, hover_color="#D92630", height=50, font=("Segoe UI", 16, "bold"), command=self.start_scan)
        self.scan_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Disk Info Section
        self.disk_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.disk_frame.pack(fill="x", pady=20)
        
        ctk.CTkLabel(self.disk_frame, text="Disk Information", font=("Segoe UI", 14, "bold"), text_color=TEXT_COLOR).pack(anchor="w", pady=(0, 10))
        
        self.selected_drives = [] # To store selected drive mountpoints
        self.drive_checkboxes = [] # To hold checkbox variables and drive info
        self.load_disk_info()

    def load_disk_info(self):
        # Clear previous entries
        for widget in self.disk_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and "drive_card" in widget.winfo_name(): # Only clear drive cards
                widget.destroy()
        self.drive_checkboxes = []

        try:
            partitions = psutil.disk_partitions()
            for p in partitions:
                if 'fixed' in p.opts:
                    try:
                        usage = psutil.disk_usage(p.mountpoint)
                        
                        card = ctk.CTkFrame(self.disk_frame, fg_color=CARD_COLOR, corner_radius=8, name="drive_card")
                        card.pack(fill="x", pady=5)
                        
                        # Checkbox for selection
                        var = ctk.BooleanVar(value=True) # Default to selected
                        cb = ctk.CTkCheckBox(card, text="", variable=var, width=24, checkbox_width=20, checkbox_height=20, border_color=BRAND_COLOR, fg_color=BRAND_COLOR)
                        cb.pack(side="left", padx=(15, 5), pady=15)
                        self.drive_checkboxes.append((var, p.mountpoint))
                        
                        disk_img = self.master.get_image("disk", (20, 20))
                        if disk_img:
                            icon = ctk.CTkLabel(card, text="", image=disk_img)
                        else:
                            icon = ctk.CTkLabel(card, text="💾", font=("Segoe UI", 20))
                        icon.pack(side="left", padx=15, pady=15)
                        
                        info = ctk.CTkFrame(card, fg_color="transparent")
                        info.pack(side="left", fill="x", expand=True)
                        
                        ctk.CTkLabel(info, text=f"Local Disk ({p.device})", font=("Segoe UI", 12, "bold"), text_color=TEXT_COLOR).pack(anchor="w")
                        
                        # Progress bar for disk usage
                        percent = usage.percent
                        bar = ctk.CTkProgressBar(info, height=6, width=200, progress_color=BRAND_COLOR if percent < 90 else "#FF0000")
                        bar.set(percent / 100)
                        bar.pack(anchor="w", pady=5)
                        
                        free_gb = usage.free / (1024**3)
                        total_gb = usage.total / (1024**3)
                        ctk.CTkLabel(info, text=f"{free_gb:.1f} GB free of {total_gb:.1f} GB", font=("Segoe UI", 10), text_color="gray").pack(anchor="w")
                        
                    except Exception:
                        pass
        except Exception:
            pass

    def create_info_card(self, parent, col, title, attr_name):
        frame = ctk.CTkFrame(parent, fg_color="#F8F9FA", corner_radius=8)
        frame.grid(row=0, column=col, sticky="ew", padx=5, pady=5)
        parent.grid_columnconfigure(col, weight=1)
        
        ctk.CTkLabel(frame, text=f"📂 {title}", font=("Segoe UI", 12), text_color="gray").pack(anchor="w", padx=10, pady=(10, 5))
        lbl = ctk.CTkLabel(frame, text="-", font=("Segoe UI", 16, "bold"), text_color=TEXT_COLOR)
        lbl.pack(anchor="w", padx=10, pady=(0, 10))
        setattr(self, attr_name, lbl)

    def start_scan(self):
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.status_label.configure(text="Scanning System...")
        threading.Thread(target=self.run_scan, daemon=True).start()

    def get_dir_size(self, path):
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_dir_size(entry.path)
        except Exception:
            pass
        return total

    def run_scan(self):
        scan_items = []
        total_junk_size = 0
        
        # Define scan targets
        targets = [
            ("System Temp", os.environ.get('TEMP', 'C:\\Windows\\Temp')),
            ("User Temp", os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')),
            ("Windows Update Cache", "C:\\Windows\\SoftwareDistribution\\Download"),
            ("Prefetch", "C:\\Windows\\Prefetch"),
            ("Chrome Cache", os.path.join(os.environ.get('LOCALAPPDATA', ''), r"Google\Chrome\User Data\Default\Cache")),
            ("Edge Cache", os.path.join(os.environ.get('LOCALAPPDATA', ''), r"Microsoft\Edge\User Data\Default\Cache")),
        ]

        step = 100 / (len(targets) + 1)
        current_progress = 0

        for name, path in targets:
            if os.path.exists(path):
                try:
                    size = self.get_dir_size(path)
                    if size > 0:
                        size_str = f"{size / (1024*1024):.1f} MB"
                        if size > 1024*1024*1024:
                            size_str = f"{size / (1024*1024*1024):.2f} GB"
                        
                        scan_items.append((name, path, size_str, size))
                        total_junk_size += size
                except Exception:
                    pass
            
            current_progress += step
            self.progressbar.set(current_progress / 100)
            self.progress_label.configure(text=f"{int(current_progress)}%")
            time.sleep(0.1) # UI update buffer

        # Check for issues (Boost optimizations not enabled)
        issues_count = 0
        # This is a simplified check. In a real app, we'd check registry keys.
        # Here we assume if the app hasn't applied them, they are issues.
        # We can check the BoostFrame state if we had access, but for now let's simulate
        # checking the registry for a few common ones.
        
        # Example: Check if Dark Mode is enabled in System
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            if val == 1: # Light mode is on
                issues_count += 1
        except:
            pass
            
        # Example: Check Telemetry
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection")
            val, _ = winreg.QueryValueEx(key, "AllowTelemetry")
            if val != 0:
                issues_count += 1
        except:
            issues_count += 1 # Key missing means likely enabled (default)

        self.progressbar.set(1.0)
        self.progress_label.configure(text="100%")
        
        # Pass results to main thread
        self.after(0, lambda: self.finish_scan(scan_items, total_junk_size, issues_count))

    def finish_scan(self, items, total_size, issues):
        self.scan_btn.configure(state="normal", text="Scan Again")
        self.status_label.configure(text="Scan Complete")
        self.status_sub.configure(text="Review results in Clean tab")
        
        # Format size
        size_str = f"{total_size / (1024*1024):.1f} MB"
        if total_size > 1024*1024*1024:
            size_str = f"{total_size / (1024*1024*1024):.2f} GB"
            
        self.junk_val.configure(text=size_str)
        self.old_val.configure(text=f"{len(items)} Locs")
        self.issues_val.configure(text=f"{issues} Issues")
        
        # Update Clean Tab
        self.master.frames["clean"].set_items(items)
        
        # Switch to Clean Tab
        self.master.show_frame("clean")


class CleanFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.title = ctk.CTkLabel(self, text="Clean Files", font=("Segoe UI", 24, "bold"), text_color=TEXT_COLOR)
        self.title.pack(anchor="w", pady=(0, 5))
        
        self.subtitle = ctk.CTkLabel(self, text="Select directories to clean and free up space", font=("Segoe UI", 12), text_color="gray")
        self.subtitle.pack(anchor="w", pady=(0, 20))

        # Header Card
        self.header = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=10)
        self.header.pack(fill="x", pady=(0, 20), ipady=10)
        
        ctk.CTkLabel(self.header, text="✨", font=("Segoe UI", 24)).pack(side="left", padx=20)
        
        info = ctk.CTkFrame(self.header, fg_color="transparent")
        info.pack(side="left")
        ctk.CTkLabel(info, text="Ready to Clean", font=("Segoe UI", 14, "bold"), text_color=TEXT_COLOR).pack(anchor="w")
        self.selected_label = ctk.CTkLabel(info, text="0 directories selected", font=("Segoe UI", 12), text_color="gray")
        self.selected_label.pack(anchor="w")
        
        self.total_size_label = ctk.CTkLabel(self.header, text="0 MB", font=("Segoe UI", 20, "bold"), text_color=BRAND_COLOR)
        self.total_size_label.pack(side="right", padx=20)

        # List
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, pady=(0, 20))

        self.check_vars = []
        
        # Initial empty state or default
        self.set_items([])

        # Action
        self.clean_btn = ctk.CTkButton(self, text="Clean Selected", fg_color=BRAND_COLOR, hover_color="#D92630", height=50, font=("Segoe UI", 16, "bold"), command=self.clean_files)
        self.clean_btn.pack(fill="x")

    def set_items(self, items):
        # Clear existing
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.check_vars = []
        
        if not items:
            ctk.CTkLabel(self.scroll, text="No junk files found. Run a scan first!", text_color="gray").pack(pady=20)
            self.total_size_label.configure(text="0 MB")
            self.selected_label.configure(text="0 directories selected")
            return

        for name, path, size_str, size_bytes in items:
            self.add_item(name, path, size_str, size_bytes)
            
        self.update_selection()

    def add_item(self, name, path, size_str, size_bytes):
        row = ctk.CTkFrame(self.scroll, fg_color=CARD_COLOR, corner_radius=8)
        row.pack(fill="x", pady=5)
        
        var = ctk.BooleanVar(value=True)
        self.check_vars.append((var, path, size_bytes))
        
        cb = ctk.CTkCheckBox(row, text="", variable=var, width=24, checkbox_width=24, checkbox_height=24, border_color=BRAND_COLOR, fg_color=BRAND_COLOR, command=self.update_selection)
        cb.pack(side="left", padx=15, pady=15)
        
        icon = ctk.CTkLabel(row, text="🗑️", font=("Segoe UI", 20))
        icon.pack(side="left", padx=10)
        
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(info, text=name, font=("Segoe UI", 14, "bold"), text_color=TEXT_COLOR).pack(anchor="w")
        ctk.CTkLabel(info, text=path[:50] + "..." if len(path) > 50 else path, font=("Segoe UI", 10), text_color="gray").pack(anchor="w")
        
        ctk.CTkLabel(row, text=size_str, font=("Segoe UI", 14, "bold"), text_color=BRAND_COLOR).pack(side="right", padx=20)

    def update_selection(self):
        count = 0
        total_bytes = 0
        for var, _, size in self.check_vars:
            if var.get():
                count += 1
                total_bytes += size
        
        self.selected_label.configure(text=f"{count} directories selected")
        
        size_str = f"{total_bytes / (1024*1024):.1f} MB"
        if total_bytes > 1024*1024*1024:
            size_str = f"{total_bytes / (1024*1024*1024):.2f} GB"
        self.total_size_label.configure(text=size_str)
        
    def clean_files(self):
        if not messagebox.askyesno("Confirm Clean", "Are you sure you want to permanently delete these files?"):
            return
            
        self.clean_btn.configure(state="disabled", text="Cleaning...")
        threading.Thread(target=self.run_clean, daemon=True).start()

    def run_clean(self):
        for var, path, _ in self.check_vars:
            if var.get() and os.path.exists(path):
                try:
                    # Simple deletion logic
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        for item in os.listdir(path):
                            item_path = os.path.join(path, item)
                            try:
                                if os.path.isfile(item_path) or os.path.islink(item_path):
                                    os.unlink(item_path)
                                elif os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                            except Exception:
                                pass
                except Exception:
                    pass
        
        self.after(0, lambda: self.clean_btn.configure(state="normal", text="Clean Selected"))
        self.after(0, lambda: messagebox.showinfo("Success", "Cleaning Completed!"))


class AccordionItem(ctk.CTkFrame):
    def __init__(self, master, title, icon_color, icon_text, options):
        super().__init__(master, fg_color=CARD_COLOR, corner_radius=10)
        self.options = options
        self.is_expanded = False
        
        # Header (Always visible)
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", ipady=5)
        self.header.bind("<Button-1>", self.toggle)
        
        # Icon
        self.icon_frame = ctk.CTkFrame(self.header, width=40, height=40, corner_radius=20, fg_color="#F0F0F0") 
        self.icon_frame.pack_propagate(False)
        self.icon_frame.pack(side="left", padx=20, pady=10)
        

        self.icon_label = ctk.CTkLabel(self.icon_frame, text=icon_text, font=("Segoe UI Emoji", 20), text_color=icon_color, anchor="center")
        self.icon_label.pack(expand=True, fill="both")
        
        # Title & Subtitle
        self.text_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.text_frame.pack(side="left", fill="y", pady=10)
        
        self.title_label = ctk.CTkLabel(self.text_frame, text=title, font=("Segoe UI", 14, "bold"), text_color=TEXT_COLOR)
        self.title_label.pack(anchor="w")
        
        enabled_count = sum(1 for opt in options if isinstance(opt, tuple) and len(opt) > 3 and opt[3]) # Check if enabled by default
        self.subtitle_label = ctk.CTkLabel(self.text_frame, text=f"{enabled_count} of {len(options)} enabled", font=("Segoe UI", 12), text_color="gray")
        self.subtitle_label.pack(anchor="w")
        
        # Arrow
        self.arrow_label = ctk.CTkLabel(self.header, text=">", font=("Segoe UI", 14, "bold"), text_color="gray")
        self.arrow_label.pack(side="right", padx=20)
        
        # Content (Hidden by default)
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        
        self.vars = []
        for item in options:
            text = item[0]
            key = item[1]
            command = item[2] if len(item) > 2 else None
            default = item[3] if len(item) > 3 else False
            
            row = ctk.CTkFrame(self.content, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            
            var = ctk.BooleanVar(value=default)
            self.vars.append((key, var))
            
            cb = ctk.CTkCheckBox(row, text=text, variable=var, font=("Segoe UI", 12), text_color=TEXT_COLOR, border_color=BRAND_COLOR, fg_color=BRAND_COLOR, command=command)
            cb.pack(anchor="w")

    def toggle(self, event=None):
        if self.is_expanded:
            self.content.pack_forget()
            self.arrow_label.configure(text=">")
        else:
            self.content.pack(fill="x", pady=(0, 15))
            self.arrow_label.configure(text="v")
        self.is_expanded = not self.is_expanded

class BoostFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.title = ctk.CTkLabel(self, text="Boost System", font=("Segoe UI", 24, "bold"), text_color=TEXT_COLOR)
        self.title.pack(anchor="w", pady=(0, 5))
        
        self.subtitle = ctk.CTkLabel(self, text="Optimize your system with advanced tweaks and settings", font=("Segoe UI", 12), text_color="gray")
        self.subtitle.pack(anchor="w", pady=(0, 20))

        # Scrollable Container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # Active Status Card
        self.status_card = ctk.CTkFrame(self.scroll, fg_color=CARD_COLOR, corner_radius=10)
        self.status_card.pack(fill="x", pady=(0, 15), ipady=10)
        
        # Icon
        icon_bg = ctk.CTkFrame(self.status_card, width=50, height=50, corner_radius=25, fg_color=BRAND_COLOR)
        icon_bg.pack(side="left", padx=20)
        ctk.CTkLabel(icon_bg, text="⚡", font=("Segoe UI", 24), text_color="white").place(relx=0.5, rely=0.5, anchor="center")
        
        # Text
        text_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        text_frame.pack(side="left", fill="y")
        ctk.CTkLabel(text_frame, text="7 Optimizations Active", font=("Segoe UI", 16, "bold"), text_color=TEXT_COLOR).pack(anchor="w")
        ctk.CTkLabel(text_frame, text="Full multilingual support • 24 languages available", font=("Segoe UI", 12), text_color="gray").pack(anchor="w")
        
        # Quick Actions Grid
        self.quick_actions = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.quick_actions.pack(fill="x", pady=(0, 15))
        
        actions = [
            ("Clean Drive", "💾", self.go_to_clean),
            ("Ping Test", "📶", self.run_ping_test),
            ("Hardware Info", "👁️", self.run_hardware_info)
        ]
        
        for i, (text, icon, cmd) in enumerate(actions):
            card = ctk.CTkButton(self.quick_actions, text="", fg_color=CARD_COLOR, corner_radius=10, height=80, hover_color="#E0E0E0", command=cmd)
            card.grid(row=0, column=i, sticky="ew", padx=5)
            self.quick_actions.grid_columnconfigure(i, weight=1)
            
            card.destroy()
            
            card = ctk.CTkFrame(self.quick_actions, fg_color=CARD_COLOR, corner_radius=10, height=80)
            card.grid(row=0, column=i, sticky="ew", padx=5)
            card.pack_propagate(False)
            self.quick_actions.grid_columnconfigure(i, weight=1)
            
            # Bind click to frame and children
            card.bind("<Button-1>", lambda e, c=cmd: c())
            
            icon_lbl = ctk.CTkLabel(card, text=icon, font=("Segoe UI", 16), text_color=BRAND_COLOR)
            icon_lbl.pack(pady=(15, 5))
            icon_lbl.bind("<Button-1>", lambda e, c=cmd: c())
            
            text_lbl = ctk.CTkLabel(card, text=text, font=("Segoe UI", 11, "bold"), text_color=TEXT_COLOR)
            text_lbl.pack()
            text_lbl.bind("<Button-1>", lambda e, c=cmd: c())

        # Accordions
        self.accordions = []
        
        # Appearance & Performance
        self.add_accordion("Appearance & Performance", "#4A90E2", "🎨", [
            ("Enable Dark Theme", "dark_mode", self.toggle_dark_mode, False),
            ("Disable Desktop Animations", "disable_anim", self.toggle_animations, True),
            ("Disable Transparency Effects", "disable_transparency", None, False),
            ("Enable UTC Time Globally", "utc_time", None, False)
        ])
        
        # Privacy & Telemetry
        self.add_accordion("Privacy & Telemetry", "#FF2E38", "🛡️", [
            ("Turn off Windows telemetry, Cortana, and more", "disable_telemetry", None, True),
            ("Disable Office telemetry (2016+)", "office_telemetry", None, True),
            ("Disable CoPilot AI in Windows 11 & Edge", "disable_copilot", None, True),
            ("Block Ad Tracking", "block_ads", None, False)
        ])
        
        # System Services
        self.add_accordion("System Services", "#9013FE", "⚙️", [
            ("Disable unnecessary Windows services", "disable_services", None, True),
            ("Stop automatic Windows 10/11 updates", "stop_updates", None, True),
            ("Disable OneDrive", "disable_onedrive", None, False),
            ("Disable HPET", "disable_hpet", None, False)
        ])
        
        # Network Optimization
        self.add_accordion("Network Optimization", "#50E3C2", "📶", [
            ("Enhance system and network performance", "perf_tweak", None, True),
            ("Clean browser profiles", "clean_browsers", None, False),
            ("Flush DNS cache", "flush_dns", None, False)
        ])
        
        # Registry & Advanced
        self.add_accordion("Registry & Advanced", "#F5A623", "🔧", [
            ("Fix common registry issues", "registry_fix", None, False),
            ("Support silent runs (Template)", "silent_run", None, False),
            ("Add items to desktop right-click menu", "context_menu", None, False)
        ])

        # Footer Actions
        self.footer = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.footer.pack(fill="x", pady=20)
        
        self.apply_btn = ctk.CTkButton(self.footer, text="Apply All Changes", fg_color=BRAND_COLOR, hover_color="#D92630", height=50, font=("Segoe UI", 16, "bold"), command=self.apply_changes)
        self.apply_btn.pack(fill="x", pady=(0, 10))

    def go_to_clean(self):
        self.master.show_frame("clean")

    def run_ping_test(self):
        import webbrowser
        webbrowser.open("https://www.speedtest.net")

    def run_hardware_info(self):
        try:
            subprocess.Popen("msinfo32")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open System Information: {e}")

    def add_accordion(self, title, color, icon, options):
        acc = AccordionItem(self.scroll, title, color, icon, options)
        acc.pack(fill="x", pady=5)
        self.accordions.append(acc)

    def toggle_dark_mode(self):
        # Simple toggle implementation
        mode = ctk.get_appearance_mode()
        new_mode = "Dark" if mode == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        
        # Update colors for dark mode if needed (simple override)
        global TEXT_COLOR, CARD_COLOR, SIDEBAR_COLOR, BG_COLOR
        if new_mode == "Dark":
            TEXT_COLOR = "#FFFFFF"
            CARD_COLOR = "#2B2D31"
            SIDEBAR_COLOR = "#1E1F22"
            BG_COLOR = "#111111"
        else:
            TEXT_COLOR = "#333333"
            CARD_COLOR = "#FFFFFF"
            SIDEBAR_COLOR = "#FFFFFF"
            BG_COLOR = "#F4F5F7"
            
        messagebox.showinfo("Theme", f"Switched to {new_mode} Mode. Some colors may require a restart to apply fully.")

    def toggle_animations(self):
        # Registry tweak for animations
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                # 2 = Adjust for best performance (disable all), 1 = Best appearance, 3 = Custom
                # This is a simplification; individual effects are in UserPreferencesMask
                winreg.SetValueEx(key, "VisualFXSetting", 0, winreg.REG_DWORD, 2) 
            messagebox.showinfo("Success", "Desktop Animations Disabled (Performance Mode Set). Restart Explorer to see changes.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change registry: {e}")

    def apply_changes(self):
        # Collect all enabled options
        changes = []
        for acc in self.accordions:
            for key, var in acc.vars:
                if var.get():
                    changes.append(key)
        
        messagebox.showinfo("Apply", f"Applying {len(changes)} optimizations...\n\n(This is a demo, real system changes would happen here)")

class ProgramsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.title = ctk.CTkLabel(self, text="Installed Programs", font=("Segoe UI", 24, "bold"), text_color=TEXT_COLOR)
        self.title.pack(anchor="w", pady=(0, 5))
        
        self.subtitle = ctk.CTkLabel(self, text="Review and uninstall programs installed over 1 year ago", font=("Segoe UI", 12), text_color="gray")
        self.subtitle.pack(anchor="w", pady=(0, 20))

        # Stats
        self.stats = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=10)
        self.stats.pack(fill="x", pady=(0, 20), ipady=10)
        
        ctk.CTkLabel(self.stats, text="📦", font=("Segoe UI", 24), text_color=BRAND_COLOR).pack(side="left", padx=20)
        
        info_frame = ctk.CTkFrame(self.stats, fg_color="transparent")
        info_frame.pack(side="left")
        
        self.count_label = ctk.CTkLabel(info_frame, text="Loading...", font=("Segoe UI", 14, "bold"), text_color=TEXT_COLOR)
        self.count_label.pack(anchor="w")
        
        self.old_count_label = ctk.CTkLabel(info_frame, text="", font=("Segoe UI", 12), text_color="#FFB000")
        self.old_count_label.pack(anchor="w")
        
        self.select_old_btn = ctk.CTkButton(self.stats, text="Select All Old", width=100, height=30, fg_color="#FFB000", hover_color="#E0A000", text_color="white", command=self.select_old_apps)
        self.select_old_btn.pack(side="right", padx=20)

        # List
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, pady=(0, 20))
        
        self.programs_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.programs_container.pack(fill="x")
        
        self.program_vars = []

        # Action Bar
        self.action_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.action_bar.pack(fill="x", pady=10)
        
        self.uninstall_btn = ctk.CTkButton(self.action_bar, text="Uninstall 0 Programs", fg_color="#FF9999", hover_color="#FF2E38", height=40, state="disabled")
        self.uninstall_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(self.action_bar, text="Refresh List", fg_color=CARD_COLOR, text_color=TEXT_COLOR, hover_color="#E0E0E0", height=40, width=100, command=self.load_programs).pack(side="right")

        # Load programs
        self.after(500, self.load_programs)

    def load_programs(self):
        # Clear existing
        for widget in self.programs_container.winfo_children():
            widget.destroy()
        self.program_vars = []
            
        self.count_label.configure(text="Scanning Registry...")
        self.old_count_label.configure(text="")
        threading.Thread(target=self.fetch_programs, daemon=True).start()

    def fetch_programs(self):
        programs = []
        one_year_ago = datetime.now() - timedelta(days=365)
        
        try:
            # Scan Uninstall key
            key_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            seen_names = set()
            
            for root, key_path in key_paths:
                try:
                    with winreg.OpenKey(root, key_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    except:
                                        continue
                                        
                                    if name in seen_names:
                                        continue
                                    seen_names.add(name)
                                    
                                    is_old = False
                                    date_str = "Unknown"
                                    
                                    try:
                                        date_raw = winreg.QueryValueEx(subkey, "InstallDate")[0]
                                        if len(date_raw) == 8:
                                            install_date = datetime.strptime(date_raw, "%Y%m%d")
                                            date_str = install_date.strftime("%b %d, %Y")
                                            if install_date < one_year_ago:
                                                is_old = True
                                                date_str += f" • { (datetime.now() - install_date).days } days old"
                                    except:
                                        pass
                                        
                                    programs.append((name, date_str, is_old))
                            except:
                                pass
                except:
                    pass
        except Exception as e:
            print(e)

        # Sort: Oldest first
        programs.sort(key=lambda x: x[2], reverse=True)
        self.after(0, lambda: self.display_programs(programs))

    def display_programs(self, programs):
        self.count_label.configure(text=f"{len(programs)} Programs Installed")
        old_count = sum(1 for p in programs if p[2])
        self.old_count_label.configure(text=f"{old_count} old programs detected")
        
        if old_count > 0:
             self.old_count_label.configure(text_color="#FFB000")
             self.select_old_btn.configure(state="normal")
        else:
             self.select_old_btn.configure(state="disabled")

        for name, date, is_old in programs:
            row = ctk.CTkFrame(self.programs_container, fg_color=CARD_COLOR, corner_radius=8)
            row.pack(fill="x", pady=5)
            
            var = ctk.BooleanVar()
            self.program_vars.append((var, is_old))
            
            cb = ctk.CTkCheckBox(row, text="", variable=var, width=20, border_color=BRAND_COLOR, fg_color=BRAND_COLOR, command=self.update_uninstall_btn)
            cb.pack(side="left", padx=15, pady=15)
            
            # Icon placeholder
            icon_lbl = ctk.CTkLabel(row, text="📦" if not is_old else "🏚️", font=("Segoe UI", 20))
            icon_lbl.pack(side="left", padx=10)
            
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            
            name_lbl = ctk.CTkLabel(info, text=name, font=("Segoe UI", 12, "bold"), text_color=TEXT_COLOR)
            name_lbl.pack(anchor="w")
            
            date_lbl = ctk.CTkLabel(info, text=date, font=("Segoe UI", 10), text_color="gray")
            date_lbl.pack(anchor="w")
            
            if is_old:
                tag = ctk.CTkLabel(row, text="Old", fg_color="#FFF3CD", text_color="#856404", corner_radius=5, padx=5)
                tag.pack(side="right", padx=15)
            
            size_lbl = ctk.CTkLabel(row, text="-- MB", font=("Segoe UI", 12, "bold"), text_color=TEXT_COLOR)
            size_lbl.pack(side="right", padx=15)

    def select_old_apps(self):
        for var, is_old in self.program_vars:
            if is_old:
                var.set(True)
        self.update_uninstall_btn()

    def update_uninstall_btn(self):
        count = sum(1 for v, _ in self.program_vars if v.get())
        self.uninstall_btn.configure(text=f"Uninstall {count} Programs")
        if count > 0:
            self.uninstall_btn.configure(state="normal", fg_color=BRAND_COLOR)
        else:
            self.uninstall_btn.configure(state="disabled", fg_color="#FF9999")

if __name__ == "__main__":
    app = TurboCleanApp()
    app.mainloop()
