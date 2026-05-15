# 🏛️ University Management Database System

## 📌 Overview
The University Management Database System is a full-stack database-driven application designed to manage academic operations efficiently. It integrates an Oracle SQL/PLSQL backend with a Flask web interface to support students, faculty, and administrators through secure and automated workflows.

---

## 🚀 Features
- Relational database design covering UG, Masters, and PhD students  
- PL/SQL automation with triggers for data integrity and business rules  
- Stored procedures for administrative operations and updates  
- SQL views for quick reporting and analytics  
- Role-based access control for secure multi-user interaction  

---

## 🛠️ Technologies Used
- Oracle Database (SQL & PL/SQL)  
- Python (Flask Framework)  
- oracledb (Thick Mode Driver)  
- HTML5, CSS3 (Frontend Templates)  

---

## ▶️ How to Run

### 1. Database Setup
Run the provided `.sql` scripts in Oracle SQL Developer or SQL*Plus to create schema, triggers, and procedures.

### 2. Configure Oracle Client
Ensure Oracle Instant Client is installed and properly configured in `app.py`.

### 3. Install Dependencies
```bash
pip install flask oracledb
