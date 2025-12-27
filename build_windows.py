"""
Build script to create standalone Windows executables using PyInstaller
"""
import os
import subprocess

def build_windows_exe():
    """Build Windows executables for client and server"""
    
    # Install PyInstaller if not already installed
    print("Installing PyInstaller...")
    subprocess.run(["pip", "install", "pyinstaller"], check=True)
    
    # Build client executable
    print("\nBuilding client.exe...")
    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=ChatX_Client",
        "--icon=NONE",  
        "client.py"
    ], check=True)
    
    # Build server executable
    print("\nBuilding server.exe...")
    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--console",
        "--name=ChatX_Server",
        "server.py"
    ], check=True)
    
    print("\n Build complete!")
    print("Executables are in the 'dist' folder:")
    print("  - ChatX_Client.exe (GUI client)")
    print("  - ChatX_Server.exe (Server)")

if __name__ == "__main__":
    build_windows_exe()
