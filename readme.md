# Iden Challenge Automation - Complete Solution

A comprehensive Playwright automation script that extracts all product data from the Iden hiring challenge application.

## 🚀 Features

- **Complete Data Extraction**: Extracts ALL products (not limited to 100)
- **Smart Session Management**: Saves and reuses authentication sessions
- **Robust Wizard Navigation**: Handles all 4 steps of the data selection process
- **Pagination Handling**: Automatically scrolls through all product pages
- **JSON Export**: Saves structured product data with all details
- **Error Resilience**: Comprehensive error handling with automatic screenshots
- **Production Ready**: Optimized for reliability and complete data extraction

## 📁 Project Structure

```
iden-challenge/
├── auth/
│   └── session.json          # Authentication cookies (auto-generated)
├── data/
│   └── products.json         # Complete product data (auto-generated)
├── utils/
│   ├── __init__.py           # Package initialization
│   ├── auth.py               # Smart authentication management
│   ├── navigation.py         # Wizard navigation handler
│   └── data_extraction.py    # Complete product extraction
├── iden_challenge.py         # Main automation script 
└── README.md                 # This documentation
```

## 🛠️ Installation & Setup

1. **Install Python 3.8+** if not already installed

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Playwright**:
   ```bash
   pip install playwright
   ```

4. **Install browsers**:
   ```bash
   playwright install chromium
   ```

## ⚙️ Configuration

### 1. Update Credentials
Edit `iden_challenge.py` and replace with your actual credentials:

```python
self.credentials = {
    "username": "your_actual_email@example.com",  # Replace with your email
    "password": "your_actual_password"            # Replace with your password
}
```

### 2. Optional Settings
Modify these in the respective files if needed:

- **Timeouts**: `utils/auth.py` and `utils/navigation.py`
- **Browser behavior**: `iden_challenge.py` (set `headless=True` for production)
- **Scroll behavior**: `utils/data_extraction.py` (adjust `max_scroll_attempts`)

## 🎯 Usage

### Run Complete Extraction:
```bash
python iden_challenge.py
```

### For Production (Headless):
```bash
# Change headless=False to headless=True in iden_challenge.py
python iden_challenge.py
```

## 🔧 How It Works

### 1. **Session Management**
- Checks for existing valid session in `auth/session.json`
- Performs fresh login if no session exists
- Saves session for future runs to avoid repeated logins

### 2. **Authentication**
- Navigates to login page
- Enters credentials securely
- Waits for successful login confirmation
- Handles login errors gracefully

### 3. **Wizard Navigation**
- Clicks "Launch Challenge" button
- Steps through 4-stage wizard:
  1. **Data Source**: Selects "Local Database"
  2. **Category**: Chooses "All Products" 
  3. **View Type**: Selects "Table View"
  4. **Products**: Clicks "View Products"

### 4. **Complete Data Extraction**
- Extracts ALL products (no 100-item limit)
- Handles pagination automatically
- Scrolls until all products are loaded
- Parses product details comprehensively

### 5. **Data Export**
- Saves to `data/products.json` with structured format
- Includes all product attributes
- Maintains data integrity

## 📊 Output Format

### Session Data (`auth/session.json`)
- Browser cookies and authentication tokens
- Enables session reuse across runs

### Product Data (`data/products.json`)
Complete product information in JSON format:

```json
[
  {
    "id": 0,
    "name": "Budget Office Set",
    "category": "Office",
    "material": "Ceramic",
    "size": "17×19×9 cm",
    "warranty": "5 Years",
    "last_updated": "18 days ago"
  },
  {
    "id": 1,
    "name": "Modern Beauty Max",
    "category": "Beauty",
    "material": "Silicone",
    "size": "21×19×14 cm",
    "warranty": "Lifetime",
    "last_updated": "5 days ago"
  }
  // ... ALL products continue
]
```

## 🐛 Troubleshooting Guide

### Common Issues & Solutions:

1. **Authentication Failed**
   ```bash
   # Delete session and retry
   rm -rf auth/
   mkdir auth
   python iden_challenge.py
   ```

2. **Element Not Found Errors**
   - Run with `headless=False` to see the issue
   - Check if website structure changed
   - Screenshots auto-saved as `error_screenshot.png`

3. **Empty Output File**
   - Check console for extraction errors
   - Verify successful navigation through all wizard steps

4. **Browser Installation Issues**
   ```bash
   # Reinstall browsers
   playwright uninstall
   playwright install
   ```

### Debug Mode:
Run with visible browser to monitor the process:
```bash
# Ensure headless=False in iden_challenge.py
python iden_challenge.py
```

## ⚡ Performance Notes

- **First Run**: ~2-3 minutes (includes login and full extraction)
- **Subsequent Runs**: ~1-2 minutes (uses saved session)
- **Data Completeness**: Extracts ALL products (1400+ items)
- **Memory Efficient**: Handles pagination without loading all data at once

## 🔒 Security & Privacy

- Credentials only stored in source code (not in session)
- Session contains only browser cookies
- No sensitive data in output JSON
- Automatic cleanup of error screenshots recommended

## 📝 Implementation Details

### Key Features:
- **Complete Extraction**: No product limit - gets everything
- **Error Recovery**: Continues after individual product errors
- **Smart Waiting**: Proper async handling for dynamic content
- **Session Persistence**: Avoids repeated logins
- **Production Ready**: Handles edge cases and timeouts

### Technical Stack:
- **Playwright**: Modern browser automation
- **Python 3.8+**: Main programming language
- **JSON**: Data serialization format
- **CSS Selectors**: Element targeting

## 🚀 Production Deployment

For server deployment:

1. Set `headless=True` in `iden_challenge.py`
2. Ensure proper browser installation:
   ```bash
   playwright install --with-deps chromium
   ```
3. Schedule with cron or task scheduler
4. Monitor output files for completion

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run with `headless=False` to see the browser
3. Examine generated screenshots for clues
4. Verify credentials and network connectivity

## 📄 License

This solution is developed for the Iden hiring challenge. Please use responsibly and in accordance with the challenge guidelines.

---

**Note**: Remember to replace the placeholder credentials in `iden_challenge.py` with your actual login information before running the script.
