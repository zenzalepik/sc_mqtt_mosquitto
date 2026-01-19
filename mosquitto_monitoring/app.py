import tkinter as tk
from tkinter import ttk, font, messagebox
import subprocess
import threading
import time
from datetime import datetime
import sys
import psutil
import socket

class MosquittoMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mosquitto Monitor - Real-time")
        self.root.geometry("500x500")
        
        # Port yang dimonitor
        self.monitor_port = 52345
        self.default_mqtt_port = 1883  # Port default MQTT
        
        # Flag untuk default port warning
        self.default_port_warning_shown = False
        
        # Setup GUI
        self.setup_gui()
        
        # Start monitoring
        self.running = True
        self.update_status()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        # Custom font
        title_font = font.Font(family="Helvetica", size=16, weight="bold")
        status_font = font.Font(family="Helvetica", size=10)
        warning_font = font.Font(family="Helvetica", size=11, weight="bold")
        
        # Title
        title_label = tk.Label(self.root, text="Mosquitto MQTT Monitor", font=title_font)
        title_label.pack(pady=10)
        
        # Port info
        port_frame = tk.Frame(self.root)
        port_frame.pack(pady=5)
        tk.Label(port_frame, text="Monitoring Port:", font=status_font).pack(side=tk.LEFT)
        self.port_label = tk.Label(port_frame, text=str(self.monitor_port), 
                                  font=status_font, fg="blue")
        self.port_label.pack(side=tk.LEFT, padx=5)
        
        # WARNING FRAME - untuk port 1883
        self.warning_frame = tk.Frame(self.root, bg="yellow", height=40)
        self.warning_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        self.warning_frame.pack_propagate(False)  # Maintain frame height
        
        self.warning_label = tk.Label(self.warning_frame, text="", 
                                     font=warning_font, bg="yellow", fg="red")
        self.warning_label.pack(pady=10)
        
        # Status frame
        status_frame = tk.Frame(self.root, relief=tk.RAISED, borderwidth=2)
        status_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Last update time
        self.time_label = tk.Label(status_frame, text="Last check: --:--:--", font=status_font)
        self.time_label.pack(pady=5)
        
        # Monitor Port Status (52345)
        monitor_frame = tk.Frame(status_frame)
        monitor_frame.pack(pady=5, fill=tk.X)
        tk.Label(monitor_frame, text=f"Port {self.monitor_port}:", font=status_font, 
                width=20, anchor="w").pack(side=tk.LEFT)
        self.monitor_status = tk.Label(monitor_frame, text="CHECKING...", 
                                      font=status_font, width=15)
        self.monitor_status.pack(side=tk.LEFT)
        
        # Default Port Status (1883)
        default_frame = tk.Frame(status_frame)
        default_frame.pack(pady=5, fill=tk.X)
        tk.Label(default_frame, text=f"Port {self.default_mqtt_port} (default):", 
                font=status_font, width=20, anchor="w").pack(side=tk.LEFT)
        self.default_status = tk.Label(default_frame, text="CHECKING...", 
                                      font=status_font, width=15)
        self.default_status.pack(side=tk.LEFT)
        
        # Process status
        process_frame = tk.Frame(status_frame)
        process_frame.pack(pady=5, fill=tk.X)
        tk.Label(process_frame, text="Mosquitto Process:", font=status_font, 
                width=20, anchor="w").pack(side=tk.LEFT)
        self.process_status = tk.Label(process_frame, text="CHECKING...", 
                                      font=status_font, width=15)
        self.process_status.pack(side=tk.LEFT)
        
        # Process PID
        pid_frame = tk.Frame(status_frame)
        pid_frame.pack(pady=5, fill=tk.X)
        tk.Label(pid_frame, text="Process ID:", font=status_font, 
                width=20, anchor="w").pack(side=tk.LEFT)
        self.pid_label = tk.Label(pid_frame, text="--", font=status_font)
        self.pid_label.pack(side=tk.LEFT)
        
        # Connection test
        conn_frame = tk.Frame(status_frame)
        conn_frame.pack(pady=5, fill=tk.X)
        tk.Label(conn_frame, text="MQTT Connection:", font=status_font, 
                width=20, anchor="w").pack(side=tk.LEFT)
        self.conn_status = tk.Label(conn_frame, text="CHECKING...", 
                                   font=status_font, width=15)
        self.conn_status.pack(side=tk.LEFT)
        
        # Summary status
        self.summary_label = tk.Label(status_frame, text="", font=title_font, pady=10)
        self.summary_label.pack()
        
        # Control buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Refresh Now", command=self.force_refresh,
                 bg="lightblue").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Kill Default (1883)", command=self.kill_default_port,
                 bg="orange", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Monitoring started...", 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def check_port_status(self, port):
        """Check if a specific port is in use"""
        try:
            # Method 1: Using psutil
            for conn in psutil.net_connections(kind='inet'):
                if hasattr(conn.laddr, 'port') and conn.laddr.port == port:
                    if conn.status == 'LISTEN':
                        # Get process info
                        try:
                            proc = psutil.Process(conn.pid)
                            return True, conn.pid, proc.name()
                        except:
                            return True, conn.pid, "Unknown"
            return False, None, None
        except Exception as e:
            # Method 2: Using socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    return True, None, "Unknown"
            except:
                pass
            return False, None, None
    
    def check_mosquitto_process(self):
        """Check if mosquitto process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'mosquitto' in proc.info['name'].lower():
                        return True, proc.info['pid'], proc.info['name']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return False, None, None
        except Exception as e:
            return False, None, None
    
    def test_mqtt_connection(self, port):
        """Test MQTT connection on specific port"""
        try:
            # Try to connect to the port using socket first (fast check)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Try mosquitto_pub if available
                try:
                    test_cmd = [
                        "mosquitto_pub",
                        "-h", "localhost",
                        "-p", str(port),
                        "-t", "monitor/test",
                        "-m", "test",
                        "-q", "0",
                        "-i", "monitor_client",
                        "-W", "1"
                    ]
                    
                    result = subprocess.run(
                        test_cmd,
                        capture_output=True, text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                        timeout=2
                    )
                    
                    return result.returncode == 0
                except (subprocess.SubprocessError, FileNotFoundError):
                    # mosquitto_pub not available, but port is open
                    return True
            return False
        except:
            return False
    
    def update_warning_display(self, default_port_active):
        """Update the warning display based on port 1883 status"""
        if default_port_active:
            self.warning_frame.config(bg="red")
            self.warning_label.config(
                text="⚠ WARNING: MQTT Default Port 1883 is Active! ⚠",
                bg="red", fg="white", font=("Helvetica", 12, "bold")
            )
            
            # Show messagebox once if not already shown
            if not self.default_port_warning_shown:
                self.root.after(100, lambda: messagebox.showwarning(
                    "Security Warning",
                    "Default MQTT port 1883 is active!\n\n"
                    "This may indicate:\n"
                    "1. Another Mosquitto instance running\n"
                    "2. Default installation running\n"
                    "3. Potential security risk\n\n"
                    "Consider stopping it if not needed."
                ))
                self.default_port_warning_shown = True
        else:
            self.warning_frame.config(bg="lightgreen")
            self.warning_label.config(
                text="✓ Default Port 1883 is not in use",
                bg="lightgreen", fg="darkgreen"
            )
            self.default_port_warning_shown = False
    
    def update_status(self):
        """Update all status indicators"""
        if not self.running:
            return
            
        try:
            # Update time
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.config(text=f"Last check: {current_time}")
            
            # Check monitor port (52345)
            monitor_active, monitor_pid, monitor_name = self.check_port_status(self.monitor_port)
            
            if monitor_active:
                self.monitor_status.config(text="ACTIVE", fg="green")
                # Test connection on monitor port
                monitor_conn = self.test_mqtt_connection(self.monitor_port)
                if monitor_conn:
                    self.conn_status.config(text=f"CONNECTED", fg="green")
                else:
                    self.conn_status.config(text=f"PORT OPEN", fg="orange")
            else:
                self.monitor_status.config(text="INACTIVE", fg="red")
                self.conn_status.config(text="DISCONNECTED", fg="red")
            
            # Check default port (1883)
            default_active, default_pid, default_name = self.check_port_status(self.default_mqtt_port)
            
            if default_active:
                self.default_status.config(text="ACTIVE ⚠", fg="red", font=("Helvetica", 10, "bold"))
            else:
                self.default_status.config(text="INACTIVE", fg="darkgreen")
            
            # Update warning display
            self.update_warning_display(default_active)
            
            # Check mosquitto process
            process_running, process_pid, process_name = self.check_mosquitto_process()
            
            if process_running:
                self.process_status.config(text="RUNNING", fg="green")
                self.pid_label.config(text=process_pid, fg="blue")
            else:
                self.process_status.config(text="STOPPED", fg="red")
                self.pid_label.config(text="--", fg="gray")
            
            # Update summary
            if monitor_active:
                self.summary_label.config(text=f"✅ PORT {self.monitor_port} ACTIVE", fg="green")
                self.status_bar.config(text=f"Port {self.monitor_port} active | Default port 1883: {'ACTIVE ⚠' if default_active else 'inactive'}")
            else:
                self.summary_label.config(text=f"❌ PORT {self.monitor_port} INACTIVE", fg="red")
                self.status_bar.config(text=f"Port {self.monitor_port} not active | Monitoring port 1883...")
                
        except Exception as e:
            self.status_bar.config(text=f"Error: {str(e)}")
        
        # Schedule next update (every 2 seconds)
        self.root.after(2000, self.update_status)
    
    def force_refresh(self):
        """Force immediate refresh"""
        self.status_bar.config(text="Manual refresh triggered...")
        self.update_status()
    
    def kill_default_port(self):
        """Kill process using default port 1883"""
        try:
            default_active, default_pid, default_name = self.check_port_status(self.default_mqtt_port)
            
            if default_active and default_pid:
                try:
                    process = psutil.Process(default_pid)
                    process.terminate()
                    
                    # Wait for process to terminate
                    try:
                        process.wait(timeout=3)
                        messagebox.showinfo("Success", f"Process on port 1883 (PID: {default_pid}) terminated successfully.")
                    except:
                        process.kill()
                        messagebox.showinfo("Success", f"Process on port 1883 (PID: {default_pid}) force killed.")
                    
                    self.status_bar.config(text=f"Killed process on port 1883 (PID: {default_pid})")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to kill process: {str(e)}")
            elif default_active:
                messagebox.showwarning("Warning", "Port 1883 is active but cannot identify process.\n"
                                                "You may need to stop it manually.")
            else:
                messagebox.showinfo("Info", "Port 1883 is already inactive.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error checking port: {str(e)}")
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MosquittoMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()