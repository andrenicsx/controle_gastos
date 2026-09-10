# CASHEYE for iPhone

This folder contains the installable web version of CASHEYE. It is a PWA: on an iPhone it can be added to the Home Screen and opened like an app.

## Publish it first

The iPhone needs an HTTPS link. The easiest options are GitHub Pages, Netlify, or Vercel. Upload the contents of this `web` folder to one of those services and obtain its public HTTPS address.

For a quick local preview on the computer, run this command from the project root:

```powershell
python -m http.server 8000 --directory web
```

Then open `http://localhost:8000` on the computer.

## Install on iPhone

1. Open the published HTTPS address in **Safari**.
2. Tap the Share button.
3. Select **Add to Home Screen**.
4. Tap **Add**.

## Bring over existing data

1. Send `lancamentos.json` to the iPhone using AirDrop, iCloud Drive, or Files.
2. Open CASHEYE, tap **Import**, and select that file.
3. Confirm the import.

The data is saved in the browser on that device. It does not automatically sync with the desktop version; automatic sync would require a shared online database.
