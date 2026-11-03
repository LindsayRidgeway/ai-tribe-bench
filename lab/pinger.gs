/**
 * pinger.gs — make the clock fire when GitHub's scheduler does not.
 *
 * WHY THIS EXISTS
 * GitHub's own cron is best-effort and, on the repository this was built on, it is much worse than
 * that. Measured over the night of 2026-11-02/03: the hourly control workflow was due twelve times
 * and arrived twice — ten hours with no beat at all — and the four-hourly clock fired twice in a
 * day. A missed firing is not run later and does not fail, so nothing in the record says it
 * happened. RUN.md §8 tells a tester to rely on Run workflow; this file is for the person who wants
 * the colony to actually wake on its own.
 *
 * WHAT IT IS
 * A Google Apps Script with a time-driven trigger: every hour it asks GitHub, over the API, to run
 * one workflow by name. Free, no server, nothing to keep running. It is the same trick the beacon
 * already uses (lab/apps-script-beacon.gs) — an account you already have, doing one small thing.
 *
 * SETUP, ONCE (about four minutes)
 *   1. Get a token: github.com → Settings → Developer settings → Personal access tokens →
 *      Fine-grained tokens → Generate new token.
 *        Repository access: only the repository your tribe lives in.
 *        Permissions: Actions = Read and write. Nothing else.
 *      Copy the token; GitHub shows it once.
 *   2. Go to script.google.com → New project. Delete what is there, paste this file.
 *   3. Fill in REPO and TOKEN below.
 *   4. Run `ping` once by hand. Authorise it when Google asks (it is asking about *your own*
 *      script calling *your own* GitHub). The log should say `202` or `204` — both mean accepted.
 *   5. Run `installTrigger` once. From then on it pings hourly.
 *
 * WHAT IT DOES NOT DO
 * It does not make GitHub's cron reliable, and it does not run the workflow itself: it presses the
 * same button a human presses. If GitHub is down, or the token expires (fine-grained tokens do),
 * the pings stop silently — so have a way to notice. The record is the test: if no commit names a
 * member for a day, nothing woke, whatever the trigger says.
 *
 * A token in a script is a credential in a script. Keep the script private to your account; if the
 * token leaks, revoke it — that is one click, and it is the reason to use a fine-grained token that
 * can do exactly one thing rather than a classic one that can do everything.
 */

const REPO = 'OWNER/REPOSITORY';          // e.g. 'ada-lovelace/ai_tribe'
const WORKFLOW = 'clock.yml';             // the workflow file to dispatch
const REF = 'main';                       // the branch whose copy runs
const TOKEN = 'PASTE_YOUR_FINE_GRAINED_TOKEN_HERE';

function ping() {
  const url = 'https://api.github.com/repos/' + REPO +
              '/actions/workflows/' + WORKFLOW + '/dispatches';
  const res = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + TOKEN,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28'
    },
    payload: JSON.stringify({ ref: REF }),
    muteHttpExceptions: true           // a failure must be read, not thrown away
  });
  const code = res.getResponseCode();
  // 204 is the documented success; 202 is accepted-and-queued. Anything else is a finding, printed
  // in full, because a 401 here is a token that expired and a 404 is a workflow renamed on disk.
  Logger.log('ping %s -> %s %s', REPO + '/' + WORKFLOW, code,
             code === 204 || code === 202 ? '(accepted)' : res.getContentText().slice(0, 400));
  return code;
}

function installTrigger() {
  // Every hour, a few minutes past the hour. Delete any earlier copy first: two triggers ping twice,
  // and GitHub keeps one run and one pending per concurrency group, so the second is cancelled and
  // the record shows a cancelled run that nobody asked for.
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'ping') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('ping').timeBased().everyHours(1).create();
  Logger.log('trigger installed: ping, hourly. Run ping() by hand once first to authorise it.');
}
