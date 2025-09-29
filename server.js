const express = require("express");
const crypto = require("crypto");
const fetch = require("node-fetch");

// --- IMPORTANT ---
// Replace with your actual LCSC API credentials
const API_KEY = process.env.LCSC_KEY || "YOUR_LCSC_KEY";
const API_SECRET = process.env.LCSC_SECRET || "YOUR_LCSC_SECRET";
// -----------------

const BASE = "https://ips.lcsc.com/rest/wmsc2agent";

function sign() {
  const ts = Math.floor(Date.now() / 1000).toString();
  const nn = crypto.randomBytes(8).toString("hex");
  const plain = `key=${API_KEY}&nonce=${nn}&secret=${API_SECRET}&timestamp=${ts}`;
  const sig = crypto.createHash("sha1").update(plain).digest("hex");
  return { ts, nn, sig };
}

const app = express();

// Serve the static frontend files
app.use(express.static('.'));

app.get("/api/lcsc/info/:cpn", async (req, res) => {
  try {
    const { ts, nn, sig } = sign();
    const url = new URL(`${BASE}/product/info/${req.params.cpn}`);
    url.searchParams.set("key", API_KEY);
    url.searchParams.set("nonce", nn);
    url.searchParams.set("timestamp", ts);
    url.searchParams.set("signature", sig);

    const apiResponse = await fetch(url);
    const data = await apiResponse.json();
    res.status(apiResponse.status).json(data);
  } catch (e) {
    res.status(500).json({ success: false, message: e.toString() });
  }
});

app.get("/api/lcsc/search", async (req, res) => {
  try {
    const { q } = req.query;
    if (!q) {
        return res.status(400).json({ success: false, message: "Query parameter 'q' is required." });
    }
    const { ts, nn, sig } = sign();
    const url = new URL(`${BASE}/search/product`);
    url.searchParams.set("key", API_KEY);
    url.searchParams.set("nonce", nn);
    url.searchParams.set("timestamp", ts);
    url.searchParams.set("signature", sig);
    url.searchParams.set("keyword", q);
    url.searchParams.set("match_type", "fuzzy");
    url.searchParams.set("is_available", "true");
    url.searchParams.set("page_size", "100");
    url.searchParams.set("current_page", "1");

    const apiResponse = await fetch(url);
    const data = await apiResponse.json();
    res.status(apiResponse.status).json(data);
  } catch (e) {
    res.status(500).json({ success: false, message: e.toString() });
  }
});

const PORT = 8080;
app.listen(PORT, () => console.log(`LCSC proxy server running on http://localhost:${PORT}`));