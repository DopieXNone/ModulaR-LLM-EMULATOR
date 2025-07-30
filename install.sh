#!/bin/bash

echo "===================================="
echo "ModulaR LLM EMULATOR - Linux Setup"
echo "===================================="
echo

# Function to detect distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo $ID
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    else
        echo "unknown"
    fi
}

# Function to install Python
install_python() {
    local distro=$1
    echo "[1/5] Installing Python..."
    
    case $distro in
        ubuntu|debian|linuxmint|pop)
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        fedora)
            sudo dnf install -y python3 python3-pip
            ;;
        centos|rhel|rocky|almalinux)
            sudo yum install -y python3 python3-pip
            ;;
        opensuse*|suse)
            sudo zypper install -y python3 python3-pip
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm python python-pip
            ;;
        alpine)
            sudo apk add python3 py3-pip
            ;;
        *)
            echo "ERROR: Unsupported distribution: $distro"
            echo "Please install Python 3 and pip manually"
            return 1
            ;;
    esac
}

# Function to install Ollama
install_ollama() {
    echo "[2/5] Installing Ollama..."
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        echo "curl not found. Installing curl..."
        local distro=$(detect_distro)
        case $distro in
            ubuntu|debian|linuxmint|pop)
                sudo apt install -y curl
                ;;
            fedora)
                sudo dnf install -y curl
                ;;
            centos|rhel|rocky|almalinux)
                sudo yum install -y curl
                ;;
            opensuse*|suse)
                sudo zypper install -y curl
                ;;
            arch|manjaro)
                sudo pacman -S --noconfirm curl
                ;;
            alpine)
                sudo apk add curl
                ;;
        esac
    fi
    
    # Install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Ollama installation failed"
        return 1
    fi
}

# Main function
main() {
    # Detect distribution
    DISTRO=$(detect_distro)
    echo "Detected distribution: $DISTRO"
    echo
    
    # Check if script is run as root
    if [ "$EUID" -eq 0 ]; then
        echo "WARNING: Do not run this script as root"
        echo "The script will request sudo permissions when needed"
        exit 1
    fi
    
    # Install Python
    install_python $DISTRO
    if [ $? -ne 0 ]; then
        echo "ERROR: Python installation failed"
        exit 1
    fi
    
    # Install Ollama
    install_ollama
    if [ $? -ne 0 ]; then
        echo "ERROR: Ollama installation failed"
        exit 1
    fi
    
    echo
    echo "[3/5] Starting Ollama service..."
    # Start Ollama in background
    ollama serve &
    OLLAMA_PID=$!
    
    # Wait for Ollama to be ready
    echo "Waiting for Ollama service to start..."
    sleep 5
    
    echo
    echo "[4/5] Downloading deepseek-r1:1.5b model..."
    ollama pull deepseek-r1:1.5b
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Unable to download deepseek-r1:1.5b model"
        echo "Verify that Ollama is installed correctly"
        # Kill temporary Ollama process
        kill $OLLAMA_PID 2>/dev/null
        exit 1
    fi
    
    echo
    echo "[5/5] Installing Python libraries..."
    
    # Create symbolic link for python if it doesn't exist
    if ! command -v python &> /dev/null; then
        if command -v python3 &> /dev/null; then
            echo "Creating symbolic link python -> python3"
            sudo ln -sf $(which python3) /usr/local/bin/python
        fi
    fi
    
    # Update pip
    python3 -m pip install --upgrade pip --user
    
    # Install required libraries
    python3 -m pip install --user requests colorama flask keyboard
    
    if [ $? -ne 0 ]; then
        echo "WARNING: Some libraries may not have been installed correctly"
    fi
    
    # Kill temporary Ollama process
    kill $OLLAMA_PID 2>/dev/null
    
    echo
    echo "===================================="
    echo "ModulaR LLM EMULATOR Setup Complete!"
    echo "===================================="
    echo
    echo "Installed programs:"
    echo "- Python 3"
    echo "- Ollama"
    echo "- Model: deepseek-r1:1.5b"
    echo
    echo "Installed Python libraries:"
    echo "- requests"
    echo "- colorama"
    echo "- flask"
    echo "- keyboard"
    echo
    echo "Notes:"
    echo "- datetime, json, subprocess, importlib, typing are built-in modules"
    echo "- msvcrt is Windows-specific (not available on Linux)"
    echo "- To start Ollama: ollama serve"
    echo "- To use the model: ollama run deepseek-r1:1.5b"
    echo
}

# Run main function
main "$@"
