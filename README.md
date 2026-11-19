# Lost dog watcher

Every 10 minutes, checks PetAlert (Vaud), petalert.fr, petalert.ch and chien-perdu.org
for NEW found-dog posts in canton Vaud and rings your iPhone via the ntfy app.
Posts near Lausanne ring at max priority; elsewhere in Vaud at high priority.

## 1. iPhone (3 min)
1. Install **ntfy** from the App Store.
2. Tap **+**, subscribe to a topic with a hard-to-guess name, e.g. `flore-lausanne-7k3q9`.
   (Anyone who knows the name can read/send to it, so make it random.)
3. iPhone Settings > Notifications > ntfy: Allow, Sounds on, **Time Sensitive on**.
4. Settings > Focus > Sleep (and Do Not Disturb) > Apps > add **ntfy**.
5. Keep the ring/silent switch on ring and volume up. iOS cannot override the silent switch.

## 2. GitHub (5 min)
1. github.com > New repository > name `dog-watcher` > **Public** (free unlimited runs;
   a private repo would run out of free minutes). Only `seen.json` (post IDs) is visible.
2. On the repo page: **Add file > Upload files**, drag in everything from this zip,
   including the `.github` folder. Commit.
3. Settings > Secrets and variables > Actions > **New repository secret**:
   name `NTFY_TOPIC`, value = your topic name from step 1.2.
4. Settings > Actions > General > Workflow permissions > **Read and write** > Save.
5. Actions tab > enable workflows if asked > "Lost dog watcher" > **Run workflow**.

Within a minute your phone should get **"Dog watcher is running"**. That first run
records existing posts; after that you only get alerts for new ones.

## Notes
- GitHub can delay scheduled runs by a few minutes at busy times.
- If a run fails, open the Actions tab to see which site errored.
- Not covered: Facebook groups, Telegram, stmz.ch (check those yourself).
- To stop: Actions tab > Lost dog watcher > "..." > Disable workflow.
