/* ============================================================
   OISignalFlow — dashboard-config.js
   API endpoint configuration for the live dashboard.

   HOW IT WORKS:
   - Running LOCALLY  → fetches config.json from the same folder
   - Hosted on NETLIFY → fetches from the DigitalOcean VM over HTTP

   If you change your VM IP, update VM_IP below and push to GitHub.
   ============================================================ */

(function () {
  // ── Your DigitalOcean VM IP and CORS server port ──
  var VM_IP   = '167.71.224.25';
  var VM_PORT = '8080';

  // Auto-detect: local dev vs any hosted environment (Netlify, etc.)
  var isLocal = (
    location.hostname === 'localhost'     ||
    location.hostname === '127.0.0.1'    ||
    location.hostname === ''             ||  // file:// protocol
    location.protocol === 'file:'
  );

  window.OISF_API = isLocal
    ? 'config.json'
    : 'http://' + VM_IP + ':' + VM_PORT + '/config.json';

  // Log which mode is active (visible in browser devtools console)
  console.log(
    '%c⚡ OISignalFlow Dashboard',
    'color:#00d4ff;font-weight:bold;font-size:14px'
  );
  console.log(
    '%cAPI Mode: ' + (isLocal ? 'LOCAL' : 'REMOTE VM'),
    'color:#94a3b8'
  );
  console.log(
    '%cFetching: ' + window.OISF_API,
    'color:#475569'
  );
})();
