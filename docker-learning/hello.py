#!/usr/bin/env python3
"""
Simple Python script for Docker learning
"""
import sys
import platform
import os

def main():
    print("🐍 Hello from Python in Docker!")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    
    # Interactive part
    name = input("What's your name? ")
    print(f"Nice to meet you, {name}! 🚀")

if __name__ == "__main__":
    main()