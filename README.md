# LinkPulse — URL Shortener & Analytics Platform

**Team Name:** One Piece in Real  
**Project Name:** LinkPulse

**Live Demo:** https://one-piece-in-real-linkpulse.onrender.com  
**GitHub Repository:** https://github.com/bhaweshb88-hub/One-Piece-in-Real-LinkPulse

---

## 1. Problem Statement

Long URLs are difficult to share, manage, and organize. Basic URL shorteners may not provide sufficient tools for tracking clicks, organizing marketing campaigns, or controlling access to links.

Individuals, developers, and marketing teams need a centralized platform to create short links, manage their settings, and monitor link activity.

LinkPulse addresses these challenges by bringing URL shortening, link management, QR code generation, and analytics together in one application.

## 2. Proposed Solution

LinkPulse is a web-based URL shortening and link management platform built with Python and Flask.

Users can create short URLs from long destination links, customize aliases, configure link expiry and click limits, and manage links through a dashboard.

The platform also provides QR code generation, link activity tracking, and administrative controls to help users manage their links efficiently.

**Try the live application:**  
https://one-piece-in-real-linkpulse.onrender.com

## 3. Features

### URL Shortening and Management
- Convert long URLs into short, shareable links.
- Create custom aliases for short links.
- Configure link expiry.
- Set click limits.
- Protect supported links with passwords.
- Enable or disable links.

### Analytics Dashboard
- View link and click statistics.
- Monitor link status.
- Review link activity through the dashboard.
- Organize links using campaigns and tags.

### QR Codes and Bulk Import
- Generate QR codes for short links.
- Import multiple links using CSV files.

### Administrative Controls
- Manage links through administrative features.
- Block destination hostnames.
- Control link availability.

*Feature availability may depend on the application's current configuration.*

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Flask | Backend web framework |
| SQLite | Database |
| HTML | Web page structure |
| CSS | Styling and layout |
| Python QR code libraries | QR code generation |
| Git | Version control |
| GitHub | Source code hosting |
| Render | Application deployment |

## 5. Project Screenshots

The following screenshots demonstrate the LinkPulse interface and its main features.

### Home Page

![LinkPulse Home Page](screenshots/home.png)

### Create Link

![LinkPulse Create Link](screenshots/create-link.png)

### Analytics Dashboard

![LinkPulse Analytics Dashboard](screenshots/dashboard.png)

### Dashboard Details

![LinkPulse Dashboard Details](screenshots/dashboard-details.png)

### Admin Controls

![LinkPulse Admin Controls](screenshots/admin.png)

## 6. Installation and Setup

Follow these instructions to run LinkPulse on your local computer.

### Prerequisites

Install the following:
- Python
- Git
- A terminal such as PowerShell or the VS Code terminal

### Step 1: Clone the Repository

```bash
git clone https://github.com/bhaweshb88-hub/One-Piece-in-Real-LinkPulse.git
```

Navigate into the project directory:

```bash
cd One-Piece-in-Real-LinkPulse
```

### Step 2: Create a Virtual Environment

On Windows, run:

```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment

For Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### Step 4: Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### Step 5: Start the Application

```powershell
python app.py
```

### Step 6: Open the Application

Open your browser and visit:

http://127.0.0.1:5000

The application should now be available locally.

## 7. Live Demo and Deployment

**Deployment Platform:** Render  
**Live Application:** https://one-piece-in-real-linkpulse.onrender.com

The deployed application can be accessed through the live link above.

If the application takes a little time to respond, the hosting service may be waking up after a period of inactivity.

## 8. Repository Structure

```text
One-Piece-in-Real-LinkPulse/
├── app.py
├── requirements.txt
├── Procfile
├── .gitignore
├── README.md
└── screenshots/
    ├── admin.png
    ├── create-link.png
    ├── dashboard-details.png
    ├── dashboard.png
    └── home.png
```

The `.venv/`, `venv/`, `__pycache__/`, local database files, and environment files are excluded using `.gitignore`.

## 9. Security and Repository Hygiene

- Keep passwords, secret keys, API tokens, and other credentials out of the public repository.
- Use `.gitignore` to exclude local environments, databases, and sensitive configuration files.
- Configure appropriate secret keys and administrator credentials for deployment.
- Do not publish private credentials in source code or documentation.
- Review environment variables and deployment settings before making configuration changes.

## 10. Future Improvements

Potential future improvements include:

- Persistent database storage for production deployments.
- User registration and role-based access control.
- More detailed analytics, including referrer, device, and browser information where available.
- Workspaces and folders for link organization.
- Improved campaign reporting and abuse monitoring.
- Link-in-bio pages and device-based redirection.

## 11. Team

**Team Name:** One Piece in Real  
**Project Name:** LinkPulse

---

**Project Status:** Deployed web application with URL shortening, link management, QR code generation, and analytics features.

**Live Demo:** https://one-piece-in-real-linkpulse.onrender.com