# Deploy NyayaSetu AI Bot to AWS EC2

This guide walks you through deploying the Telegram bot on an Amazon EC2 instance so it runs 24/7.

---

## Prerequisites

- **AWS account** with console access
- **Telegram Bot Token** (from [@BotFather](https://t.me/BotFather))
- **Neo4j** instance (cloud or self-hosted) with URI, username, and password
- **Git** installed on your local machine

---

## Step 1: Create an EC2 Key Pair (if you don’t have one)

1. In AWS Console go to **EC2** → **Key Pairs** (under Network & Security).
2. Click **Create key pair**.
3. Name it (e.g. `nyayasetu-bot`) and choose **.pem** for macOS/Linux or **.ppk** for PuTTY on Windows.
4. Download and store the private key safely.  
   On macOS/Linux set permissions:
   ```bash
   chmod 400 ~/Downloads/nyayasetu-bot.pem
   ```

---

## Step 2: Launch an EC2 Instance

1. In **EC2** → **Instances** → **Launch instance**.
2. Use these settings:
   - **Name:** `nyayasetu-bot` (or any name).
   - **AMI:** **Amazon Linux 2023** or **Ubuntu 22.04 LTS**.
   - **Instance type:** **t2.micro** (free tier) or **t3.micro** for slightly better performance.
   - **Key pair:** Select the key pair you created.
   - **Network settings:** Create security group and allow:
     - **SSH (22)** from your IP (or 0.0.0.0/0 only if you understand the risk).
   - **Storage:** 8 GB default is enough.
3. Click **Launch instance**.

---

## Step 3: Connect to Your Instance

1. In **EC2** → **Instances**, select the instance and copy its **Public IPv4 address**.
2. SSH in (replace with your key path and IP):

   **Amazon Linux 2023:**
   ```bash
   ssh -i /path/to/your-key.pem ec2-user@<PUBLIC_IP>
   ```

   **Ubuntu:**
   ```bash
   ssh -i /path/to/your-key.pem ubuntu@<PUBLIC_IP>
   ```

---

## Step 4: Install Dependencies on the Server

### On Amazon Linux 2023

```bash
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip git
```

### On Ubuntu 22.04

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
```

---

## Step 5: Clone the Repository and Set Up the App

```bash
# Create app directory (use your repo URL)
sudo mkdir -p /opt/nyayasetu-bot
sudo chown $USER:$USER /opt/nyayasetu-bot
cd /opt/nyayasetu-bot

# Clone your repo (replace with your actual repo URL)
git clone https://github.com/YOUR_USERNAME/AI-for-Bharat-NyayaSetu-AI-.git .

# Or upload via SCP from your machine if the repo is private:
# From your local machine: scp -i your-key.pem -r . ec2-user@<PUBLIC_IP>:/opt/nyayasetu-bot
```

---

## Step 6: Create Virtual Environment and Install Python Packages

```bash
cd /opt/nyayasetu-bot

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 7: Configure Environment Variables

Create a `.env` file on the server (do **not** commit real secrets to git):

```bash
nano .env
```

Add (replace with your real values):

```env
BOT_TOKEN=your_telegram_bot_token_from_botfather
NEO4J_URI=neo4j+s://your-neo4j-host.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
SERVER_URL=https://your-domain-or-public-ip
FILES_DIR=user_files
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

---

## Step 8: Run the Bot as a System Service (Recommended)

So the bot restarts on reboot and on crash, use systemd.

1. Copy the service file from the repo (or create it manually):

   ```bash
   sudo cp /opt/nyayasetu-bot/deploy/nyayasetu-bot.service /etc/systemd/system/
   ```

   On **Ubuntu**, set the correct user:
   ```bash
   sudo sed -i 's/User=ec2-user/User=ubuntu/' /etc/systemd/system/nyayasetu-bot.service
   ```

2. The unit file is in `deploy/nyayasetu-bot.service`. It uses `User=ec2-user` for Amazon Linux; change to `User=ubuntu` on Ubuntu.

3. Enable and start the service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable nyayasetu-bot
   sudo systemctl start nyayasetu-bot
   sudo systemctl status nyayasetu-bot
   ```

4. Useful commands:
   - **Logs:** `sudo journalctl -u nyayasetu-bot -f`
   - **Restart:** `sudo systemctl restart nyayasetu-bot`
   - **Stop:** `sudo systemctl stop nyayasetu-bot`

---

## Step 9: (Optional) Create and Mount a Volume for User Files

If the bot stores files in `FILES_DIR` and you want them to persist across instance replacement:

1. In EC2 create an **EBS volume** and attach it to the instance.
2. SSH in, then format and mount (example for Ubuntu/Amazon Linux):

   ```bash
   # Find the device name (e.g. /dev/nvme1n1 for Nitro instances)
   lsblk
   sudo mkfs -t ext4 /dev/nvme1n1
   sudo mkdir -p /opt/nyayasetu-bot/user_files
   sudo mount /dev/nvme1n1 /opt/nyayasetu-bot/user_files
   sudo chown ec2-user:ec2-user /opt/nyayasetu-bot/user_files   # or ubuntu:ubuntu on Ubuntu
   ```

3. To mount automatically on boot, add an entry to `/etc/fstab` (use the volume’s UUID from `sudo blkid`).

---

## Step 10: Updating the Bot

After you push changes to your repo:

```bash
cd /opt/nyayasetu-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart nyayasetu-bot
```

---

## Security Checklist

- [ ] Restrict SSH (22) to your IP in the security group where possible.
- [ ] Keep the OS updated: `sudo dnf update -y` or `sudo apt update && sudo apt upgrade -y`.
- [ ] Never commit `.env` or key pairs to git.
- [ ] Prefer Neo4j over TLS (`neo4j+s://`) and use strong passwords.
- [ ] If you add a webhook or HTTP endpoint later, put a reverse proxy (e.g. nginx) in front and use HTTPS.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| Bot doesn’t respond | `sudo journalctl -u nyayasetu-bot -f` for errors; confirm `BOT_TOKEN` and network. |
| Neo4j connection errors | Security group allows **outbound** traffic; Neo4j cloud allows this server’s IP. |
| Service won’t start | `WorkingDirectory` and `ExecStart` paths correct; `venv` exists; `.env` present. |
| Permission denied | `User=` in the service file matches the owner of `/opt/nyayasetu-bot`. |

---

## Cost Notes

- **t2.micro / t3.micro** can be in the **free tier** for 750 hours/month in the first 12 months.
- You pay for EBS storage (e.g. ~$0.10/GB/month) and data transfer if you exceed free tier.
- Neo4j Aura has its own free tier; check their pricing for larger usage.
