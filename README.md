# EasyEDA API Explorer and LCSC Stock Checker

This project is a web-based tool that serves two main purposes:
1.  An API explorer for the EasyEDA API.
2.  A stock checker for LCSC components, which requires your own API key to function.

The application features a theme switcher with Default, Black, and Sunrise themes, and the ability to export stock check results to a CSV file.

## Features

- **EasyEDA API Explorer**: Browse and search a list of EasyEDA API functions with descriptions, parameters, and examples.
- **LCSC Stock Checker**: Search for LCSC parts by their part number and view stock information. (Requires configuration).
- **JLCPCB Stock Checker**: A UI placeholder for a future JLCPCB integration.
- **Theme Switcher**: Choose between Default, Black, and Sunrise color themes. Your preference is saved locally.
- **CSV Export**: Export the results of a stock check to a CSV file.

## Setup and Configuration

To run this project locally, you will need to have Node.js and npm installed.

### 1. Install Dependencies

Clone or download the project files, navigate to the project directory in your terminal, and run the following command to install the necessary dependencies:

```bash
npm install
```

### 2. Configure LCSC API Credentials

For the LCSC Stock Checker to work, you must have an LCSC OpenAPI key and secret.

**You must configure these credentials in the `server.js` file.**

Open `server.js` and replace the placeholder values with your actual credentials:

```javascript
// --- IMPORTANT ---
// Replace with your actual LCSC API credentials
const API_KEY = process.env.LCSC_KEY || "YOUR_LCSC_KEY";
const API_SECRET = process.env.LCSC_SECRET || "YOUR_LCSC_SECRET";
// -----------------
```

Alternatively, you can set them as environment variables named `LCSC_KEY` and `LCSC_SECRET` before starting the server.

### 3. Start the Server

Once the dependencies are installed and the API keys are configured, you can start the server with the following command:

```bash
node server.js
```

You should see a message in your terminal indicating that the server is running:
`LCSC proxy server running on http://localhost:8080`

### 4. Access the Application

Open your web browser and navigate to the following address:

[http://localhost:8080](http://localhost:8080)

You should now be able to use the EasyEDA API Explorer and the LCSC Stock Checker.