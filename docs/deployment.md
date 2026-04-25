# Xeno Bot Deployment & CI/CD Guide

This document outlines the architecture and steps taken to host the Xeno Discord Bot on an Oracle Cloud Ubuntu VM using Docker and GitHub Actions for automated deployment.

## 🏗️ Architecture Overview

1.  **Local Development**: VS Code with a Python virtual environment.
2.  **Continuous Integration (CI)**: GitHub Actions builds a Docker image and pushes it to **GitHub Container Registry (GHCR)**.
3.  **Continuous Deployment (CD)**: GitHub Actions SSHs into the Oracle VM and triggers an update.
4.  **Hosting**: Oracle Ubuntu VM running Docker Compose.

---

## 💻 Local Setup (VS Code)

To make development easier, the following VS Code files were added:
*   **`.vscode/launch.json`**: Configures the "F5" run command to execute `bot.py` directly.
*   **`.vscode/settings.json`**: Ensures VS Code uses the `.venv` interpreter and activates it in the terminal automatically.

---

## ☁️ Server Setup (Ubuntu VM)

### 1. Prerequisites
Docker and Docker Compose (v2) were installed using the official Docker repositories.

### 2. File Structure
The project lives in `~/xeno-bot/` on the server:
*   `~/xeno-bot/config.json`: The bot's private configuration (Manually created).
*   `~/xeno-bot/database/`: Persistent storage for `database.db` and `schema.sql`.
*   `~/xeno-bot/word_chain_data/`: Persistent storage for word lexicons.
*   `~/xeno-bot/docker-compose.yml`: Defines the service and volume mounts.

---

## 🚀 CI/CD Pipeline (GitHub Actions)

The workflow is defined in `.github/workflows/docker-ci.yml`.

### 🔑 Required GitHub Secrets
To allow the pipeline to run, the following secrets were added to the repository:
*   `VM_HOST`: The IP address of the Oracle VM.
*   `VM_USER`: Your SSH username (`ubuntu`).
*   `VM_SSH_KEY`: Your **OpenSSH formatted** private key.

### How it works:
1.  **Push to `main`**: Triggers the `build-and-push` job.
2.  **Build**: Docker image is built using the project's `Dockerfile`.
3.  **Push**: Image is tagged as `latest` and pushed to `ghcr.io`.
4.  **Deploy**: The `deploy` job SSHs into the VM and runs:
    ```bash
    cd ~/xeno-bot
    docker compose pull
    docker compose up -d
    docker system prune -f
    ```

---

## 💾 Data Migration (WinSCP)

Since `database.db` is a binary file, it cannot be edited via terminal.
*   **WinSCP** was used to transfer the local `database.db` and `word_chain_data` files to the VM.
*   **Volume Mounting**: The `docker-compose.yml` ensures that when the container restarts, it doesn't lose data by mapping host folders to `/app/database` and `/app/word_chain_data`.

---

## 🛠️ Useful Commands

| Action | Command |
| :--- | :--- |
| **Check Logs** | `docker logs -f xeno-bot` |
| **Restart Bot** | `docker compose restart bot` |
| **Stop Bot** | `docker compose down` |
| **Start Bot** | `docker compose up -d` |
| **Check Stats** | `docker ps` |

---

## 📝 Maintenance
*   **Database Schema**: If you change the database structure, update `database/schema.sql` on the VM.
*   **Config Changes**: If you change the bot token or prefix, update `config.json` on the VM and restart the container.
