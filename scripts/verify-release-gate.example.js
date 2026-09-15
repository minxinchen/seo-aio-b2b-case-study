// Fixture validator only. No network requests; this does not test a live site.
const fs = require('node:fs');
const required = ['multilingual_pages', 'anonymous_public_html', 'structured_data', 'visual_mobile_desktop', 'full_site_regression'];
try {
  if (!process.argv[2]) throw new Error('Provide a release-gate JSON fixture; no live result is implied.');
  const report = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  if (!Array.isArray(report.checks) || !Array.isArray(report.release_blockers)) throw new Error('Missing checks or blockers');
  const failed = required.filter(name => {
    const rows = report.checks.filter(c => c.name === name);
    return rows.length !== 1 || rows[0].result !== 'PASS';
  });
  const pass = failed.length === 0 && report.release_blockers.length === 0 && report.checks.every(c => c.result === 'PASS');
  console.log(JSON.stringify({mode: 'fixture_validation_not_live_verification', pass, failed_checks: failed}, null, 2));
  process.exitCode = pass ? 0 : 1;
} catch (error) { console.error(error.message); process.exitCode = 2; }
