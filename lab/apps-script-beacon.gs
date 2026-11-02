// The beacon's other end, as a Google Apps Script web app.
//
// Why this exists: on 2026-11-02 the Formspree endpoint answered {"ok":true} to three submissions and
// no mail arrived at the address it is configured to mail. That is not something the sender can
// diagnose — it can report what the endpoint said, which it now does, and nothing more. Apps Script is
// worth the extra five minutes for one reason: the Sheet is a record and the email is only a
// notification. If mail breaks again, the Sheet still answers "did anyone actually run this", which is
// the question the beacon exists to answer.
//
// Set up, once, about five minutes:
//
//   1. sheets.new — a blank spreadsheet. Name it something you will recognise in a year.
//   2. Extensions -> Apps Script. Delete what is there, paste this file, Save.
//   3. Deploy -> New deployment -> type "Web app".
//        Description:   tribe beacon
//        Execute as:    Me
//        Who has access: Anyone            <-- "Anyone" means anyone, without a Google login.
//      Deploy. It will ask you to authorise; the scopes are "send email as you" and "edit this
//      spreadsheet", which is exactly what the code does and nothing else.
//   4. Copy the Web app URL. It looks like
//        https://script.google.com/macros/s/AKfy.../exec
//   5. Put it in the repository: Settings -> Secrets and variables -> Actions -> Variables ->
//      TRIBE_BEACON_URL = that URL. (A variable, not a secret: forks inherit files, never variables or
//      secrets, so the address a fork must be able to read has to be in the open — and it is written
//      into .github/workflows/wake.yml as the fallback.)
//   6. To prove it end to end, delete .tribe-beacon in the repository and run any wake. The marker
//      names the endpoint as well as the repository, so changing the endpoint is itself a reason to
//      send once more. One row appears in the Sheet and one mail in the inbox.
//
// What arrives, per trial: when, repository, whether it was a fork, which member woke, which model
// answered. No address, no name, no IP kept by this code. One row per repository, ever.
//
// MailApp's free quota is 100 messages a day, which is around a hundred times more than this will ever
// need; a repository that wakes a hundred times in a day has other problems.

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var book = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = book.getSheetByName('beacons') || book.insertSheet('beacons');
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(['first seen', 'repository', 'fork', 'member', 'model', 'claimed when']);
    }

    var d = {};
    try {
      d = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    } catch (err) {
      d = { unparsed: (e && e.postData && e.postData.contents) || '' };
    }

    sheet.appendRow([
      new Date(),
      d.repo || '(no repository named)',
      d.fork === true || d.fork === 'true',
      d.member || '',
      d.model || '',
      d.when || ''
    ]);

    MailApp.sendEmail({
      to: 'ai.tribe.model@gmail.com',
      subject: 'AI tribe beacon: ' + (d.repo || '(no repository named)') + (d.fork ? ' (fork)' : ''),
      body: JSON.stringify(d, null, 2) +
            '\n\nRow ' + sheet.getLastRow() + ' of the sheet. One row per repository; a fork sends once,' +
            ' when its own owner first runs it.'
    });

    return ContentService
      .createTextOutput(JSON.stringify({ ok: true, row: sheet.getLastRow() }))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

// Kept so that opening the URL in a browser answers something instead of an error: if you can read
// this sentence in the browser, the deployment is live and the address is right.
function doGet() {
  return ContentService.createTextOutput('the tribe beacon is deployed; POST JSON here.');
}
