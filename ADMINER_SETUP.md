# 🗄️ Adminer Database Management Setup

This guide explains how to use Adminer for managing your SQLite database, including the solution for SQLite passwordless access.

## 🔍 **The SQLite Password Issue**

According to the [Adminer documentation](https://www.adminer.org/en/password/), Adminer 4.6.3+ doesn't support accessing databases without passwords for security reasons. Since SQLite doesn't support user authentication, we need a workaround.

## ✅ **Our Solution: Custom Plugin**

We've implemented the **login-password-less plugin** recommended by Adminer:
- Uses a dummy password (`admin`) for Adminer's interface
- Automatically connects to SQLite without passing credentials to the database
- Maintains security by requiring authentication at the web interface level

## 🚀 **Quick Start**

### **1. Start Adminer**
```bash
# Build and start Adminer with SQLite plugin
./deploy.sh adminer
```

### **2. Access Adminer**
- **Local**: `http://localhost:8080`
- **Web**: `https://danilbogdan.com/adminer/` (if nginx configured)

### **3. Login**
- **Server**: `sqlite:///data/money_manager.db`
- **Username**: *(leave empty)*
- **Password**: `admin`

### **4. Explore Your Database**
After login, you'll have full access to:
- **customers** - Customer information
- **connections** - Salt Edge bank connections
- **accounts** - Bank accounts data
- **transactions** - Transaction records

## 📋 **Available Operations**

### **Browse Data** ✅
- View all tables and their contents
- Navigate relationships between tables
- Search and filter records

### **Execute Queries** ✅
```sql
-- Example: Get all customers with their connections
SELECT c.name, c.email, co.provider_name, co.status
FROM customers c
LEFT JOIN connections co ON c.id = co.customer_id;

-- Example: Get transaction summary by account
SELECT a.name, COUNT(t.id) as transaction_count, SUM(t.amount) as total_amount
FROM accounts a
LEFT JOIN transactions t ON a.id = t.account_id
GROUP BY a.id, a.name;
```

### **Export Data** ✅
- Export tables as SQL, CSV, or other formats
- Create database backups
- Generate reports

### **Database Structure** ✅
- View table schemas
- Check indexes and constraints
- Analyze relationships

## 🔧 **Technical Details**

### **Custom Docker Image**
```dockerfile
FROM adminer:latest
COPY adminer-config/login-password-less.php /var/www/html/plugins-enabled/
# ... permissions and configuration
```

### **Plugin Configuration**
The `login-password-less.php` plugin:
- Accepts the dummy password "admin"
- Connects directly to SQLite file
- Bypasses Adminer's password requirements

### **Docker Compose Setup**
```yaml
adminer:
  build:
    dockerfile: Dockerfile.adminer
  environment:
    - ADMINER_PLUGINS=login-password-less
    - ADMINER_DEFAULT_SERVER=sqlite:///data/money_manager.db
```

## 🔒 **Security Configuration**

### **Local Access**
- Default: Only accessible from localhost
- Safe for development and debugging

### **Web Access (Optional)**
If you configure nginx with our provided config:
- Requires basic authentication at nginx level
- Additional security layer before reaching Adminer
- HTTPS encryption for all data

### **Database Permissions**
- Read-only access to database files
- Cannot modify database structure
- Safe for production inspection

## 🛠️ **Troubleshooting**

### **Login Issues**
```bash
# Check if Adminer is running
docker compose ps

# Check logs
docker compose logs adminer

# Restart Adminer
./deploy.sh stop-adminer
./deploy.sh adminer
```

### **Database Not Found**
```bash
# Ensure Money Manager is running (creates the database)
./deploy.sh status

# Check if database file exists
ls -la data/money_manager.db

# Start the main application first
./deploy.sh deploy
```

### **Plugin Issues**
```bash
# Rebuild Adminer with plugins
docker compose --profile adminer build adminer --no-cache
docker compose --profile adminer up -d adminer
```

## 📊 **Useful Database Queries**

### **System Overview**
```sql
-- Check database structure
SELECT name FROM sqlite_master WHERE type='table';

-- Get row counts for all tables
SELECT 'customers' as table_name, COUNT(*) as rows FROM customers
UNION ALL
SELECT 'connections', COUNT(*) FROM connections
UNION ALL
SELECT 'accounts', COUNT(*) FROM accounts
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions;
```

### **Data Analysis**
```sql
-- Recent transactions
SELECT t.*, a.name as account_name, c.name as customer_name
FROM transactions t
JOIN accounts a ON t.account_id = a.id
JOIN connections co ON a.connection_id = co.id
JOIN customers c ON co.customer_id = c.id
ORDER BY t.made_on DESC
LIMIT 10;

-- Connection status summary
SELECT status, COUNT(*) as count
FROM connections
GROUP BY status;
```

### **Data Validation**
```sql
-- Check for orphaned records
SELECT 'Accounts without connections' as issue, COUNT(*) as count
FROM accounts a
LEFT JOIN connections c ON a.connection_id = c.id
WHERE c.id IS NULL

UNION ALL

SELECT 'Transactions without accounts', COUNT(*)
FROM transactions t
LEFT JOIN accounts a ON t.account_id = a.id
WHERE a.id IS NULL;
```

## 🎯 **Next Steps**

1. **Explore**: Browse your database tables to understand the data structure
2. **Query**: Use SQL queries to analyze your financial data
3. **Export**: Create reports and backups of your data
4. **Monitor**: Use Adminer to debug issues and verify data integrity

## 📝 **Commands Reference**

```bash
# Start/Stop Adminer
./deploy.sh adminer           # Start Adminer service
./deploy.sh stop-adminer      # Stop Adminer service

# Access URLs
http://localhost:8080         # Direct local access
https://danilbogdan.com/adminer/  # Web access (if configured)

# Login credentials
Username: (empty)
Password: admin
Server: sqlite:///data/money_manager.db
```

Need help with specific queries or database analysis? The Adminer interface provides a user-friendly way to explore your Money Manager data! 🔍
