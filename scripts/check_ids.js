const fs = require("fs");
const js = fs.readFileSync("D:/openhands/projects/v2/phishing_ai_master/deployment/frontend/script.js", "utf8");
const html = fs.readFileSync("D:/openhands/projects/v2/phishing_ai_master/deployment/frontend/index.html", "utf8");
const ids = new Set((html.match(/id="([^"]+)"/g) || []).map(s => s.match(/id="([^"]+)"/)[1]));
const refs = [...new Set((js.match(/getElementById\("([^"]+)"\)/g) || []).map(s => s.match(/getElementById\("([^"]+)"\)/)[1]))];
console.log("referenced:", refs.length, "defined:", ids.size);
console.log("MISSING:", refs.filter(r => !ids.has(r)));
