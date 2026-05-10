/* ============================================================
   OISignalFlow — dashboard-config.js

   LOCAL dev   → fetch config.json directly (same folder)
   PRODUCTION  → fetch /api/config.json  (Netlify proxies
                 this server-side to the VM over HTTP,
                 so no mixed-content error on HTTPS)
   ============================================================ */

(function () {
  var isLocal = (
    location.hostname === 'localhost'  ||
    location.hostname === '127.0.0.1' ||
    location.hostname === ''          ||
    location.protocol === 'file:'
  );

  window.OISF_API = isLocal ? 'config.json' : '/api/config.json';

  console.log(
    '%c⚡ OISignalFlow Dashboard',
    'color:#00d4ff;font-weight:bold;font-size:14px'
  );
  console.log('%cAPI Mode : ' + (isLocal ? 'LOCAL' : 'NETLIFY PROXY'), 'color:#94a3b8');
  console.log('%cEndpoint : ' + window.OISF_API, 'color:#475569');
})();
